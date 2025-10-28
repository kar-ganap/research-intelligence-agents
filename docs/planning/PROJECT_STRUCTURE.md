# Research Intelligence Platform - Project Structure

**Last Updated**: 2025-10-27

---

## Directory Structure

```
research-intelligence-agents/
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore patterns
├── README.md                       # Project overview
├── ARCHITECTURE.md                 # System architecture document
├── PROJECT_STRUCTURE.md            # This file
├── IMPLEMENTATION_PLAN.md          # Phased implementation plan (Crawl/Walk/Run)
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Poetry/pip configuration
│
├── docs/                           # Documentation
│   ├── api/                        # API documentation
│   │   ├── openapi.yaml           # OpenAPI spec
│   │   └── endpoints.md           # Endpoint details
│   ├── adk/                       # ADK agent documentation
│   │   ├── agent_specs.md         # Agent specifications
│   │   └── tool_functions.md     # Tool function reference
│   ├── deployment/                # Deployment guides
│   │   ├── cloud_run.md          # Cloud Run setup
│   │   └── local_dev.md          # Local development
│   └── diagrams/                  # Architecture diagrams
│       └── exported/              # Exported images
│
├── src/                           # Source code
│   ├── __init__.py
│   │
│   ├── agents/                    # ADK Agent definitions
│   │   ├── __init__.py
│   │   ├── base.py               # Base agent utilities
│   │   ├── router_agent.py       # RouterAgent
│   │   ├── retriever_agent.py    # RetrieverAgent
│   │   ├── graph_agent.py        # GraphQueryAgent
│   │   ├── contradiction_agent.py # ContradictionAgent
│   │   ├── confidence_agent.py   # ConfidenceAgent
│   │   ├── synthesis_agent.py    # SynthesisAgent
│   │   └── ingestion/            # Ingestion pipeline agents
│   │       ├── __init__.py
│   │       ├── ingestor_agent.py
│   │       ├── table_extractor_agent.py
│   │       ├── entity_agent.py
│   │       ├── relationship_agent.py
│   │       └── indexer_agent.py
│   │
│   ├── pipelines/                # ADK Pipeline orchestration
│   │   ├── __init__.py
│   │   ├── qa_pipeline.py        # Q&A pipeline
│   │   ├── ingestion_pipeline.py # Paper ingestion pipeline
│   │   └── graph_update_pipeline.py # Graph update pipeline
│   │
│   ├── tools/                    # Agent tool functions
│   │   ├── __init__.py
│   │   ├── pdf_reader.py         # PDF extraction
│   │   ├── retrieval.py          # Search functions
│   │   ├── graph_operations.py   # Graph queries
│   │   ├── embeddings.py         # Vector operations
│   │   ├── entity_extraction.py  # NLP utilities
│   │   └── confidence.py         # Confidence scoring
│   │
│   ├── services/                 # Cloud Run Services
│   │   ├── __init__.py
│   │   ├── api_gateway/          # API Gateway service
│   │   │   ├── __init__.py
│   │   │   ├── main.py           # Flask/FastAPI app
│   │   │   ├── routes/           # API routes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ask.py        # /ask endpoint
│   │   │   │   ├── upload.py     # /upload endpoint
│   │   │   │   ├── graph.py      # /graph endpoint
│   │   │   │   └── watch_rules.py # /watch-rules endpoint
│   │   │   ├── middleware/       # Auth, rate limiting
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   └── rate_limiter.py
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── orchestrator/         # Multi-agent orchestrator
│   │   │   ├── __init__.py
│   │   │   ├── main.py           # Service entry point
│   │   │   ├── agent_runner.py   # ADK pipeline runner
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── graph_service/        # Graph query service
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── graph_queries.py  # Specialized graph ops
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   └── frontend/             # React dashboard
│   │       ├── public/
│   │       ├── src/
│   │       │   ├── components/
│   │       │   │   ├── Dashboard.jsx
│   │       │   │   ├── KnowledgeGraph.jsx
│   │       │   │   ├── QuestionInput.jsx
│   │       │   │   └── WatchRules.jsx
│   │       │   ├── services/
│   │       │   │   └── api.js
│   │       │   ├── App.jsx
│   │       │   └── index.js
│   │       ├── Dockerfile
│   │       ├── package.json
│   │       └── nginx.conf
│   │
│   ├── jobs/                     # Cloud Run Jobs
│   │   ├── __init__.py
│   │   ├── arxiv_watcher/        # Daily arXiv monitoring
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── arxiv_client.py   # arXiv API wrapper
│   │   │   ├── matcher.py        # Match papers to rules
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── intake_pipeline/      # Paper processing
│   │   │   ├── __init__.py
│   │   │   ├── main.py           # Job entry point
│   │   │   ├── processor.py      # Uses ingestion agents
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── graph_updater/        # MapReduce relationship detection
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── map_phase.py      # Parallel comparison
│   │   │   ├── reduce_phase.py   # Aggregation
│   │   │   ├── paradigm_shift.py # Trend detection
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── weekly_digest/        # Email digest generation
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── digest_generator.py
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   └── nightly_eval/         # Quality metrics
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── evaluator.py
│   │       ├── metrics.py
│   │       ├── Dockerfile
│   │       └── requirements.txt
│   │
│   ├── workers/                  # Cloud Run Workers
│   │   ├── __init__.py
│   │   └── alert_worker/         # Pub/Sub alert processor
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── notification_sender.py
│   │       ├── Dockerfile
│   │       └── requirements.txt
│   │
│   ├── storage/                  # Storage layer abstractions
│   │   ├── __init__.py
│   │   ├── firestore_client.py   # Firestore operations
│   │   ├── vector_store.py       # Vertex AI Vector Search
│   │   ├── cloud_storage.py      # GCS operations
│   │   └── bigquery_client.py    # BigQuery operations
│   │
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   ├── paper.py              # Paper model
│   │   ├── relationship.py       # Relationship model
│   │   ├── watch_rule.py         # Watch rule model
│   │   ├── alert.py              # Alert model
│   │   └── schemas.py            # Pydantic schemas
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   ├── logging.py            # Structured logging
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── helpers.py            # Common utilities
│   │
│   └── config/                   # Configuration files
│       ├── __init__.py
│       ├── agents.yaml           # Agent configurations
│       ├── models.yaml           # Model configurations
│       └── features.yaml         # Feature flags
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/                    # Unit tests
│   │   ├── agents/
│   │   ├── tools/
│   │   └── storage/
│   ├── integration/             # Integration tests
│   │   ├── test_qa_pipeline.py
│   │   └── test_ingestion.py
│   ├── e2e/                     # End-to-end tests
│   │   └── test_full_flow.py
│   └── fixtures/                # Test fixtures
│       ├── sample_papers/       # Sample PDFs
│       ├── expected_outputs/    # Expected results
│       └── mock_data.json       # Mock data
│
├── scripts/                     # Utility scripts
│   ├── setup_gcp.sh            # GCP initial setup
│   ├── deploy_all.sh           # Deploy all services
│   ├── seed_demo_data.py       # Load demo data
│   ├── test_agents.py          # Test individual agents
│   ├── generate_diagram.py     # Generate architecture diagrams
│   └── cleanup.sh              # Cleanup resources
│
├── infra/                       # Infrastructure as Code
│   ├── terraform/              # Terraform configs
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── modules/
│   │       ├── firestore/
│   │       ├── pubsub/
│   │       └── cloud_run/
│   └── cloudbuild/             # Cloud Build configs
│       ├── api-gateway.yaml
│       ├── orchestrator.yaml
│       └── jobs.yaml
│
├── data/                        # Data directory (gitignored)
│   ├── papers/                  # Downloaded PDFs
│   ├── cache/                   # Cached embeddings
│   └── eval/                    # Evaluation datasets
│
└── monitoring/                  # Monitoring configs
    ├── dashboards/             # Cloud Monitoring dashboards
    │   └── main_dashboard.json
    └── alerts/                 # Alert policies
        └── alert_config.yaml
```

