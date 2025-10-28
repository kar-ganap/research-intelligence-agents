# Phase 0: Setup Guide - Research Intelligence Platform

**Estimated Time**: 2-3 hours (hard cap)
**Goal**: Get development environment ready with all dependencies working
**Status**: Pre-hackathon preparation

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [Verification Tests](#verification-tests)
5. [Troubleshooting](#troubleshooting)
6. [Go/No-Go Decision](#gono-go-decision)

---

## Overview

### What Phase 0 Achieves

By the end of Phase 0, you'll have:
- ✅ Python environment with ADK installed
- ✅ GCP project configured
- ✅ Gemini API working
- ✅ Firestore database created
- ✅ Local project structure
- ✅ Verified everything works

### Why This Matters

**Phase 0 is your foundation**. If you start Phase 1 without proper setup, you'll waste time debugging environment issues instead of building features.

**Time Investment**: 2-3 hours now saves 6-8 hours of frustration later.

---

## Prerequisites

### Required Accounts

- [ ] **Google Cloud Account** (free tier OK)
  - New accounts get $300 credit
  - URL: https://console.cloud.google.com

- [ ] **Google AI Studio Account** (for Gemini API key)
  - Free tier available
  - URL: https://aistudio.google.com

- [ ] **SendGrid Account** (optional for Phase 2)
  - Free tier: 100 emails/day
  - URL: https://sendgrid.com

### System Requirements

- **Python**: 3.9 or higher (3.11 recommended)
- **pip**: Latest version
- **git**: For version control
- **OS**: macOS, Linux, or Windows with WSL

### Check Your System

```bash
# Check Python version
python --version  # Should be 3.9+

# Check pip
pip --version

# Check git
git --version
```

---

## Step-by-Step Setup

### Task 1: Python Environment (15 minutes)

#### Create Virtual Environment

```bash
# Navigate to project directory
cd ~/Documents/Personal/random_projects/research-intelligence-agents

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your prompt
```

#### Install Core Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install ADK and dependencies
pip install google-adk
pip install google-generativeai
pip install google-cloud-firestore
pip install google-cloud-storage
pip install google-cloud-pubsub
pip install PyMuPDF  # For PDF processing
pip install python-dotenv

# Verify ADK installation
python -c "from google.adk import LlmAgent; print('✅ ADK installed successfully')"
```

**Expected Output**:
```
✅ ADK installed successfully
```

**If this fails**, see [Troubleshooting](#troubleshooting).

#### Create requirements.txt

```bash
# Generate requirements file
pip freeze > requirements.txt
```

**✅ Checkpoint 1**: ADK imports without errors

---

### Task 2: GCP Project Setup (20 minutes)

#### Create GCP Project

1. Go to https://console.cloud.google.com
2. Click "Select a project" → "New Project"
3. Project name: `research-intelligence-platform`
4. Project ID: `research-intel-[your-id]` (note this!)
5. Click "Create"

#### Enable Required APIs

```bash
# Set your project ID
export PROJECT_ID="research-intel-[your-id]"
gcloud config set project $PROJECT_ID

# Enable APIs (takes 2-3 minutes)
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

**Expected Output**:
```
Operation "operations/..." finished successfully.
```

#### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create research-intel-sa \
    --display-name="Research Intelligence Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:research-intel-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:research-intel-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Download service account key
gcloud iam service-accounts keys create ~/research-intel-key.json \
    --iam-account=research-intel-sa@$PROJECT_ID.iam.gserviceaccount.com

echo "✅ Service account key saved to ~/research-intel-key.json"
```

**⚠️ IMPORTANT**: Keep this key file secure! Add it to `.gitignore`.

**✅ Checkpoint 2**: GCP project created and APIs enabled

---

### Task 3: Firestore Database (10 minutes)

#### Create Firestore Database

```bash
# Create Firestore database in Native mode
gcloud firestore databases create \
    --location=us-central1 \
    --type=firestore-native

echo "✅ Firestore database created"
```

**Alternative**: Use Cloud Console
1. Go to https://console.cloud.google.com/firestore
2. Click "Select Native Mode"
3. Choose location: `us-central1`
4. Click "Create Database"

#### Verify Firestore Access

```python
# test_firestore.py
from google.cloud import firestore
import os

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('~/research-intel-key.json')

# Initialize client
db = firestore.Client(project='research-intel-[your-id]')

# Test write
test_ref = db.collection('_test').document('test_doc')
test_ref.set({'message': 'Hello from Phase 0!', 'timestamp': firestore.SERVER_TIMESTAMP})

# Test read
doc = test_ref.get()
if doc.exists:
    print(f"✅ Firestore working! Data: {doc.to_dict()}")
else:
    print("❌ Firestore read failed")

# Cleanup
test_ref.delete()
print("✅ Test document cleaned up")
```

**Run the test**:
```bash
python test_firestore.py
```

**Expected Output**:
```
✅ Firestore working! Data: {'message': 'Hello from Phase 0!', 'timestamp': ...}
✅ Test document cleaned up
```

**✅ Checkpoint 3**: Firestore read/write works

---

### Task 4: Gemini API Setup (10 minutes)

#### Get API Key

1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Select your GCP project
4. Copy the API key (starts with `AIza...`)

**⚠️ IMPORTANT**: Never commit this key to git!

#### Test Gemini API

```python
# test_gemini.py
import google.generativeai as genai
import os

# Configure API key
api_key = "YOUR_API_KEY_HERE"  # Replace with your key
genai.configure(api_key=api_key)

# Test API call
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content('Say "Hello from Gemini!" in exactly those words.')

print(f"✅ Gemini API working!")
print(f"Response: {response.text}")
```

**Run the test**:
```bash
python test_gemini.py
```

**Expected Output**:
```
✅ Gemini API working!
Response: Hello from Gemini!
```

**✅ Checkpoint 4**: Gemini API returns responses

---

### Task 5: ADK Agent Test (15 minutes)

#### Create First ADK Agent

```python
# test_adk_agent.py
from google.adk.agents import LlmAgent
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Define a simple tool function
def get_current_year() -> str:
    """Returns the current year"""
    return "2025"

# Create an ADK agent
test_agent = LlmAgent(
    name="TestAgent",
    model="gemini-2.0-flash-exp",
    description="A test agent that answers questions about the year",
    instruction="""
    You are a helpful assistant.
    If asked about the current year, use the get_current_year tool.
    Answer concisely.
    """,
    tools=[get_current_year],
    output_key="answer"
)

# Test the agent
print("Testing ADK Agent...")
print("-" * 50)

# Run agent
from google.adk.runners import Runner

runner = Runner()
result = runner.run(
    agent=test_agent,
    user_input="What year is it?"
)

print(f"✅ ADK Agent executed successfully!")
print(f"Answer: {result.get('answer', 'No answer found')}")
```

**Setup .env file first**:
```bash
# Create .env file
cat > .env << EOF
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=$HOME/research-intel-key.json
GOOGLE_CLOUD_PROJECT=research-intel-[your-id]
EOF
```

**Run the test**:
```bash
python test_adk_agent.py
```

**Expected Output**:
```
Testing ADK Agent...
--------------------------------------------------
✅ ADK Agent executed successfully!
Answer: The current year is 2025.
```

**✅ Checkpoint 5**: ADK agent runs and uses tools

---

### Task 6: Project Structure (20 minutes)

#### Create Directory Structure

```bash
# Create all directories
mkdir -p src/{agents,tools,pipelines,services,jobs,workers,storage,models,utils,config}
mkdir -p src/agents/ingestion
mkdir -p src/services/{api_gateway,orchestrator,graph_service,frontend}
mkdir -p src/jobs/{arxiv_watcher,intake_pipeline,graph_updater,weekly_digest,nightly_eval}
mkdir -p src/workers/alert_worker
mkdir -p tests/{unit,integration,e2e,fixtures}
mkdir -p docs/{api,adk,deployment,diagrams}
mkdir -p scripts
mkdir -p infra/{terraform,cloudbuild}
mkdir -p data/{papers,cache,eval}
mkdir -p monitoring/{dashboards,alerts}

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;

echo "✅ Project structure created"
```

#### Create Essential Files

```bash
# .gitignore
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

# Environment
.env
.env.local

# Credentials
*.json
!package.json
*-key.json
credentials/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Data
data/
*.pdf
cache/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Build
dist/
build/
*.egg-info/
EOF

# .env.example
cat > .env.example << 'EOF'
# GCP Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCP_REGION=us-central1

# API Keys
GOOGLE_API_KEY=your-gemini-api-key
SENDGRID_API_KEY=your-sendgrid-key

# Firestore
FIRESTORE_DATABASE=(default)

# Environment
ENV=development
LOG_LEVEL=INFO
EOF

# README.md
cat > README.md << 'EOF'
# Research Intelligence Platform

Multi-agent system for monitoring research literature, built with Google ADK and Cloud Run.

## Setup

See [PHASE_0_SETUP_GUIDE.md](PHASE_0_SETUP_GUIDE.md) for detailed setup instructions.

## Quick Start

```bash
# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# Test
python scripts/test_setup.py
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture.

## Implementation Plan

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for phased development plan.
EOF

echo "✅ Essential files created"
```

**✅ Checkpoint 6**: Project structure exists

---

### Task 7: Create Setup Verification Script (15 minutes)

```python
# scripts/test_setup.py
"""
Phase 0 Setup Verification Script

Tests all components to ensure environment is ready for Phase 1.
"""

import sys
import os
from typing import Dict, Any

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def test_python_version() -> bool:
    """Test Python version is 3.9+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"{GREEN}✅{RESET} Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"{RED}❌{RESET} Python version too old: {version.major}.{version.minor}")
        return False

def test_adk_import() -> bool:
    """Test ADK imports"""
    try:
        from google.adk import LlmAgent
        from google.adk.agents import SequentialAgent, ParallelAgent
        print(f"{GREEN}✅{RESET} ADK imports successfully")
        return True
    except ImportError as e:
        print(f"{RED}❌{RESET} ADK import failed: {e}")
        return False

def test_gemini_api() -> bool:
    """Test Gemini API connection"""
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')

        if not api_key:
            print(f"{RED}❌{RESET} GOOGLE_API_KEY not set in .env")
            return False

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content('Say "OK" in one word.')

        if response.text:
            print(f"{GREEN}✅{RESET} Gemini API working")
            return True
        else:
            print(f"{RED}❌{RESET} Gemini API returned empty response")
            return False

    except Exception as e:
        print(f"{RED}❌{RESET} Gemini API test failed: {e}")
        return False

def test_firestore_connection() -> bool:
    """Test Firestore connection"""
    try:
        from google.cloud import firestore
        from dotenv import load_dotenv

        load_dotenv()

        db = firestore.Client()

        # Write test document
        test_ref = db.collection('_phase0_test').document('test')
        test_ref.set({'status': 'testing', 'phase': 0})

        # Read test document
        doc = test_ref.get()

        # Cleanup
        test_ref.delete()

        if doc.exists:
            print(f"{GREEN}✅{RESET} Firestore read/write working")
            return True
        else:
            print(f"{RED}❌{RESET} Firestore read failed")
            return False

    except Exception as e:
        print(f"{RED}❌{RESET} Firestore test failed: {e}")
        return False

def test_project_structure() -> bool:
    """Test project structure exists"""
    required_dirs = [
        'src/agents',
        'src/tools',
        'src/pipelines',
        'src/storage',
        'tests/unit',
        'docs'
    ]

    all_exist = True
    for directory in required_dirs:
        if os.path.isdir(directory):
            print(f"{GREEN}✅{RESET} {directory} exists")
        else:
            print(f"{RED}❌{RESET} {directory} missing")
            all_exist = False

    return all_exist

def test_pdf_processing() -> bool:
    """Test PDF processing library"""
    try:
        import fitz  # PyMuPDF
        print(f"{GREEN}✅{RESET} PyMuPDF (PDF processing) available")
        return True
    except ImportError:
        print(f"{RED}❌{RESET} PyMuPDF not installed (pip install PyMuPDF)")
        return False

def test_env_file() -> bool:
    """Test .env file exists and has required vars"""
    if not os.path.exists('.env'):
        print(f"{RED}❌{RESET} .env file not found (copy from .env.example)")
        return False

    from dotenv import load_dotenv
    load_dotenv()

    required_vars = ['GOOGLE_API_KEY', 'GOOGLE_CLOUD_PROJECT']
    missing = []

    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"{RED}❌{RESET} Missing env vars: {', '.join(missing)}")
        return False
    else:
        print(f"{GREEN}✅{RESET} .env file configured")
        return True

def run_all_tests() -> Dict[str, bool]:
    """Run all verification tests"""
    print("=" * 60)
    print("PHASE 0 SETUP VERIFICATION")
    print("=" * 60)
    print()

    tests = {
        'Python Version': test_python_version,
        'ADK Import': test_adk_import,
        'Gemini API': test_gemini_api,
        'Firestore': test_firestore_connection,
        'Project Structure': test_project_structure,
        'PDF Processing': test_pdf_processing,
        'Environment File': test_env_file
    }

    results = {}

    for name, test_func in tests.items():
        print(f"\n[{name}]")
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"{RED}❌{RESET} Unexpected error: {e}")
            results[name] = False

    return results

def print_summary(results: Dict[str, bool]):
    """Print summary and decision"""
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    print(f"\nTests Passed: {passed}/{total}")
    print()

    # Level 1 (Blockers)
    blockers = [
        'Python Version',
        'ADK Import',
        'Gemini API',
        'Firestore',
        'Project Structure'
    ]

    level_1_pass = all(results.get(b, False) for b in blockers)

    # Level 2 (Important but not blocking)
    nice_to_have = ['PDF Processing', 'Environment File']
    level_2_pass = all(results.get(n, False) for n in nice_to_have)

    print("GO/NO-GO DECISION:")
    print("-" * 60)

    if level_1_pass and level_2_pass:
        print(f"{GREEN}✅ GO{RESET} - All tests passed")
        print(f"{GREEN}Ready to proceed to Phase 1.1{RESET}")
        return True
    elif level_1_pass:
        print(f"{YELLOW}⚠️  CONDITIONAL GO{RESET} - Level 1 tests passed")
        print(f"{YELLOW}Some optional features may not work{RESET}")
        failed = [k for k, v in results.items() if not v and k in nice_to_have]
        print(f"Failed: {', '.join(failed)}")
        print(f"{YELLOW}Can proceed but fix these before Phase 2{RESET}")
        return True
    else:
        print(f"{RED}❌ NO-GO{RESET} - Critical tests failed")
        failed = [k for k, v in results.items() if not v and k in blockers]
        print(f"Blockers: {', '.join(failed)}")
        print(f"{RED}Fix these issues before proceeding{RESET}")
        return False

if __name__ == '__main__':
    results = run_all_tests()
    can_proceed = print_summary(results)

    print()
    print("=" * 60)

    if can_proceed:
        print(f"\n{GREEN}Next Step:{RESET} Run 'python scripts/phase_1_start.py'")
    else:
        print(f"\n{RED}Next Step:{RESET} Fix failed tests and re-run")

    print()

    sys.exit(0 if can_proceed else 1)
```

**Run the verification**:
```bash
python scripts/test_setup.py
```

**Expected Output**:
```
============================================================
PHASE 0 SETUP VERIFICATION
============================================================

[Python Version]
✅ Python 3.11.5

[ADK Import]
✅ ADK imports successfully

[Gemini API]
✅ Gemini API working

[Firestore]
✅ Firestore read/write working

[Project Structure]
✅ src/agents exists
✅ src/tools exists
✅ src/pipelines exists
✅ src/storage exists
✅ tests/unit exists
✅ docs exists

[PDF Processing]
✅ PyMuPDF (PDF processing) available

[Environment File]
✅ .env file configured

============================================================
SUMMARY
============================================================

Tests Passed: 7/7

GO/NO-GO DECISION:
------------------------------------------------------------
✅ GO - All tests passed
Ready to proceed to Phase 1.1

============================================================

Next Step: Run 'python scripts/phase_1_start.py'
```

**✅ Checkpoint 7**: All verification tests pass

---

## Verification Tests

### Quick Verification Checklist

Run these commands to verify everything works:

```bash
# 1. Check Python and packages
python -c "from google.adk import LlmAgent; print('ADK OK')"
python -c "import google.generativeai; print('Gemini OK')"
python -c "from google.cloud import firestore; print('Firestore OK')"

# 2. Run full verification
python scripts/test_setup.py

# 3. Check GCP setup
gcloud config get-value project
gcloud services list --enabled | grep -E 'run|firestore|pubsub'

# 4. Test Firestore connection
python test_firestore.py

# 5. Test Gemini API
python test_gemini.py

# 6. Test ADK agent
python test_adk_agent.py
```

### Success Criteria Table

| Check | Level | Command | Pass Criteria |
|-------|-------|---------|---------------|
| Python 3.9+ | 1 | `python --version` | ≥ 3.9 |
| ADK installs | 1 | `pip show google-adk` | Installed |
| ADK imports | 1 | `python -c "from google.adk import LlmAgent"` | No errors |
| Gemini API key set | 1 | `echo $GOOGLE_API_KEY` | Has value |
| Gemini API works | 1 | `python test_gemini.py` | Returns response |
| GCP project exists | 1 | `gcloud projects describe $PROJECT_ID` | Project details shown |
| Firestore created | 1 | `gcloud firestore databases list` | Database listed |
| Firestore read/write | 1 | `python test_firestore.py` | Success message |
| Service account key | 1 | `ls ~/research-intel-key.json` | File exists |
| Project structure | 1 | `ls src/agents` | Directory exists |
| ADK agent runs | 1 | `python test_adk_agent.py` | Agent executes |
| PDF library | 2 | `python -c "import fitz"` | No errors |
| .env file | 2 | `cat .env` | Contains keys |

---

## Troubleshooting

### Issue: ADK Installation Fails

**Symptoms**:
```
ERROR: Could not find a version that satisfies the requirement google-adk
```

**Solutions**:

1. **Check Python version**:
   ```bash
   python --version  # Must be 3.9+
   ```

2. **Update pip**:
   ```bash
   pip install --upgrade pip
   ```

3. **Try alternative package name**:
   ```bash
   # ADK might be under different name
   pip install google-gen-ai-adk
   # OR
   pip install google-ai-adk
   ```

4. **Install from source** (last resort):
   ```bash
   pip install git+https://github.com/google/adk.git
   ```

---

### Issue: Gemini API Key Not Working

**Symptoms**:
```
google.api_core.exceptions.PermissionDenied: 403 API key not valid
```

**Solutions**:

1. **Regenerate API key**:
   - Go to https://aistudio.google.com/app/apikey
   - Delete old key
   - Create new key
   - Copy and paste into `.env`

2. **Check API key format**:
   - Should start with `AIza`
   - No spaces or newlines
   - In `.env`: `GOOGLE_API_KEY=AIzaSy...` (no quotes)

3. **Verify API is enabled**:
   ```bash
   gcloud services enable generativelanguage.googleapis.com
   ```

---

### Issue: Firestore Permission Denied

**Symptoms**:
```
google.api_core.exceptions.PermissionDenied: 403 Missing or insufficient permissions
```

**Solutions**:

1. **Check service account roles**:
   ```bash
   gcloud projects get-iam-policy $PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:research-intel-sa@*"
   ```

2. **Re-grant roles**:
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:research-intel-sa@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/datastore.user"
   ```

3. **Check credentials file path**:
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ls -l $GOOGLE_APPLICATION_CREDENTIALS
   ```

4. **Use default credentials** (alternative):
   ```bash
   gcloud auth application-default login
   ```

---

### Issue: Firestore Database Already Exists

**Symptoms**:
```
ERROR: Database already exists in Datastore mode
```

**Solutions**:

This means your project has an old Datastore database. You have two options:

**Option A: Use existing Firestore** (recommended):
```bash
# Check if it's in Native mode
gcloud firestore databases describe --database='(default)'

# If it says "FIRESTORE_NATIVE", you're good to go
# If it says "DATASTORE_MODE", you need Option B
```

**Option B: Create new GCP project**:
```bash
# It's easier to start fresh than migrate
# Create new project in Cloud Console
# Repeat Task 2 with new project ID
```

---

### Issue: "Module not found" Errors

**Symptoms**:
```
ModuleNotFoundError: No module named 'google.adk'
```

**Solutions**:

1. **Check virtual environment is activated**:
   ```bash
   which python  # Should show path to venv/bin/python
   ```

2. **Reinstall in venv**:
   ```bash
   deactivate
   source venv/bin/activate
   pip install google-adk
   ```

3. **Check Python path**:
   ```python
   import sys
   print(sys.path)  # Should include venv site-packages
   ```

---

### Issue: Slow Installation

**Symptoms**:
Pip taking >10 minutes to install packages

**Solutions**:

1. **Use faster mirror**:
   ```bash
   pip install --index-url https://pypi.org/simple google-adk
   ```

2. **Install without dependencies first**:
   ```bash
   pip install --no-deps google-adk
   # Then install dependencies separately
   ```

3. **Use pre-built wheels**:
   ```bash
   pip install --only-binary :all: google-adk
   ```

---

## Go/No-Go Decision

### Decision Criteria

```python
def phase_0_complete():
    """
    Determine if Phase 0 is complete and can proceed to Phase 1

    Returns:
        tuple: (can_proceed: bool, reason: str)
    """

    # Level 1 Checks (Blockers)
    level_1 = {
        'adk_imports': test_adk_import(),
        'gemini_api': test_gemini_api(),
        'firestore': test_firestore_connection(),
        'project_structure': test_project_structure()
    }

    # Level 2 Checks (Important but not blocking)
    level_2 = {
        'pdf_processing': test_pdf_processing(),
        'env_file': test_env_file()
    }

    # Must pass all Level 1
    level_1_pass = all(level_1.values())
    level_2_pass = all(level_2.values())

    if not level_1_pass:
        failed = [k for k, v in level_1.items() if not v]
        return False, f"BLOCKED by: {', '.join(failed)}"

    if not level_2_pass:
        failed = [k for k, v in level_2.items() if not v]
        print(f"⚠️  WARNING: {', '.join(failed)} not working")
        print("Can proceed but some features may fail")

    return True, "Phase 0 complete, ready for Phase 1"
```

### Decision Matrix

| Scenario | Level 1 | Level 2 | Decision | Action |
|----------|---------|---------|----------|--------|
| All pass | ✅ | ✅ | **GO** | Proceed to Phase 1.1 |
| L1 pass, L2 fail | ✅ | ❌ | **CONDITIONAL GO** | Proceed, fix L2 later |
| L1 fail, L2 pass | ❌ | ✅ | **NO-GO** | Fix L1 blockers |
| All fail | ❌ | ❌ | **NO-GO** | Retry setup from scratch |

### Time Budget Check

```python
def check_time_budget(hours_spent: float) -> str:
    """
    Check if still within time budget

    Args:
        hours_spent: Hours spent on Phase 0

    Returns:
        str: Recommendation
    """
    if hours_spent <= 2:
        return "✅ On track"
    elif hours_spent <= 3:
        return "⚠️  At time cap, proceed to Phase 1"
    else:
        return "🚨 Over budget! Proceed anyway or ask for help"
```

**Hard Cap**: 3 hours
- If you've spent >3 hours and still have blockers, consider:
  1. Using mock/local versions (skip GCP for now)
  2. Asking for help in Discord/Slack
  3. Starting Phase 1 with local-only setup

---

## Final Checklist

Before proceeding to Phase 1, verify:

- [ ] Virtual environment activated
- [ ] ADK imports successfully
- [ ] Gemini API returns responses
- [ ] Firestore read/write works
- [ ] GCP project configured
- [ ] Service account key downloaded
- [ ] Project structure created
- [ ] `.env` file configured
- [ ] `test_setup.py` passes all Level 1 tests
- [ ] Time spent ≤ 3 hours

### Generate Phase 0 Report

```bash
# Run this to generate a report
python scripts/test_setup.py > phase_0_report.txt
cat phase_0_report.txt
```

### Commit Phase 0 Completion

```bash
# Initialize git repo
git init
git add .
git commit -m "feat: Phase 0 complete - development environment ready

✅ ADK installed and working
✅ GCP project configured
✅ Firestore database created
✅ Gemini API tested
✅ Project structure created
✅ All verification tests pass

Ready to proceed to Phase 1.1: Basic PDF Ingestion"

# Tag the commit
git tag v0.0.1-phase0-complete
```

---

## Next Steps

**If Phase 0 Complete**:
```bash
# Proceed to Phase 1.1
python scripts/phase_1_start.py
```

**If Phase 0 Blocked**:
1. Review failed tests in output
2. Check troubleshooting section
3. Fix issues
4. Re-run `python scripts/test_setup.py`
5. Repeat until all Level 1 tests pass

---

## Estimated Time Breakdown

| Task | Estimated | Actual | Notes |
|------|-----------|--------|-------|
| Python environment | 15 min | ___ | |
| GCP project setup | 20 min | ___ | |
| Firestore database | 10 min | ___ | |
| Gemini API setup | 10 min | ___ | |
| ADK agent test | 15 min | ___ | |
| Project structure | 20 min | ___ | |
| Verification script | 15 min | ___ | |
| Troubleshooting buffer | 30 min | ___ | |
| **Total** | **2h 15m** | ___ | Hard cap: 3h |

---

## Quick Reference Commands

```bash
# Activate environment
source venv/bin/activate

# Test everything
python scripts/test_setup.py

# Check GCP project
gcloud config get-value project

# List enabled APIs
gcloud services list --enabled

# Test Firestore
python test_firestore.py

# Test Gemini
python test_gemini.py

# Test ADK
python test_adk_agent.py

# Deactivate environment
deactivate
```

---

## Summary

Phase 0 sets up your development environment. By the end:

✅ **You can run ADK agents locally**
✅ **You can call Gemini API**
✅ **You can read/write to Firestore**
✅ **Your project structure is ready**
✅ **All tools are verified working**

**Time Investment**: 2-3 hours now saves 6-8 hours of frustration later.

**Go/No-Go**: Must pass all Level 1 tests to proceed to Phase 1.

**Next**: [IMPLEMENTATION_PLAN.md - Phase 1.1: Basic PDF Ingestion](IMPLEMENTATION_PLAN.md#sub-phase-11-basic-pdf-ingestion-morning-4-hours)
