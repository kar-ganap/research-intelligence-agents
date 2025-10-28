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
- [UV](https://github.com/astral-sh/uv) - Fast Python package installer
- Google Cloud Project
- Gemini API key

### Setup

```bash
# 1. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on macOS: brew install uv

# 2. Run setup script
bash scripts/setup_project.sh

# 3. Create virtual environment and install dependencies with UV
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 4. Install dependencies (UV is 10-100x faster than pip!)
uv pip install -e ".[dev]"

# 5. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 6. Verify setup
python scripts/test_setup.py
```

### Why UV?

UV is a blazingly fast Python package installer written in Rust:
- 🚀 **10-100x faster** than pip
- 📦 Drop-in replacement for pip
- 🔒 Reliable dependency resolution
- 💾 Better caching

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

### 📖 Getting Started
- [docs/guides/PHASE_0_SETUP_GUIDE.md](docs/guides/PHASE_0_SETUP_GUIDE.md) - Environment setup guide
- [docs/guides/UV_SETUP.md](docs/guides/UV_SETUP.md) - UV package manager guide
- [docs/guides/GCP_ARXIV_SETUP.md](docs/guides/GCP_ARXIV_SETUP.md) - GCP project & arXiv API setup
- [docs/guides/GENAI_SDK_MIGRATION.md](docs/guides/GENAI_SDK_MIGRATION.md) - Google GenAI SDK migration guide

### 🗺️ Planning & Architecture
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture with diagrams
- [docs/planning/IMPLEMENTATION_PLAN.md](docs/planning/IMPLEMENTATION_PLAN.md) - Phased development plan (Crawl/Walk/Run)
- [docs/planning/PROJECT_STRUCTURE.md](docs/planning/PROJECT_STRUCTURE.md) - Code organization
- [docs/planning/STATUS.md](docs/planning/STATUS.md) - Current progress tracker
- [docs/planning/research-intelligence-platform-complete-plan.md](docs/planning/research-intelligence-platform-complete-plan.md) - Original complete plan

### 📋 Reference
- [docs/reference/HackathonBrief.md](docs/reference/HackathonBrief.md) - Google Cloud Run Hackathon requirements
- [docs/reference/Developer Tutorial_ Building AI Agents with Google ADK (Python SDK).pdf](docs/reference/Developer%20Tutorial_%20Building%20AI%20Agents%20with%20Google%20ADK%20(Python%20SDK).pdf) - ADK tutorial PDF

---

## 🛠️ Development

### Local Development

```bash
# Activate environment
source .venv/bin/activate

# Run API Gateway locally
cd src/services/api_gateway
python main.py

# Run Orchestrator locally
cd src/services/orchestrator
python main.py

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
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