---

## Key Design Principles

### 1. **Modularity**
- Each agent is a separate module with clear interfaces
- Tools are reusable across agents
- Storage layer is abstracted (easy to swap implementations)

### 2. **Deployment Independence**
- Each service/job/worker has its own `Dockerfile` and `requirements.txt`
- Services can be deployed independently
- Shared code is imported from `src/`

### 3. **Configuration Management**
```python
# src/utils/config.py
from dataclasses import dataclass
import yaml
import os

@dataclass
class AgentConfig:
    name: str
    model: str
    temperature: float
    max_tokens: int

@dataclass
class Config:
    agents: dict[str, AgentConfig]
    features: dict[str, bool]
    storage: dict

def load_config() -> Config:
    """Load configuration from YAML files and environment variables"""
    env = os.getenv('ENV', 'development')

    with open(f'src/config/agents.yaml') as f:
        agents = yaml.safe_load(f)

    with open(f'src/config/features.yaml') as f:
        features = yaml.safe_load(f)

    return Config(agents=agents, features=features, ...)
```

### 4. **Feature Flags**
```yaml
# src/config/features.yaml
features:
  graph_visualization: true
  proactive_alerts: true
  contradiction_detection: true
  confidence_scoring: true
  weekly_digest: true

  # Phase 3 features (initially disabled)
  gpu_mode: false
  debate_system: false
  mcp_server: false

phases:
  crawl:
    - basic_ingestion
    - simple_qa
    - citation_support

  walk:
    - graph_visualization
    - proactive_alerts
    - confidence_scoring

  run:
    - gpu_mode
    - mcp_server
    - debate_system
```

