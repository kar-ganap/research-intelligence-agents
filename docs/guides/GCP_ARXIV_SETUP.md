# GCP Project & arXiv API Setup Guide

This guide walks you through setting up your Google Cloud Project and testing the arXiv API for the Research Intelligence Platform.

---

## 🎯 Overview

You need to:
1. Create a new GCP project for this hackathon
2. Enable required Google Cloud APIs
3. Set up Firestore database
4. Create Cloud Storage buckets
5. Configure Pub/Sub topics
6. Test arXiv API connectivity
7. Update your `.env` file

---

## Part 1: Create GCP Project

### Step 1: Create Project

```bash
# Set your desired project ID (must be globally unique)
export PROJECT_ID="research-intelligence-$(date +%s)"

# Create the project
gcloud projects create $PROJECT_ID --name="Research Intelligence Platform"

# Set as active project
gcloud config set project $PROJECT_ID

# Link billing account (required for Cloud Run)
# List your billing accounts
gcloud billing accounts list

# Link billing (replace BILLING_ACCOUNT_ID with your account)
gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### Step 2: Enable Required APIs

```bash
# Enable all required Google Cloud APIs
gcloud services enable \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

This will take 2-3 minutes to complete.

---

## Part 2: Set Up Firestore

### Create Firestore Database

```bash
# Create Firestore database in Native mode
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native

# Verify creation
gcloud firestore databases list
```

### Create Initial Collections

The collections will be created automatically when you first write to them, but here's the schema we'll use:

- `papers` - Research papers with metadata
- `relationships` - Graph edges between papers
- `watch_rules` - User alert preferences
- `alerts` - Generated notifications
- `users` - User profiles

---

## Part 3: Set Up Cloud Storage

### Create Buckets

```bash
# Set project ID variable if not already set
export PROJECT_ID=$(gcloud config get-value project)

# Create bucket for PDFs
gsutil mb -l us-central1 gs://${PROJECT_ID}-pdfs

# Create bucket for cache
gsutil mb -l us-central1 gs://${PROJECT_ID}-cache

# Verify buckets
gsutil ls
```

### Set Bucket Permissions

```bash
# Make buckets private (default, but explicit)
gsutil iam ch allUsers:objectViewer gs://${PROJECT_ID}-pdfs
gsutil iam ch allUsers:objectViewer gs://${PROJECT_ID}-cache
```

---

## Part 4: Set Up Pub/Sub Topics

### Create Topics

```bash
# Create topics for event-driven architecture
gcloud pubsub topics create arxiv.candidates
gcloud pubsub topics create docs.ready
gcloud pubsub topics create arxiv.matches

# Create subscriptions
gcloud pubsub subscriptions create arxiv-candidates-sub \
  --topic=arxiv.candidates

gcloud pubsub subscriptions create docs-ready-sub \
  --topic=docs.ready

gcloud pubsub subscriptions create arxiv-matches-sub \
  --topic=arxiv.matches

# Verify
gcloud pubsub topics list
gcloud pubsub subscriptions list
```

---

## Part 5: Create Service Account

### Generate Credentials

```bash
# Create service account
gcloud iam service-accounts create research-intelligence \
  --display-name="Research Intelligence Platform Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:research-intelligence@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:research-intelligence@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:research-intelligence@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:research-intelligence@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/pubsub.editor"

# Download key file
gcloud iam service-accounts keys create credentials.json \
  --iam-account=research-intelligence@${PROJECT_ID}.iam.gserviceaccount.com

# Move to project root (don't commit this!)
mv credentials.json ../../../credentials.json
```

---

## Part 6: Test arXiv API

### Install arXiv Package

```bash
# Add arxiv package to dependencies
uv pip install arxiv
```

### Test Script

Create `scripts/test_arxiv.py`:

```python
#!/usr/bin/env python3
"""Test arXiv API connectivity and basic functionality."""

import arxiv

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def test_arxiv_search():
    """Test basic arXiv search."""
    print(f"{BLUE}Testing arXiv API...{RESET}\n")

    try:
        # Search for recent ML papers
        search = arxiv.Search(
            query="cat:cs.AI",
            max_results=5,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        results = list(search.results())

        print(f"{GREEN}✅ arXiv API Working!{RESET}\n")
        print(f"Found {len(results)} recent papers:\n")

        for i, paper in enumerate(results, 1):
            print(f"{i}. {paper.title}")
            print(f"   Authors: {', '.join([a.name for a in paper.authors[:3]])}")
            print(f"   Published: {paper.published.strftime('%Y-%m-%d')}")
            print(f"   PDF: {paper.pdf_url}")
            print()

        return True

    except Exception as e:
        print(f"{RED}❌ arXiv API Failed: {e}{RESET}")
        return False

def test_arxiv_download():
    """Test PDF download capability."""
    print(f"{BLUE}Testing PDF download...{RESET}\n")

    try:
        # Get one paper
        search = arxiv.Search(
            query="cat:cs.AI",
            max_results=1
        )

        paper = next(search.results())

        # Download to temp location
        paper.download_pdf(dirpath="/tmp", filename="test_paper.pdf")

        print(f"{GREEN}✅ PDF Download Working!{RESET}")
        print(f"Downloaded: {paper.title}")
        print(f"Location: /tmp/test_paper.pdf\n")

        return True

    except Exception as e:
        print(f"{RED}❌ PDF Download Failed: {e}{RESET}")
        return False

if __name__ == "__main__":
    print(f"\n{'=' * 70}")
    print(f"{'arXiv API Test Suite'.center(70)}")
    print(f"{'=' * 70}\n")

    test1 = test_arxiv_search()
    test2 = test_arxiv_download()

    print(f"{'=' * 70}")
    if test1 and test2:
        print(f"{GREEN}✅ All arXiv tests passed!{RESET}")
    else:
        print(f"{RED}❌ Some arXiv tests failed{RESET}")
    print(f"{'=' * 70}\n")
```

