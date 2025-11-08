#!/bin/bash
set -e

echo "========================================="
echo "Converting Pub/Sub Subscriptions to PUSH"
echo "========================================="
echo ""

# Configuration
PROJECT_ID="research-intel-agents"
REGION="us-central1"

# Get service URLs
echo "Fetching service URLs..."
INTAKE_URL=$(gcloud run services describe intake-pipeline \
    --region $REGION \
    --project $PROJECT_ID \
    --format='value(status.url)' 2>/dev/null || echo "")

GRAPH_UPDATER_URL=$(gcloud run services describe graph-updater \
    --region $REGION \
    --project $PROJECT_ID \
    --format='value(status.url)' 2>/dev/null || echo "")

if [ -z "$INTAKE_URL" ]; then
    echo "ERROR: intake-pipeline service not found. Deploy it first."
    exit 1
fi

if [ -z "$GRAPH_UPDATER_URL" ]; then
    echo "ERROR: graph-updater service not found. Deploy it first."
    exit 1
fi

echo "Intake Pipeline URL: $INTAKE_URL"
echo "Graph Updater URL: $GRAPH_UPDATER_URL"
echo ""

# Convert arxiv-candidates-sub to PUSH
echo "========================================="
echo "Converting arxiv-candidates-sub to PUSH"
echo "========================================="

# Delete existing subscription
echo "Deleting existing PULL subscription: arxiv-candidates-sub"
gcloud pubsub subscriptions delete arxiv-candidates-sub \
    --project=$PROJECT_ID \
    --quiet || echo "Subscription not found, creating new one..."

# Create new PUSH subscription
echo "Creating PUSH subscription: arxiv-candidates-sub"
gcloud pubsub subscriptions create arxiv-candidates-sub \
    --topic=arxiv.candidates \
    --push-endpoint="$INTAKE_URL/" \
    --project=$PROJECT_ID \
    --ack-deadline=600 \
    --min-retry-delay=10s \
    --max-retry-delay=600s

echo "✅ arxiv-candidates-sub converted to PUSH"
echo ""

# Convert docs-ready-sub to PUSH
echo "========================================="
echo "Converting docs-ready-sub to PUSH"
echo "========================================="

# Delete existing subscription
echo "Deleting existing PULL subscription: docs-ready-sub"
gcloud pubsub subscriptions delete docs-ready-sub \
    --project=$PROJECT_ID \
    --quiet || echo "Subscription not found, creating new one..."

# Create new PUSH subscription
echo "Creating PUSH subscription: docs-ready-sub"
gcloud pubsub subscriptions create docs-ready-sub \
    --topic=docs.ready \
    --push-endpoint="$GRAPH_UPDATER_URL/" \
    --project=$PROJECT_ID \
    --ack-deadline=600 \
    --min-retry-delay=10s \
    --max-retry-delay=600s

echo "✅ docs-ready-sub converted to PUSH"
echo ""

# Summary
echo "========================================="
echo "Conversion Complete"
echo "========================================="
echo ""
echo "PUSH Subscriptions:"
echo "  arxiv-candidates-sub → $INTAKE_URL/"
echo "  docs-ready-sub → $GRAPH_UPDATER_URL/"
echo ""
echo "Pipeline flow:"
echo "  arxiv-watcher → arxiv.candidates → intake-pipeline"
echo "                                    ↓"
echo "                                  docs.ready → graph-updater"
echo ""
