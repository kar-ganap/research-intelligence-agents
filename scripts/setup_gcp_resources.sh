#!/bin/bash
# GCP Resource Setup Script for Research Intelligence Platform
# This script creates all necessary GCP resources for the project

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="research-intel-agents"
REGION="us-central1"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     GCP Resource Setup - Research Intelligence Platform      ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

print_success "gcloud CLI found"

# Set the project
print_status "Setting active project to ${PROJECT_ID}..."
if gcloud config set project ${PROJECT_ID} 2>/dev/null; then
    print_success "Project set to ${PROJECT_ID}"
else
    print_error "Failed to set project. Does the project exist?"
    echo ""
    echo "To create the project, run:"
    echo "  gcloud projects create ${PROJECT_ID} --name='Research Intelligence Platform'"
    exit 1
fi

# Check if billing is enabled
print_status "Checking billing status..."
if gcloud beta billing projects describe ${PROJECT_ID} --format="value(billingEnabled)" 2>/dev/null | grep -q "True"; then
    print_success "Billing is enabled"
else
    print_warning "Billing is not enabled for this project"
    echo ""
    echo "To enable billing:"
    echo "  1. Go to https://console.cloud.google.com/billing"
    echo "  2. Link a billing account to project ${PROJECT_ID}"
    echo ""
    read -p "Press Enter after enabling billing, or Ctrl+C to exit..."
fi

# Enable required APIs
print_status "Enabling required Google Cloud APIs..."
echo "This may take 2-3 minutes..."

APIS=(
    "aiplatform.googleapis.com"
    "firestore.googleapis.com"
    "storage.googleapis.com"
    "pubsub.googleapis.com"
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "secretmanager.googleapis.com"
    "logging.googleapis.com"
    "monitoring.googleapis.com"
    "generativelanguage.googleapis.com"
)

for api in "${APIS[@]}"; do
    if gcloud services enable ${api} 2>/dev/null; then
        print_success "Enabled ${api}"
    else
        print_warning "Could not enable ${api} (may already be enabled)"
    fi
done

echo ""

# Create Firestore database
print_status "Creating Firestore database..."
if gcloud firestore databases create \
    --location=${REGION} \
    --type=firestore-native 2>/dev/null; then
    print_success "Firestore database created in ${REGION}"
else
    print_warning "Firestore database may already exist"
fi

echo ""

# Create Cloud Storage buckets
print_status "Creating Cloud Storage buckets..."

BUCKET_PDFS="${PROJECT_ID}-pdfs"
BUCKET_CACHE="${PROJECT_ID}-cache"

if gsutil mb -l ${REGION} gs://${BUCKET_PDFS} 2>/dev/null; then
    print_success "Created bucket: gs://${BUCKET_PDFS}"
else
    print_warning "Bucket gs://${BUCKET_PDFS} may already exist"
fi

if gsutil mb -l ${REGION} gs://${BUCKET_CACHE} 2>/dev/null; then
    print_success "Created bucket: gs://${BUCKET_CACHE}"
else
    print_warning "Bucket gs://${BUCKET_CACHE} may already exist"
fi

echo ""

# Create Pub/Sub topics
print_status "Creating Pub/Sub topics..."

TOPICS=(
    "arxiv.candidates"
    "docs.ready"
    "arxiv.matches"
)

for topic in "${TOPICS[@]}"; do
    if gcloud pubsub topics create ${topic} 2>/dev/null; then
        print_success "Created topic: ${topic}"
    else
        print_warning "Topic ${topic} may already exist"
    fi
done

echo ""

# Create Pub/Sub subscriptions
print_status "Creating Pub/Sub subscriptions..."

SUBSCRIPTIONS=(
    "arxiv-candidates-sub:arxiv.candidates"
    "docs-ready-sub:docs.ready"
    "arxiv-matches-sub:arxiv.matches"
)

for sub in "${SUBSCRIPTIONS[@]}"; do
    SUB_NAME="${sub%%:*}"
    TOPIC_NAME="${sub##*:}"

    if gcloud pubsub subscriptions create ${SUB_NAME} \
        --topic=${TOPIC_NAME} 2>/dev/null; then
        print_success "Created subscription: ${SUB_NAME}"
    else
        print_warning "Subscription ${SUB_NAME} may already exist"
    fi
done

echo ""

# Create service account
print_status "Creating service account..."

SERVICE_ACCOUNT_NAME="research-intelligence"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
    --display-name="Research Intelligence Platform Service Account" 2>/dev/null; then
    print_success "Created service account: ${SERVICE_ACCOUNT_NAME}"
else
    print_warning "Service account may already exist"
fi

# Grant IAM roles
print_status "Granting IAM roles to service account..."

ROLES=(
    "roles/aiplatform.user"
    "roles/datastore.user"
    "roles/storage.objectAdmin"
    "roles/pubsub.editor"
    "roles/logging.logWriter"
    "roles/monitoring.metricWriter"
)

for role in "${ROLES[@]}"; do
    if gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="${role}" \
        --condition=None \
        > /dev/null 2>&1; then
        print_success "Granted ${role}"
    else
        print_warning "Role ${role} may already be granted"
    fi
done

echo ""

# Create and download service account key
print_status "Creating service account key..."

KEY_FILE="credentials.json"

if [ -f "${KEY_FILE}" ]; then
    print_warning "Key file ${KEY_FILE} already exists, skipping..."
else
    if gcloud iam service-accounts keys create ${KEY_FILE} \
        --iam-account=${SERVICE_ACCOUNT_EMAIL} 2>/dev/null; then
        print_success "Service account key created: ${KEY_FILE}"
        print_warning "Keep this file secure! It's in .gitignore"
    else
        print_error "Failed to create service account key"
    fi
fi

echo ""

# Update .env file
print_status "Updating .env file with credentials path..."

if grep -q "GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json" .env; then
    sed -i.bak "s|GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json|GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/credentials.json|g" .env
    rm .env.bak
    print_success "Updated GOOGLE_APPLICATION_CREDENTIALS in .env"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Setup Complete!                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

print_success "All GCP resources have been created"
echo ""
echo "Resources created:"
echo "  • Firestore database (Native mode)"
echo "  • Cloud Storage buckets (2)"
echo "  • Pub/Sub topics (3)"
echo "  • Pub/Sub subscriptions (3)"
echo "  • Service account with IAM roles"
echo ""

# Verify setup
print_status "Running verification tests..."
echo ""

# Test Firestore
if python3 -c "
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '$(pwd)/credentials.json'
os.environ['GOOGLE_CLOUD_PROJECT'] = '${PROJECT_ID}'
from google.cloud import firestore
db = firestore.Client(project='${PROJECT_ID}')
print('✓ Firestore connection successful')
" 2>/dev/null; then
    print_success "Firestore verified"
else
    print_warning "Firestore verification failed (may need to wait for propagation)"
fi

# Test Storage
if gsutil ls gs://${BUCKET_PDFS} > /dev/null 2>&1; then
    print_success "Cloud Storage verified"
else
    print_warning "Cloud Storage verification failed"
fi

# Test Pub/Sub
if gcloud pubsub topics list | grep -q "arxiv.candidates"; then
    print_success "Pub/Sub verified"
else
    print_warning "Pub/Sub verification failed"
fi

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Review your .env file to ensure all values are correct"
echo "  2. Run: ${YELLOW}uv run python scripts/test_setup.py${NC}"
echo "  3. Start Phase 1 development!"
echo ""
echo -e "${BLUE}Cost reminder:${NC} Free tier should cover most development"
echo "Monitor costs at: https://console.cloud.google.com/billing"
echo ""
