# Research Intelligence Platform

Multi-agent AI system for monitoring research literature, building knowledge graphs, and providing proactive intelligence to researchers.

**Built with**: Google Gemini API, Cloud Run, Gemini 2.0 Flash & Gemini 2.5 Pro, Firestore

**🎉 Live Demo**: https://frontend-up5qa34vea-uc.a.run.app

---

## 🎯 Project Overview

This platform uses 6 specialized AI agents to:
- 📚 Automatically ingest and index research papers from arXiv
- 🕸️ Build knowledge graphs showing paper relationships (150 relationships across 49 papers)
- 🔔 Proactively alert researchers to relevant publications
- 💬 Answer questions with citations and confidence scores
- 🔍 Detect contradictions and controversies in research

**Key Achievement**: Improved knowledge graph density from 7.7% to **12.8%** (66% improvement) through multi-agent relationship detection with selective confidence thresholds.

---

## 🏗️ Architecture

### Production Services (All Healthy ✅)

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | https://frontend-up5qa34vea-uc.a.run.app | React UI with D3.js graph visualization |
| **API Gateway** | https://api-gateway-up5qa34vea-uc.a.run.app | Request routing, service discovery |
| **Orchestrator** | https://orchestrator-up5qa34vea-uc.a.run.app | Coordinates ingestion & Q&A workflows |
| **Graph Service** | https://graph-service-up5qa34vea-uc.a.run.app | Knowledge graph queries & traversal |
| **Intake Pipeline** | Cloud Run Job | Paper ingestion processing |
| **Graph Updater** | Cloud Run Job | Relationship detection & updates |

### AI Agents (All ADK-Compliant)

All agents use Google ADK primitives (LlmAgent, Runner, InMemorySessionService) with Gemini 2.5 Pro:

- **Entity Agent** - Extracts authors, methods, datasets, and infers arXiv category
- **Relationship Agent** - Detects paper relationships: extends, supports, contradicts
- **Answer Agent** - Generates answers with citations
- **Confidence Agent** - Scores answer confidence
- **Graph Query Agent** - Translates natural language to graph queries
- **Alert Matching Agent** - Matches papers to user watch rules with explanations

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture diagrams.

---

## 📊 Knowledge Graph Metrics

- **Papers**: 49 AI/ML research papers
- **Relationships**: 150 total
  - 124 "extends" relationships
  - 26 "supports" relationships
- **Graph Density**: 12.8% (up from 7.7%)
- **Relationship Types**: extends, supports, contradicts, cites, builds_on, applies

