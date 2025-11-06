#!/bin/bash
set -e

echo "========================================="
echo "Deploying Pipeline Services"
echo "========================================="
echo ""

# Configuration
PROJECT_ID="research-intel-agents"
REGION="us-central1"

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "ERROR: GOOGLE_API_KEY environment variable is not set"
    exit 1
fi

echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Deploy Intake Pipeline Service
echo "========================================="
echo "Deploying Intake Pipeline Service"
echo "========================================="

gcloud run deploy intake-pipeline \
    --source . \
    --region $REGION \
    --project $PROJECT_ID \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_API_KEY=$GOOGLE_API_KEY,DEFAULT_MODEL=gemini-2.5-pro" \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=600 \
    --memory=2Gi \
    --cpu=2

# Capture intake-pipeline URL
INTAKE_URL=$(gcloud run services describe intake-pipeline \
    --region $REGION \
    --project $PROJECT_ID \
    --format='value(status.url)')

echo ""
echo "Intake Pipeline Service deployed: $INTAKE_URL"
echo ""

# Deploy Graph Updater Service
echo "========================================="
echo "Deploying Graph Updater Service"
echo "========================================="

gcloud run deploy graph-updater \
    --source . \
    --region $REGION \
    --project $PROJECT_ID \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_API_KEY=$GOOGLE_API_KEY,DEFAULT_MODEL=gemini-2.5-pro" \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=1800 \
    --memory=2Gi \
    --cpu=2

# Capture graph-updater URL
GRAPH_UPDATER_URL=$(gcloud run services describe graph-updater \
    --region $REGION \
    --project $PROJECT_ID \
    --format='value(status.url)')

echo ""
echo "Graph Updater Service deployed: $GRAPH_UPDATER_URL"
echo ""

# Summary
echo "========================================="
echo "Deployment Complete"
echo "========================================="
echo "Intake Pipeline: $INTAKE_URL"
echo "Graph Updater: $GRAPH_UPDATER_URL"
echo ""
echo "Next steps:"
echo "1. Convert arxiv-candidates-sub to PUSH: $INTAKE_URL"
echo "2. Convert docs-ready-sub to PUSH: $GRAPH_UPDATER_URL"
echo ""
