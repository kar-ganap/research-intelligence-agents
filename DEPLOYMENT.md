# Deployment Guide - Research Intelligence Platform

Complete guide for deploying to Google Cloud Run for the hackathon submission.

---

## Prerequisites

1. **Google Cloud Project**
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable firestore.googleapis.com
   gcloud services enable pubsub.googleapis.com
   gcloud services enable cloudscheduler.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

3. **Setup Firestore**
   ```bash
   # Go to: https://console.cloud.google.com/firestore
   # Select "Firestore Native mode"
   # Choose region: us-central1
   ```

4. **Environment Variables**
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export REGION=us-central1
   ```

---

## Quick Deployment (All-in-One)

Deploy everything with a single command:

```bash
bash scripts/deploy_all.sh
```

This script will:
1. Setup Pub/Sub topics and subscriptions
2. Deploy all 4 Cloud Run Services
3. Deploy all 3 Cloud Run Jobs
4. Deploy 1 Cloud Run Worker
5. Setup Cloud Scheduler for recurring jobs

---

## Step-by-Step Deployment

If you prefer to deploy components individually:

### Step 1: Setup Pub/Sub

```bash
bash scripts/setup_pubsub.sh
```

Creates:
- `arxiv-candidates` topic + subscription (ArXiv Watcher → Intake Pipeline)
- `arxiv-matches` topic + subscription (Intake Pipeline → Alert Worker)

### Step 2: Deploy Services

```bash
bash scripts/deploy_services.sh
```

Deploys:
1. **API Gateway** (public, port 8080)
   - Entry point for all HTTP requests
   - Routes to Orchestrator and Graph Service

2. **Orchestrator** (internal, port 8081)
   - Multi-agent ADK pipeline coordination
   - AnswerAgent + ConfidenceAgent

3. **Graph Service** (internal, port 8082)
   - Knowledge graph queries
   - Relationship lookups

4. **Frontend** (public, nginx)
   - Web UI for demo
   - vis.js graph visualization

### Step 3: Deploy Jobs and Worker

```bash
bash scripts/deploy_jobs.sh
```

Deploys:
1. **ArXiv Watcher Job**
   - Fetches new papers daily
   - Publishes to Pub/Sub

2. **Intake Pipeline Job**
   - Processes papers (5 parallel tasks)
   - Runs IngestionPipeline with all agents

3. **Graph Updater Job**
   - Detects relationships (3 parallel tasks)
   - Uses RelationshipAgent (ADK)

4. **Alert Worker**
   - Pub/Sub consumer
   - Sends notifications

### Step 4: Setup Cloud Scheduler

```bash
bash scripts/setup_scheduler.sh
```

Schedules:
- ArXiv Watcher: Daily at 6am UTC
- Graph Updater: Daily at 2am UTC

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    CLOUD RUN DEPLOYMENT                  │
└─────────────────────────────────────────────────────────┘

┌──────────────┐
│  Frontend    │ (Service, Public)
│  nginx       │
└──────┬───────┘
       │
       ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ API Gateway  │───────▶│ Orchestrator │        │ Graph Service│
│ (Service)    │        │ (Service)    │        │  (Service)   │
│ Public       │        │ Internal     │        │  Internal    │
└──────────────┘        └──────┬───────┘        └──────┬───────┘
                               │                       │
                               ▼                       ▼
                        ┌─────────────────────────────────┐
                        │         Firestore                │
                        │  - Papers                        │
                        │  - Relationships                 │
                        └─────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                    BACKGROUND PROCESSING                  │
└──────────────────────────────────────────────────────────┘

Cloud Scheduler (6am) ──▶ ArXiv Watcher (Job)
                               │
                               ▼
                          Pub/Sub: arxiv-candidates
                               │
                               ▼
                          Intake Pipeline (Job, 5 tasks)
                               │
                               ▼
                          Firestore + Pub/Sub: arxiv-matches
                               │
                               ▼
                          Alert Worker (Worker)

Cloud Scheduler (2am) ──▶ Graph Updater (Job, 3 tasks)
                               │
                               ▼
                          Firestore (relationships)
```

---

## Resource Types Deployed

### ✅ Services (4)
- `api-gateway` - HTTP request handler
- `orchestrator` - ADK agent coordination
- `graph-service` - Graph queries
- `frontend` - Web UI