**Optimization Story**: We improved graph density by 66% through:
1. Temperature increase (0.3 → 0.7) for more diverse LLM outputs
2. Refined relationship detection prompt
3. Selective confidence thresholds (contradicts=0.7, extends/supports=0.5)
4. Union strategy to account for LLM variation

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- [UV](https://github.com/astral-sh/uv) - Fast Python package installer
- Google Cloud Project
- Gemini API key

### Local Setup

```bash
# 1. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on macOS: brew install uv

# 2. Clone repository
git clone https://github.com/yourusername/research-intelligence-agents.git
cd research-intelligence-agents

# 3. Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   GOOGLE_CLOUD_PROJECT=your-project-id
#   GOOGLE_API_KEY=your-gemini-api-key
#   DEFAULT_MODEL=gemini-2.5-pro
#   FROM_EMAIL=your-email@example.com  # For alert notifications
#   SENDGRID_API_KEY=your-sendgrid-key  # Optional, for email delivery

# 5. Verify setup
python scripts/test_setup.py
```

### Why UV?

UV is a blazingly fast Python package installer written in Rust:
- 🚀 **10-100x faster** than pip
- 📦 Drop-in replacement for pip
- 🔒 Reliable dependency resolution
- 💾 Better caching

---

## 🌐 Deployment

### Deploy to Cloud Run

```bash
# Deploy all services
bash scripts/deploy_all_services.sh

# Verify deployment
bash scripts/verify_services.sh
```

### Individual Service Deployment

```bash
# Deploy specific service
gcloud run deploy api-gateway \
  --source ./src/services/api_gateway \
  --region us-central1 \
  --allow-unauthenticated
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment procedures.

---

## 💻 Development

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

### Adding Papers

```bash
# Add demo papers
uv run python scripts/add_papers.py

# Add specific AI papers
uv run python scripts/add_ai_papers.py

# Generate relationships
uv run python scripts/populate_relationships.py
```

### Testing

```bash
# Run all tests
pytest

# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Test specific functionality
python scripts/test_qa_comprehensive.py
python scripts/test_relationship_detection.py
python scripts/test_graph_queries.py
```

---

## 📋 Implementation Phases

### ✅ Phase 1: Crawl (Days 0-1) - COMPLETE
- ✅ Basic PDF ingestion from arXiv
- ✅ Simple Q&A with citations
- ✅ Entity extraction
- **Result**: Proved concept end-to-end

### ✅ Phase 2: Walk (Days 2-3) - COMPLETE
- ✅ Knowledge graph relationships (150 relationships)
- ✅ Proactive alerting system with SendGrid
- ✅ Multi-agent intelligence (7 agents)
- ✅ Confidence scoring for answers
- ✅ Graph density optimization (66% improvement)
- **Result**: Added trust and intelligence layer

### ✅ Phase 3: Run (Day 4) - COMPLETE
- ✅ Production deployment to Cloud Run
- ✅ Interactive graph visualization with D3.js
- ✅ Service health monitoring
- ✅ Comprehensive documentation
- **Result**: Production-ready for demo

See [docs/planning/IMPLEMENTATION_PLAN.md](docs/planning/IMPLEMENTATION_PLAN.md) for detailed phase breakdown.

---

## 📚 Documentation

### 🎯 Quick Links
- [DEMO_GUIDE.md](DEMO_GUIDE.md) - Hackathon presentation guide
- [API_REFERENCE.md](API_REFERENCE.md) - API endpoints and examples
- [docs/CODEBASE_AUDIT_2025-11-08.md](docs/CODEBASE_AUDIT_2025-11-08.md) - Comprehensive codebase audit

### 📖 Getting Started
- [docs/guides/PHASE_0_SETUP_GUIDE.md](docs/guides/PHASE_0_SETUP_GUIDE.md) - Environment setup guide
- [docs/guides/UV_SETUP.md](docs/guides/UV_SETUP.md) - UV package manager guide
- [docs/guides/GCP_ARXIV_SETUP.md](docs/guides/GCP_ARXIV_SETUP.md) - GCP project & arXiv API setup
- [docs/guides/GENAI_SDK_MIGRATION.md](docs/guides/GENAI_SDK_MIGRATION.md) - Google GenAI SDK migration guide

### 🗺️ Planning & Architecture
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture with diagrams
- [docs/planning/IMPLEMENTATION_PLAN.md](docs/planning/IMPLEMENTATION_PLAN.md) - Phased development plan (Crawl/Walk/Run)
- [docs/planning/KNOWLEDGE_GRAPH_DESIGN.md](docs/planning/KNOWLEDGE_GRAPH_DESIGN.md) - Graph schema & relationship types
- [docs/planning/STATUS.md](docs/planning/STATUS.md) - Current progress tracker

### 📋 Reference
- [docs/reference/HackathonBrief.md](docs/reference/HackathonBrief.md) - Google Cloud Run Hackathon requirements
- [FUTURE_ROADMAP.md](FUTURE_ROADMAP.md) - Planned features and enhancements

---

## 📊 Project Status

- [x] Phase 0: Environment Setup
- [x] Phase 1: Crawl - Basic Features (PDF ingestion, Q&A, citations)
- [x] Phase 2: Walk - Intelligence Layer (Graph, alerts, confidence scoring)
- [x] Phase 3: Run - Production Ready (Deployment, visualization, monitoring)

**Current Status**: Production-ready, all services deployed and healthy ✅

---

## 🏆 Hackathon

Built for **Google Cloud Run Hackathon** - AI Agents Category

**Requirements Met**:
- ✅ Multi-agent application (6 specialized agents)
- ✅ Google Gemini API integration
- ✅ Deployed to Cloud Run (6 services + 2 jobs + 1 worker)
- ✅ All 3 resource types: Services, Jobs, Workers
- ✅ Solves real-world problem (research literature monitoring)
- ✅ Agent collaboration (multi-agent orchestration)
- ✅ Production-ready with monitoring

**Unique Features**:
- Knowledge graph with 12.8% density (150 relationships)
- Multi-agent relationship detection with selective thresholds
- Interactive graph visualization
- Proactive alerting system
- Confidence-scored Q&A with citations

---

## 🔑 Key Features

### 1. Intelligent Paper Ingestion
- Automatic PDF download from arXiv
- arXiv metadata fetching from arXiv API for manual uploads
- Filename-based arXiv ID extraction (e.g., 2411.04997.pdf)
- Entity extraction (authors, methods, datasets)
- LLM-based arXiv category inference
- Semantic indexing with embeddings
- Metadata enrichment

### 2. Knowledge Graph Construction
- Multi-agent relationship detection
- 6 relationship types: extends, supports, contradicts, cites, builds_on, applies
- Temporal constraint handling (papers can only reference older papers)
- Graph density optimization through LLM temperature tuning

### 3. Interactive Visualization
- D3.js force-directed graph
- Node coloring by paper category
- Relationship type filtering
- Hover tooltips with paper metadata
- Click to view paper details

### 4. Proactive Alerting
- User-defined interest profiles (claim-based, keyword, author, relationship)
- Semantic matching with Gemini
- Enhanced email notifications with:
  - Paper category/field display
  - Key findings excerpt
  - Match confidence percentage with color coding
  - More specific subject lines
- Email notifications via SendGrid
- Alert history tracking
- Watch rules default to FROM_EMAIL if not specified

### 5. Q&A with Citations
- Natural language question answering
- Confidence scoring (0-1 scale)
- Source citations with paper IDs
- Graph-augmented retrieval

---

## 📁 Project Structure

```
research-intelligence-agents/
├── src/                      # Core application code
│   ├── agents/              # AI agents (entity, relationship, Q&A, confidence, alert)
│   ├── pipelines/           # Ingestion & Q&A orchestration
│   ├── services/            # 6 Cloud Run services
│   ├── jobs/                # Background jobs (arXiv watcher, graph updater)
│   ├── workers/             # Pub/Sub workers (alert worker)
│   ├── tools/               # PDF reading, retrieval, graph queries
│   ├── storage/             # Firestore client
│   └── utils/               # Config, logging, embeddings
│
├── scripts/                  # 54 operational scripts
│   ├── deploy_all_services.sh
│   ├── add_papers.py
│   ├── populate_relationships.py
│   └── test_*.py
│
├── docs/                     # Comprehensive documentation
│   ├── guides/              # Setup & migration guides
│   ├── planning/            # Phase plans & design docs
│   └── reference/           # Hackathon brief
│
└── tests/                    # Test suite (pytest)
    ├── unit/                # Unit tests
    ├── integration/         # Integration tests
    └── fixtures/            # Test papers & expected outputs
```

---

## 🤝 Contributing

This is a hackathon project. Contributions welcome after initial submission!

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- **Google Cloud Run Hackathon** for the opportunity
- **Google Gemini API** for powerful LLM capabilities
- **arXiv.org** for open access to research papers
- **D3.js** for graph visualization

---

## 📞 Contact

For questions or feedback, please open an issue on GitHub.
