#!/bin/bash

# Research Intelligence Platform - Project Setup Script
# Creates all directories and initial files

set -e  # Exit on error

echo "=================================================="
echo "Research Intelligence Platform - Project Setup"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [[ ! -f "ARCHITECTURE.md" ]]; then
    echo -e "${YELLOW}⚠️  Warning: ARCHITECTURE.md not found${NC}"
    echo "Make sure you're in the project root directory"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${BLUE}Creating directory structure...${NC}"
echo ""

# Main source directories
echo "Creating src/ structure..."
mkdir -p src/{agents,tools,pipelines,services,jobs,workers,storage,models,utils,config}

# Agents subdirectories
echo "Creating agents/ subdirectories..."
mkdir -p src/agents/ingestion

# Services subdirectories
echo "Creating services/ subdirectories..."
mkdir -p src/services/api_gateway/{routes,middleware}
mkdir -p src/services/orchestrator
mkdir -p src/services/graph_service
mkdir -p src/services/frontend/{public,src/{components,services}}

# Jobs subdirectories
echo "Creating jobs/ subdirectories..."
mkdir -p src/jobs/arxiv_watcher
mkdir -p src/jobs/intake_pipeline
mkdir -p src/jobs/graph_updater
mkdir -p src/jobs/weekly_digest
mkdir -p src/jobs/nightly_eval

# Workers subdirectories
echo "Creating workers/ subdirectories..."
mkdir -p src/workers/alert_worker

# Test directories
echo "Creating tests/ structure..."
mkdir -p tests/{unit,integration,e2e,fixtures}
mkdir -p tests/unit/{agents,tools,storage}
mkdir -p tests/fixtures/{sample_papers,expected_outputs}

# Documentation directories
echo "Creating docs/ structure..."
mkdir -p docs/{api,adk,deployment,diagrams/exported}

# Scripts directory (already exists but ensure)
mkdir -p scripts

# Infrastructure directories
echo "Creating infra/ structure..."
mkdir -p infra/terraform/modules/{firestore,pubsub,cloud_run}
mkdir -p infra/cloudbuild

# Data directories (will be gitignored)
echo "Creating data/ structure..."
mkdir -p data/{papers,cache,eval}

# Monitoring directories
echo "Creating monitoring/ structure..."
mkdir -p monitoring/{dashboards,alerts}

echo ""
echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

# Create __init__.py files
echo -e "${BLUE}Creating Python package files (__init__.py)...${NC}"

# Find all directories under src/ and tests/ and create __init__.py
find src -type d -exec touch {}/__init__.py \; 2>/dev/null || true
find tests -type d -exec touch {}/__init__.py \; 2>/dev/null || true

echo -e "${GREEN}✅ Python package files created${NC}"
echo ""

# Create essential configuration files
echo -e "${BLUE}Creating essential configuration files...${NC}"
echo ""

# .gitignore
if [[ ! -f ".gitignore" ]]; then
    echo "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv
ENV/

# Environment
.env
.env.local
.env.*.local

# Credentials
*.json
!package.json
!package-lock.json
!tsconfig.json
*-key.json
credentials/
service-account*.json

# IDEs
.vscode/
.idea/
*.swp
*.swo
*.sublime-project
*.sublime-workspace

# Data
data/
*.pdf
cache/
*.pkl
*.pickle

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build
dist/
build/
*.egg-info/
.eggs/
node_modules/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Temporary files
*.tmp
*.temp
tmp/
temp/

# Phase reports
phase_*_report.txt

# Cloud Run
.dockerignore
EOF
    echo -e "${GREEN}✅ .gitignore created${NC}"
else
    echo -e "${YELLOW}⚠️  .gitignore already exists, skipping${NC}"
fi

# .env.example
if [[ ! -f ".env.example" ]]; then
    echo "Creating .env.example..."
    cat > .env.example << 'EOF'
