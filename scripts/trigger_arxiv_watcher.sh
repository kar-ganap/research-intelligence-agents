#!/bin/bash
#
# Trigger ArXiv Watcher Job - Manual Execution for Testing
#
# This script manually triggers the Cloud Run Job and shows execution logs
#

set -e

PROJECT_ID="research-intel-agents"
REGION="us-central1"
JOB_NAME="arxiv-watcher"

echo "================================================================"
echo "Triggering ArXiv Watcher Job"
echo "================================================================"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Job: $JOB_NAME"
echo ""
echo "Note: This will fetch papers from the last 24 hours"
echo "      and publish them to Pub/Sub for processing"
echo ""
echo "================================================================"
echo ""

# Check if job exists
echo "→ Checking if job exists..."
if ! gcloud run jobs describe $JOB_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="value(metadata.name)" &> /dev/null; then
    echo "❌ Job '$JOB_NAME' not found. Please deploy it first."
    exit 1
fi

echo "✓ Job found"
echo ""

# Execute the job
echo "→ Executing job..."
EXECUTION_NAME=$(gcloud run jobs execute $JOB_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="value(metadata.name)" \
  --wait)

echo ""
echo "================================================================"
echo "Execution started: $EXECUTION_NAME"
echo "================================================================"
echo ""

# Get execution status
echo "→ Getting execution status..."
gcloud run jobs executions describe $EXECUTION_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="table(
    metadata.name,
    status.conditions[0].type,
    status.conditions[0].status,
    status.startTime,
    status.completionTime
  )"

echo ""
echo "→ Fetching logs..."
echo ""

# Get logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME AND resource.labels.location=$REGION AND labels.execution_name=$EXECUTION_NAME" \
  --project $PROJECT_ID \
  --limit 100 \
  --format "value(textPayload)" \
  --freshness 10m

echo ""
echo "================================================================"
echo "✅ Job execution complete!"
echo "================================================================"