### 5. **ADK Agent Organization**

```python
# src/agents/base.py
from google.adk.agents import LlmAgent
from typing import List, Callable
from src.utils.config import load_config

class BaseResearchAgent:
    """Base class for all research intelligence agents"""

    def __init__(self, name: str, config_key: str):
        self.config = load_config().agents[config_key]
        self.name = name
        self._agent = None

    def create_agent(
        self,
        description: str,
        instruction: str,
        tools: List[Callable],
        output_key: str
    ) -> LlmAgent:
        """Factory method to create ADK agent"""
        return LlmAgent(
            name=self.name,
            model=self.config.model,
            description=description,
            instruction=instruction,
            tools=tools,
            output_key=output_key
        )

    @property
    def agent(self) -> LlmAgent:
        """Lazy load agent"""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    def _create_agent(self) -> LlmAgent:
        """Override in subclass"""
        raise NotImplementedError
```

### 6. **Storage Abstraction**

```python
# src/storage/firestore_client.py
from google.cloud import firestore
from typing import Dict, List, Optional
from src.models.paper import Paper

class FirestoreClient:
    """Abstraction over Firestore operations"""

    def __init__(self):
        self.db = firestore.Client()

    def create_paper(self, paper: Paper) -> str:
        """Create paper document"""
        doc_ref = self.db.collection('papers').document(paper.paper_id)
        doc_ref.set(paper.to_dict())
        return paper.paper_id

    def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get paper by ID"""
        doc = self.db.collection('papers').document(paper_id).get()
        if doc.exists:
            return Paper.from_dict(doc.to_dict())
        return None

    def query_papers(
        self,
        field: str,
        operator: str,
        value: any,
        limit: int = 10
    ) -> List[Paper]:
        """Query papers collection"""
        docs = self.db.collection('papers') \
            .where(field, operator, value) \
            .limit(limit) \
            .stream()
        return [Paper.from_dict(doc.to_dict()) for doc in docs]
```

### 7. **Testing Structure**

```python
# tests/conftest.py
import pytest
from src.storage.firestore_client import FirestoreClient
from google.cloud import firestore
from unittest.mock import Mock

@pytest.fixture
def mock_firestore():
    """Mock Firestore client for testing"""
    return Mock(spec=firestore.Client)

@pytest.fixture
def sample_paper():
    """Sample paper for testing"""
    from src.models.paper import Paper
    return Paper(
        paper_id="test:001",
        title="Test Paper",
        authors=["Test Author"],
        year=2023,
        abstract="Test abstract",
        entities={
            "methods": ["test_method"],
            "findings": ["test_finding"]
        }
    )

@pytest.fixture
def sample_papers_list():
    """List of sample papers"""
    # Load from tests/fixtures/mock_data.json
    import json
    with open('tests/fixtures/mock_data.json') as f:
        data = json.load(f)
    return data['papers']
```