### ✅ Jobs (3)
- `arxiv-watcher` - Daily paper fetching
- `intake-pipeline` - Parallel processing (5 tasks)
- `graph-updater` - Batch relationships (3 tasks)

### ✅ Worker (1)
- `alert-worker` - Pub/Sub consumer

**Total: 8 Cloud Run resources**

---

## Verification

### 1. Check Services

```bash
gcloud run services list --platform managed --region us-central1
```

Expected output:
```
SERVICE          REGION       URL
api-gateway      us-central1  https://api-gateway-xxx.run.app
orchestrator     us-central1  https://orchestrator-xxx.run.app
graph-service    us-central1  https://graph-service-xxx.run.app
frontend         us-central1  https://frontend-xxx.run.app
alert-worker     us-central1  https://alert-worker-xxx.run.app
```

### 2. Check Jobs

```bash
gcloud run jobs list --region us-central1
```

Expected output:
```
JOB               REGION       LAST RUN
arxiv-watcher     us-central1  -
intake-pipeline   us-central1  -
graph-updater     us-central1  -
```

### 3. Test API

```bash
API_URL=$(gcloud run services describe api-gateway --region us-central1 --format="value(status.url)")

# Health check
curl $API_URL/health

# Test Q&A
curl -X POST $API_URL/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are the authors of BERT?"}'
```

### 4. Test Frontend

```bash
FRONTEND_URL=$(gcloud run services describe frontend --region us-central1 --format="value(status.url)")
echo "Open in browser: $FRONTEND_URL"
```

### 5. Manually Trigger Job

```bash
# Trigger ArXiv Watcher
gcloud run jobs execute arxiv-watcher --region us-central1

# Check execution
gcloud run jobs executions list --job arxiv-watcher --region us-central1
```

---

## Cost Optimization

All services use Cloud Run's scale-to-zero:
- **Services**: Pay only when processing requests
- **Jobs**: Pay only when running
- **Worker**: Scales to 0 when no messages

Estimated monthly cost (light usage):
- Services: $5-10/month
- Jobs: $2-5/month
- Pub/Sub: $1-2/month
- **Total: ~$10-20/month**

---

## Troubleshooting

### Service won't deploy
```bash
# Check logs
gcloud run services logs read api-gateway --region us-central1

# Check build logs
gcloud builds list --limit 5
```

### Job fails to run
```bash
# View execution logs
gcloud run jobs executions describe EXECUTION_ID --region us-central1

# Check job configuration
gcloud run jobs describe arxiv-watcher --region us-central1
```

### Pub/Sub messages not flowing
```bash
# Check topics
gcloud pubsub topics list

# Check subscriptions
gcloud pubsub subscriptions list

# Manually publish test message
gcloud pubsub topics publish arxiv-candidates \
  --message '{"test": "message"}'
```

---

## Next Steps

After deployment:

1. **Seed Demo Data**
   ```bash
   # Ingest 4 test papers
   python scripts/add_bert_paper.py
   # Add more papers for demo
   ```

2. **Test End-to-End**
   - Open frontend URL
   - Ask questions
   - View knowledge graph

3. **Prepare Demo Video**
   - Record 3-minute walkthrough
   - Show Q&A, graph, Cloud Run dashboard

4. **Submit to Hackathon**
   - Text description (200-500 words)
   - Demo video (YouTube)
   - GitHub repository
   - Architecture diagram
   - Try it out link (frontend URL)

---

## Hackathon Submission Checklist

- [ ] ✅ Multi-agent application (7 ADK agents)
- [ ] ✅ Deployed to Cloud Run (8 resources)
- [ ] ✅ All 3 resource types (Services, Jobs, Worker)
- [ ] ✅ Uses Gemini models
- [ ] ✅ Solves real-world problem
- [ ] Text description written
- [ ] Demo video recorded (<3 min)
- [ ] GitHub repository public
- [ ] Architecture diagram created
- [ ] Frontend URL accessible

---

## Resources

- **Frontend URL**: https://frontend-xxx.run.app
- **API URL**: https://api-gateway-xxx.run.app
- **Project Console**: https://console.cloud.google.com/run?project=your-project-id
- **GitHub**: https://github.com/yourusername/research-intelligence-platform

---

**Built for Google Cloud Run Hackathon - AI Agents Category**