# GCP Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
GCP_REGION=us-central1

# API Keys
GOOGLE_API_KEY=your-gemini-api-key-here
SENDGRID_API_KEY=your-sendgrid-key-here

# Firestore
FIRESTORE_DATABASE=(default)

# Vertex AI
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_INDEX_ENDPOINT=your-endpoint-id

# Cloud Storage
GCS_BUCKET_PDFS=your-project-id-pdfs
GCS_BUCKET_CACHE=your-project-id-cache

# Pub/Sub Topics
PUBSUB_TOPIC_CANDIDATES=arxiv.candidates
PUBSUB_TOPIC_READY=docs.ready
PUBSUB_TOPIC_MATCHES=arxiv.matches

# Feature Flags (for Crawl/Walk/Run phases)
ENABLE_GRAPH_VISUALIZATION=true
ENABLE_PROACTIVE_ALERTS=true
ENABLE_CONTRADICTION_DETECTION=true
ENABLE_CONFIDENCE_SCORING=true
ENABLE_GPU_MODE=false
ENABLE_DEBATE_SYSTEM=false
ENABLE_MCP_SERVER=false

# Environment
ENV=development  # development, staging, production
LOG_LEVEL=INFO
DEBUG=false

# Service URLs (for local development)
API_GATEWAY_URL=http://localhost:8080
ORCHESTRATOR_URL=http://localhost:8081
GRAPH_SERVICE_URL=http://localhost:8082

# Frontend
REACT_APP_API_URL=http://localhost:8080

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Agent Configuration
DEFAULT_MODEL=gemini-2.0-flash-exp
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=2048
DEFAULT_TIMEOUT=30

# Testing
TEST_MODE=false
USE_FIXTURES=false
EOF
    echo -e "${GREEN}✅ .env.example created${NC}"
else
    echo -e "${YELLOW}⚠️  .env.example already exists, skipping${NC}"
fi

# README.md
if [[ ! -f "README.md" ]]; then
    echo "Creating README.md..."
    cat > README.md << 'EOF'
# Research Intelligence Platform

Multi-agent AI system for monitoring research literature, building knowledge graphs, and providing proactive intelligence to researchers.

**Built with**: Google ADK, Cloud Run, Gemini 2.0, Firestore

---

## 🎯 Project Overview

This platform uses 7 specialized AI agents to:
- 📚 Automatically ingest and index research papers
- 🕸️ Build knowledge graphs showing paper relationships
- 🔔 Proactively alert researchers to relevant publications
- 💬 Answer questions with citations and confidence scores
- 🔍 Detect contradictions and controversies in research

---

## 🏗️ Architecture

- **Services**: API Gateway, Orchestrator, Graph Service, Frontend
- **Jobs**: arXiv Watcher, Intake Pipeline, Graph Updater, Digest Generator
- **Workers**: Alert Worker (Pub/Sub consumer)

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Cloud Project
- Gemini API key

### Setup

```bash
# 1. Run setup script
bash scripts/setup_project.sh

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Verify setup
python scripts/test_setup.py
```

---

## 📋 Implementation Phases

### Phase 1: Crawl (Days 0-1)
- ✅ Basic PDF ingestion
- ✅ Simple Q&A with citations
- **Goal**: Prove concept end-to-end

### Phase 2: Walk (Days 2-3)
- ✅ Knowledge graph relationships
- ✅ Proactive alerting system
- ✅ Multi-agent intelligence
- ✅ Confidence scoring
- **Goal**: Add trust and intelligence

### Phase 3: Run (Day 4)
- ✅ Production deployment
- ✅ Visualization
- ✅ Demo preparation
- **Goal**: Polish and ship

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed plan.

---

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# Verify Phase 0 setup
python scripts/test_setup.py
```

---

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Code organization
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Phased development plan
- [PHASE_0_SETUP_GUIDE.md](PHASE_0_SETUP_GUIDE.md) - Environment setup guide

---

## 🛠️ Development

### Local Development

```bash
# Activate environment
source venv/bin/activate

