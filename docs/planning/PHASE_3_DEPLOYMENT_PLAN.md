# Phase 3: Deployment Plan (Simplified MVP)

**Created**: 2025-10-28
**Status**: In Progress

---

## Context

We have working Phase 1-2 functionality (ingestion, Q&A, relationships, confidence scoring) but it's all script-based. The original architecture plan called for 4 services + 5 jobs, but that would require significant refactoring.

**Decision**: Deploy pragmatic MVP that demonstrates all features end-to-end on Cloud Run.

---

## Simplified Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLOUD RUN DEPLOYMENT                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐        ┌──────────────────────┐
│  Frontend Service    │◀──────▶│   API Service        │
│  (Cloud Run)         │        │   (Cloud Run)        │
│                      │        │                      │
│  - Simple HTML/JS UI │        │  - Flask/FastAPI     │
│  - Q&A interface     │        │  - QAPipeline        │
│  - Graph viz         │        │  - IngestionPipeline │
└──────────────────────┘        └──────────────────────┘
                                          │
                                          ▼
                                ┌──────────────────────┐
                                │   Firestore          │
                                │   - Papers           │
                                │   - Relationships    │
                                └──────────────────────┘
```

**Resource Count**: 2 Cloud Run Services (meets hackathon minimum)

---

## Implementation Tasks

### Task 1: Create API Service

**File**: `src/services/api/main.py`

```python
"""
Research Intelligence Platform - API Service
Wraps existing pipelines with HTTP endpoints
"""
from flask import Flask, request, jsonify
from src.pipelines.qa_pipeline import QAPipeline
from src.pipelines.ingestion_pipeline import IngestionPipeline
from src.storage.firestore_client import FirestoreClient

app = Flask(__name__)

# Initialize pipelines
qa_pipeline = QAPipeline(enable_confidence=True)
ingestion_pipeline = IngestionPipeline(
    enable_relationships=True,
    enable_alerting=True
)
firestore_client = FirestoreClient()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/ask', methods=['POST'])
def ask():
    """Q&A endpoint with confidence scoring"""
    data = request.json
    question = data.get('question')
    result = qa_pipeline.ask(question)
    return jsonify(result), 200

@app.route('/api/papers', methods=['GET'])
def list_papers():
    """List all papers"""
    papers = firestore_client.get_all_papers()
    return jsonify({'papers': papers}), 200

@app.route('/api/graph', methods=['GET'])
def graph():
    """Get knowledge graph data"""
    papers = firestore_client.get_all_papers()
    relationships = firestore_client.get_all_relationships()

    # Transform to vis.js format
    nodes = [{'id': p['paper_id'], 'label': p['title'][:50]}
             for p in papers]
    edges = [{'from': r['source_id'], 'to': r['target_id'],
              'label': r['relationship_type']}
             for r in relationships]

    return jsonify({'nodes': nodes, 'edges': edges}), 200

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

**Endpoints**:
- `GET /health` - Health check
- `POST /api/ask` - Q&A with confidence
- `GET /api/papers` - List papers
- `GET /api/graph` - Knowledge graph data

---

### Task 2: Create Dockerfile for API Service

**File**: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY .env.example .env

# Expose port
EXPOSE 8080

# Run API service
CMD ["python", "-m", "src.services.api.main"]
```

---

### Task 3: Create Simple Frontend

**File**: `src/services/frontend/index.html`

Simple HTML page with:
- Text input for questions
- Display area for answers with citations
- Basic graph visualization using vis.js CDN

**File**: `src/services/frontend/Dockerfile`

```dockerfile
FROM nginx:alpine
COPY src/services/frontend/*.html /usr/share/nginx/html/
COPY src/services/frontend/*.js /usr/share/nginx/html/
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
```

---

### Task 4: Deployment Scripts

**File**: `scripts/deploy_api.sh`

```bash
#!/bin/bash
set -e

PROJECT_ID="your-gcp-project"
REGION="us-central1"
SERVICE_NAME="research-intelligence-api"

echo "Building and deploying API service..."

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

echo "✅ API deployed"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
```

**File**: `scripts/deploy_frontend.sh`

```bash
#!/bin/bash
set -e

PROJECT_ID="your-gcp-project"
REGION="us-central1"
SERVICE_NAME="research-intelligence-frontend"

cd src/services/frontend

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

echo "✅ Frontend deployed"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
```

---

## Testing Plan

### Local Testing

```bash
# 1. Test API locally
cd /path/to/project
python src/services/api/main.py

# In another terminal:
curl http://localhost:8080/health
curl -X POST http://localhost:8080/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are the authors of the Transformer paper?"}'

# 2. Test frontend locally
cd src/services/frontend
python -m http.server 8000
# Open http://localhost:8000 in browser
```

### Cloud Testing

```bash
# 1. Deploy API
bash scripts/deploy_api.sh

# 2. Deploy frontend
bash scripts/deploy_frontend.sh

# 3. Test API endpoint
API_URL=$(gcloud run services describe research-intelligence-api \
  --region us-central1 --format="value(status.url)")

curl $API_URL/health
curl -X POST $API_URL/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What BLEU score did the Transformer achieve?"}'

# 4. Open frontend in browser
FRONTEND_URL=$(gcloud run services describe research-intelligence-frontend \
  --region us-central1 --format="value(status.url)")

open $FRONTEND_URL
```

---

## Success Criteria

- [ ] API service deploys to Cloud Run without errors
- [ ] Frontend service deploys to Cloud Run without errors
- [ ] `/api/ask` returns answers with citations and confidence scores
- [ ] `/api/graph` returns knowledge graph data
- [ ] Frontend loads and can query API
- [ ] End-to-end demo works (ask question → get answer)
- [ ] All environment variables configured correctly
- [ ] Services are publicly accessible

---

## Timeline

- **Task 1-2** (API + Dockerfile): 1 hour
- **Task 3** (Frontend): 1 hour
- **Task 4** (Deploy scripts): 30 minutes
- **Testing**: 1 hour
- **Buffer**: 30 minutes

**Total**: ~4 hours

---

## Phase 3.2 & 3.3 (After Deployment)

Once services are deployed:

1. **Demo Preparation**:
   - Seed 10 papers (use existing 4 + download 6 more)
   - Create demo script
   - Record 3-minute video

2. **Documentation**:
   - Update README with deployment URLs
   - Create architecture diagram
   - Write hackathon submission description

---

## Deferred for Future Work

These were in the original plan but aren't critical for MVP:

- Separate Orchestrator service (currently: pipelines run in API process)
- Graph Service (currently: graph endpoint in main API)
- Cloud Run Jobs (ArXiv watcher, intake pipeline, etc.)
- Pub/Sub alerting worker
- Cloud Scheduler cron jobs
- React frontend (using simple HTML instead)

All of these can be added later as enhancements (see FUTURE_WORK.md).

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Cloud Run build fails | Test Docker build locally first |
| API timeout on cold start | Add warmup endpoint, increase timeout to 300s |
| Firestore connection fails | Use Application Default Credentials, set GOOGLE_CLOUD_PROJECT env var |
| PDF ingestion too slow for API | Make `/api/ingest` async or skip in MVP (pre-seed data) |
| Frontend can't reach API | Enable CORS in Flask, use environment variable for API URL |

---

## Next Steps

1. Create `src/services/api/main.py` (Flask API wrapper)
2. Create root `Dockerfile` for API service
3. Create simple frontend HTML + Dockerfile
4. Write deployment scripts
5. Test locally
6. Deploy to Cloud Run
7. Verify end-to-end functionality