### Run Test

```bash
chmod +x scripts/test_arxiv.py
uv run python scripts/test_arxiv.py
```

---

## Part 7: Update .env File

### Configure Your Environment

```bash
# Get your project ID
export PROJECT_ID=$(gcloud config get-value project)

# Update .env file with actual values
cat > .env << EOF
# GCP Configuration
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/credentials.json
GCP_REGION=us-central1

# API Keys
GOOGLE_API_KEY=$(gcloud auth application-default print-access-token)
GEMINI_API_KEY=your-gemini-api-key-from-ai-studio

# Firestore
FIRESTORE_DATABASE=(default)

# Cloud Storage
GCS_BUCKET_PDFS=${PROJECT_ID}-pdfs
GCS_BUCKET_CACHE=${PROJECT_ID}-cache

# Pub/Sub Topics
PUBSUB_TOPIC_CANDIDATES=arxiv.candidates
PUBSUB_TOPIC_READY=docs.ready
PUBSUB_TOPIC_MATCHES=arxiv.matches

# Feature Flags
ENABLE_GRAPH_VISUALIZATION=false
ENABLE_PROACTIVE_ALERTS=false
ENABLE_CONTRADICTION_DETECTION=false
ENABLE_CONFIDENCE_SCORING=false

# Environment
ENV=development
LOG_LEVEL=INFO
DEBUG=true

# Agent Configuration
DEFAULT_MODEL=gemini-2.0-flash-exp
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=2048
DEFAULT_TIMEOUT=30
EOF
```

---

## Part 8: Verify Complete Setup

### Run Full Verification

```bash
# Re-run setup test
uv run python scripts/test_setup.py

# Run arXiv test
uv run python scripts/test_arxiv.py

# Test Firestore connection
python -c "
from google.cloud import firestore
import os
db = firestore.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
print('✅ Firestore connected!')
print(f'Project: {os.getenv(\"GOOGLE_CLOUD_PROJECT\")}')"
```

---

## 📊 Verification Checklist

After completing this guide, verify:

- [ ] GCP project created and billing enabled
- [ ] All APIs enabled (7+ services)
- [ ] Firestore database created in `us-central1`
- [ ] Cloud Storage buckets created (2 buckets)
- [ ] Pub/Sub topics and subscriptions created (3 each)
- [ ] Service account created with credentials downloaded
- [ ] arXiv API tested and working
- [ ] `.env` file updated with real values
- [ ] All verification scripts pass

---

## 🎯 Success Criteria

You're ready for Phase 1 when:

✅ `python scripts/test_setup.py` shows all critical tests passing
✅ `python scripts/test_arxiv.py` successfully fetches papers
✅ Firestore connection test succeeds
✅ GCS buckets exist and are accessible
✅ Pub/Sub topics are created

---

## 💰 Cost Management

To avoid unexpected charges:

```bash
# Set budget alert
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Research Intelligence Budget" \
  --budget-amount=50 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90

# Monitor costs
gcloud billing budgets list --billing-account=BILLING_ACCOUNT_ID
```

---

## 🔧 Troubleshooting

### Issue: APIs not enabled

```bash
# Check which APIs are enabled
gcloud services list --enabled

# Enable specific API
gcloud services enable SERVICE_NAME.googleapis.com
```

### Issue: Firestore creation fails

```bash
# Check if Firestore already exists
gcloud firestore databases list

# If exists in Datastore mode, you need to create new project
```

### Issue: Permission denied

```bash
# Check your permissions
gcloud projects get-iam-policy $PROJECT_ID

# Grant yourself Owner role if needed
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/owner"
```

---

## 📚 Resources

- [GCP Console](https://console.cloud.google.com)
- [Firestore Docs](https://cloud.google.com/firestore/docs)
- [arXiv API Guide](https://info.arxiv.org/help/api/index.html)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

---

**Next Step**: After completing this setup, proceed to Phase 1 implementation!