# Run API Gateway locally
cd src/services/api_gateway
python main.py

# Run Orchestrator locally
cd src/services/orchestrator
python main.py
```

### Docker Development

```bash
# Build all images
docker-compose build

# Run services
docker-compose up
```

---

## 🌐 Deployment

### Deploy to Cloud Run

```bash
# Deploy all services
bash scripts/deploy_all.sh

# Deploy individual service
gcloud run deploy api-gateway \
  --source ./src/services/api_gateway \
  --region us-central1
```

---

## 📊 Project Status

- [x] Phase 0: Environment Setup
- [ ] Phase 1: Crawl - Basic Features
- [ ] Phase 2: Walk - Intelligence Layer
- [ ] Phase 3: Run - Production Ready

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file

---

## 🤝 Contributing

This is a hackathon project. Contributions welcome after initial submission!

---

## 🏆 Hackathon

Built for **Google Cloud Run Hackathon** - AI Agents Category

**Requirements Met**:
- ✅ Multi-agent application (7 agents)
- ✅ Google ADK framework
- ✅ Deployed to Cloud Run
- ✅ All 3 resource types (Services, Jobs, Workers)
- ✅ Solves real-world problem

---

**For more information**, see documentation files or run `python scripts/test_setup.py` to verify your environment.
EOF
    echo -e "${GREEN}✅ README.md created${NC}"
else
    echo -e "${YELLOW}⚠️  README.md already exists, skipping${NC}"
fi

# requirements.txt stub
if [[ ! -f "requirements.txt" ]]; then
    echo "Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
# Core ADK and Google AI
google-adk>=0.1.0
google-generativeai>=0.3.0

# Google Cloud Services
google-cloud-firestore>=2.14.0
google-cloud-storage>=2.14.0
google-cloud-pubsub>=2.19.0
google-cloud-aiplatform>=1.38.0

# PDF Processing
PyMuPDF>=1.23.8
pdfplumber>=0.10.3

# ML/NLP
sentence-transformers>=2.2.2
numpy>=1.24.3

# Web Framework
flask>=3.0.0
flask-cors>=4.0.0
gunicorn>=21.2.0

# Utilities
python-dotenv>=1.0.0
requests>=2.31.0
pydantic>=2.5.0

# Development
pytest>=7.4.3
pytest-asyncio>=0.21.1
black>=23.12.0
flake8>=6.1.0
mypy>=1.7.0
EOF
    echo -e "${GREEN}✅ requirements.txt created${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt already exists, skipping${NC}"
fi

# Create placeholder files in key directories
echo ""
echo -e "${BLUE}Creating placeholder files...${NC}"

# src/agents/base.py
cat > src/agents/base.py << 'EOF'
"""
Base agent class for Research Intelligence Platform

Provides common functionality for all agents.
"""

from google.adk.agents import LlmAgent
from typing import List, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class BaseResearchAgent:
    """Base class for all research intelligence agents"""

    def __init__(self, name: str, model: str = "gemini-2.0-flash-exp"):
        self.name = name
        self.model = model
        self._agent: Optional[LlmAgent] = None
        logger.info(f"Initialized {name}")

    def create_agent(
        self,
        description: str,
        instruction: str,
        tools: List[Callable],
        output_key: str
    ) -> LlmAgent:
        """
        Factory method to create ADK agent

        Args:
            description: Brief description for routing
            instruction: Detailed instruction for the agent
            tools: List of tool functions
            output_key: Key to store output in state

        Returns:
            LlmAgent instance
        """
        return LlmAgent(
            name=self.name,
            model=self.model,
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
        """Override in subclass to define agent"""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _create_agent()"
        )

    def run(self, input_data: dict) -> dict:
        """Run the agent with input data"""
        logger.info(f"Running {self.name}")
        return self.agent.run(input_data)
EOF

# src/utils/config.py
cat > src/utils/config.py << 'EOF'
"""
Configuration management for Research Intelligence Platform
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class GCPConfig:
    """GCP configuration"""
    project_id: str
    region: str
    credentials_path: Optional[str]


@dataclass
class AgentConfig:
    """Agent configuration"""
    default_model: str
    temperature: float
    max_tokens: int
    timeout: int


@dataclass
class Config:
    """Main configuration"""
    gcp: GCPConfig
    agent: AgentConfig
    env: str
    debug: bool


def load_config() -> Config:
    """Load configuration from environment variables"""
    return Config(
        gcp=GCPConfig(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT', ''),
            region=os.getenv('GCP_REGION', 'us-central1'),
            credentials_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        ),
        agent=AgentConfig(
            default_model=os.getenv('DEFAULT_MODEL', 'gemini-2.0-flash-exp'),
            temperature=float(os.getenv('DEFAULT_TEMPERATURE', '0.3')),
            max_tokens=int(os.getenv('DEFAULT_MAX_TOKENS', '2048')),
            timeout=int(os.getenv('DEFAULT_TIMEOUT', '30'))
        ),
        env=os.getenv('ENV', 'development'),
        debug=os.getenv('DEBUG', 'false').lower() == 'true'
    )


# Global config instance
config = load_config()
EOF

# src/utils/logging.py
cat > src/utils/logging.py << 'EOF'
"""
Logging configuration for Research Intelligence Platform
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None
) -> None:
    """
    Setup logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_string: Custom format string (optional)
    """
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set third-party loggers to WARNING
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
EOF

# tests/conftest.py
cat > tests/conftest.py << 'EOF'
"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


@pytest.fixture
def sample_paper():
    """Sample paper data for testing"""
    return {
        'paper_id': 'test:001',
        'title': 'Test Paper on Machine Learning',
        'authors': ['Smith, J.', 'Doe, A.'],
        'year': 2023,
        'abstract': 'This is a test paper about machine learning.',
        'entities': {
            'methods': ['neural_networks', 'deep_learning'],
            'findings': ['improved_accuracy', 'faster_training'],
            'datasets': ['imagenet', 'cifar10']
        }
    }


@pytest.fixture
def sample_question():
    """Sample question for testing"""
    return "What methods were used in the paper?"


@pytest.fixture
def mock_firestore(monkeypatch):
    """Mock Firestore client for testing"""
    class MockFirestore:
        def collection(self, name):
            return self

        def document(self, id):
            return self

        def get(self):
            return self

        def exists(self):
            return True

        def to_dict(self):
            return {'test': 'data'}

    monkeypatch.setattr('google.cloud.firestore.Client', MockFirestore)
    return MockFirestore()
EOF

echo -e "${GREEN}✅ Placeholder files created${NC}"
echo ""

# Summary
echo ""
echo "=================================================="
echo -e "${GREEN}✅ Project Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Directory structure created:"
echo "  • src/ - Source code (agents, tools, services, etc.)"
echo "  • tests/ - Test suite"
echo "  • docs/ - Documentation"
echo "  • scripts/ - Utility scripts"
echo "  • infra/ - Infrastructure as Code"
echo ""
echo "Configuration files created:"
echo "  • .gitignore"
echo "  • .env.example"
echo "  • README.md"
echo "  • requirements.txt"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Review PROJECT_STRUCTURE.md for details"
echo "  2. Follow PHASE_0_SETUP_GUIDE.md for environment setup"
echo "  3. Run: python -m venv venv && source venv/bin/activate"
echo "  4. Run: pip install -r requirements.txt"
echo "  5. Run: cp .env.example .env (and edit with your keys)"
echo "  6. Run: python scripts/test_setup.py (when ready)"
echo ""
echo -e "${GREEN}Happy building! 🚀${NC}"
echo ""