---

## Development Workflow

### Phase Structure
```
Phase X (Crawl/Walk/Run)
├── Sub-phase X.1 (Goal 1)
│   ├── Tasks
│   ├── Done-When Criteria
│   └── Go/No-Go Decision
├── Sub-phase X.2 (Goal 2)
│   └── ...
└── Phase Completion Checklist
```

### Git Workflow
```bash
# Feature branches
git checkout -b phase-1/crawl/basic-ingestion
git checkout -b phase-1/crawl/simple-qa

# Commit conventions
git commit -m "feat(agents): add RetrieverAgent with hybrid search"
git commit -m "fix(storage): handle missing paper_id in Firestore"
git commit -m "test(agents): add unit tests for ConfidenceAgent"

# Phase milestones
git tag -a v0.1.0-crawl -m "Phase 1 Crawl Complete"
git tag -a v0.2.0-walk -m "Phase 2 Walk Complete"
git tag -a v1.0.0-run -m "Phase 3 Run Complete"
```

### Local Development
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Test dependencies

# Setup environment
cp .env.example .env
# Edit .env with your credentials

# Run tests
pytest tests/unit/           # Fast unit tests
pytest tests/integration/    # Integration tests
pytest tests/e2e/           # Full end-to-end tests

# Test individual agents
python scripts/test_agents.py --agent retriever

# Run services locally
# Terminal 1: API Gateway
cd src/services/api_gateway && python main.py

# Terminal 2: Orchestrator
cd src/services/orchestrator && python main.py

# Terminal 3: Frontend
cd src/services/frontend && npm start
```

### Docker Development
```bash
# Build all images
docker-compose build

# Run locally
docker-compose up

# Test specific service
docker-compose up api-gateway orchestrator

# Run with fixtures
docker-compose -f docker-compose.yml -f docker-compose.fixtures.yml up
```

---

## Data Flow Through Structure

### Example: Q&A Request

```
1. User sends POST /ask to Frontend
   └── src/services/frontend/src/services/api.js

2. Frontend calls API Gateway
   └── src/services/api_gateway/routes/ask.py

3. API Gateway authenticates and forwards to Orchestrator
   └── src/services/api_gateway/middleware/auth.py
   └── src/services/orchestrator/main.py

4. Orchestrator loads QA Pipeline
   └── src/pipelines/qa_pipeline.py

5. Pipeline executes agents sequentially/parallel
   └── src/agents/retriever_agent.py (uses src/tools/retrieval.py)
   └── src/agents/graph_agent.py (uses src/tools/graph_operations.py)
   └── src/agents/contradiction_agent.py
   └── src/agents/confidence_agent.py (uses src/tools/confidence.py)
   └── src/agents/synthesis_agent.py

6. Agents access storage
   └── src/storage/firestore_client.py
   └── src/storage/vector_store.py

7. Result returned through stack
   └── Orchestrator → API Gateway → Frontend → User
```

### Example: Paper Ingestion

```
1. arXiv Watcher Job runs (scheduled)
   └── src/jobs/arxiv_watcher/main.py

2. Matches papers to watch rules
   └── src/jobs/arxiv_watcher/matcher.py
   └── src/storage/firestore_client.py (get watch rules)

3. Publishes to Pub/Sub
   └── Cloud Pub/Sub (arxiv.candidates)

4. Intake Pipeline Job triggered
   └── src/jobs/intake_pipeline/main.py

5. Pipeline loads ingestion agents
   └── src/pipelines/ingestion_pipeline.py
   └── src/agents/ingestion/ingestor_agent.py (uses src/tools/pdf_reader.py)
   └── src/agents/ingestion/entity_agent.py (uses src/tools/entity_extraction.py)
   └── src/agents/ingestion/indexer_agent.py

6. Data stored
   └── src/storage/firestore_client.py (paper metadata)
   └── src/storage/cloud_storage.py (PDF)
   └── src/storage/vector_store.py (embeddings)

7. Publishes completion event
   └── Cloud Pub/Sub (docs.ready)
