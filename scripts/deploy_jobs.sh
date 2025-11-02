#!/bin/bash
#
# Deploy Cloud Run Jobs and Worker
# - ArXiv Watcher Job
# - Intake Pipeline Job
# - Graph Updater Job
# - Alert Worker
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-""}
REGION=${REGION:-"us-central1"}

echo -e "${BLUE}Deploying Cloud Run Jobs and Worker...${NC}\n"

# Deploy ArXiv Watcher Job
echo -e "${BLUE}[1/4] Deploying ArXiv Watcher Job...${NC}"
gcloud run jobs deploy arxiv-watcher \
  --source ./src/jobs/arxiv_watcher \
  --region $REGION \
  --memory 512Mi \
  --cpu 1 \
  --max-retries 3 \
  --task-timeout 600 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,PUBSUB_TOPIC=arxiv-candidates \
  --project $PROJECT_ID

echo -e "${GREEN}✅ ArXiv Watcher Job deployed${NC}\n"

# Deploy Intake Pipeline Job
echo -e "${BLUE}[2/4] Deploying Intake Pipeline Job...${NC}"
gcloud run jobs deploy intake-pipeline \
  --source ./src/jobs/intake_pipeline \
  --region $REGION \
  --memory 2Gi \
  --cpu 2 \
  --max-retries 1 \
  --task-timeout 1800 \
  --parallelism 5 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,PUBSUB_SUBSCRIPTION=arxiv-candidates-sub \
  --project $PROJECT_ID

echo -e "${GREEN}✅ Intake Pipeline Job deployed${NC}\n"

# Deploy Graph Updater Job
echo -e "${BLUE}[3/4] Deploying Graph Updater Job...${NC}"
gcloud run jobs deploy graph-updater \
  --source ./src/jobs/graph_updater \
  --region $REGION \
  --memory 1Gi \
  --cpu 1 \
  --max-retries 1 \
  --task-timeout 3600 \
  --parallelism 3 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,SKIP_EXISTING=true \
  --project $PROJECT_ID

echo -e "${GREEN}✅ Graph Updater Job deployed${NC}\n"

# Deploy Alert Worker
echo -e "${BLUE}[4/4] Deploying Alert Worker...${NC}"
gcloud run deploy alert-worker \
  --source ./src/workers/alert_worker \
  --platform managed \
  --region $REGION \
  --no-allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,PUBSUB_SUBSCRIPTION=arxiv-matches-sub \
  --project $PROJECT_ID

echo -e "${GREEN}✅ Alert Worker deployed${NC}\n"

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All jobs and worker deployed!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Jobs deployed:"
echo "  1. arxiv-watcher    - Fetches new papers from arXiv"
echo "  2. intake-pipeline  - Processes papers (5 parallel tasks)"
echo "  3. graph-updater    - Detects relationships (3 parallel tasks)"
echo ""
echo "Worker deployed:"
echo "  1. alert-worker     - Processes notification events"
echo ""
echo "To manually trigger a job:"
echo "  gcloud run jobs execute arxiv-watcher --region $REGION"
echo ""
echo "To view job executions:"
echo "  gcloud run jobs executions list --job arxiv-watcher --region $REGION"
echo ""