```

---

## File Templates

### Agent Template
```python
# src/agents/example_agent.py
from src.agents.base import BaseResearchAgent
from src.tools.example import example_tool
from google.adk.agents import LlmAgent

class ExampleAgent(BaseResearchAgent):
    """
    ExampleAgent description.

    Purpose: What this agent does
    Input: What it expects in state
    Output: What it produces (output_key)
    """

    def __init__(self):
        super().__init__(name="ExampleAgent", config_key="example_agent")

    def _create_agent(self) -> LlmAgent:
        return self.create_agent(
            description="Brief description for routing",
            instruction="""
            Detailed instruction for the agent.

            Your role: ...
            Use these tools: ...
            Output format: ...
            """,
            tools=[example_tool],
            output_key="example_result"
        )

# Usage
if __name__ == "__main__":
    agent = ExampleAgent()
    result = agent.agent.run({"input": "test"})
    print(result)
```

### Tool Template
```python
# src/tools/example.py
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def example_tool(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of what the tool does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        dict: Result dictionary with keys:
            - status: 'success' or 'error'
            - data: The actual result
            - message: Optional message

    Example:
        >>> example_tool("test", 42)
        {'status': 'success', 'data': {...}}
    """
    try:
        # Tool logic here
        result = process(param1, param2)

        logger.info(f"example_tool executed successfully: {param1}")

        return {
            'status': 'success',
            'data': result
        }

    except Exception as e:
        logger.error(f"example_tool failed: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
```

### Service Template
```python
# src/services/example_service/main.py
from flask import Flask, request, jsonify
from src.utils.config import load_config
from src.utils.logging import setup_logging
import logging

app = Flask(__name__)
config = load_config()
setup_logging()
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/example', methods=['POST'])
def example_endpoint():
    """Example endpoint"""
    try:
        data = request.json

        # Process request
        result = process_request(data)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in /example: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

### Dockerfile Template
```dockerfile
# src/services/example_service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy shared source code
COPY src/ /app/src/

# Copy service-specific code
COPY src/services/example_service/ /app/

# Install dependencies
COPY src/services/example_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8080

# Run service
CMD ["python", "main.py"]
```

---

## Environment Variables

### `.env.example`
```bash
# GCP Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCP_REGION=us-central1

# API Keys
GOOGLE_API_KEY=your-gemini-api-key
SENDGRID_API_KEY=your-sendgrid-key

# Firestore
FIRESTORE_DATABASE=(default)

# Vertex AI
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_INDEX_ENDPOINT=your-endpoint-id

# Cloud Storage
GCS_BUCKET_PDFS=your-bucket-pdfs
GCS_BUCKET_CACHE=your-bucket-cache

# Pub/Sub
PUBSUB_TOPIC_CANDIDATES=arxiv.candidates
PUBSUB_TOPIC_READY=docs.ready
PUBSUB_TOPIC_MATCHES=arxiv.matches

# Feature Flags
ENABLE_GRAPH_VISUALIZATION=true
ENABLE_PROACTIVE_ALERTS=true
ENABLE_CONTRADICTION_DETECTION=true
ENABLE_GPU_MODE=false

# Environment
ENV=development  # development, staging, production
LOG_LEVEL=INFO

# Service URLs (for local dev)
API_GATEWAY_URL=http://localhost:8080
ORCHESTRATOR_URL=http://localhost:8081
GRAPH_SERVICE_URL=http://localhost:8082

# Frontend
REACT_APP_API_URL=http://localhost:8080

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Agent Configuration
DEFAULT_MODEL=gemini-2.0-flash-exp
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=2048
```

---

## Next Steps

1. **Create directory structure**: Run setup script to create all directories
2. **Initialize Git**: Set up version control and initial commit
3. **Setup GCP**: Configure Firestore, Pub/Sub, Cloud Storage
4. **Implement Phase 1 (Crawl)**: See IMPLEMENTATION_PLAN.md for detailed phases

**Ready to generate**:
- [ ] Setup script (`scripts/setup_project.sh`)
- [ ] IMPLEMENTATION_PLAN.md (detailed Crawl/Walk/Run phases)
- [ ] Initial requirements.txt
- [ ] Docker compose for local development
- [ ] Sample agent implementations

Let me know which you'd like next!
