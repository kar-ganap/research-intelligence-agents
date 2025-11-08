#!/bin/bash
#
# Setup Cloud Scheduler for recurring jobs
#
# Schedules:
# - ArXiv Watcher: Daily at 6am UTC
# - Graph Updater: Daily at 2am UTC
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-""}
REGION=${REGION:-"us-central1"}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}ERROR: GOOGLE_CLOUD_PROJECT environment variable not set${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Cloud Scheduler Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Project ID: ${GREEN}$PROJECT_ID${NC}"
echo -e "Region: ${GREEN}$REGION${NC}"
echo ""

# Enable Cloud Scheduler API
echo -e "${BLUE}Enabling Cloud Scheduler API...${NC}"
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID
echo -e "${GREEN}✅ Cloud Scheduler API enabled${NC}\n"

# Schedule 1: ArXiv Watcher (Daily at 6am UTC)
echo -e "${BLUE}[1/2] Creating schedule for ArXiv Watcher...${NC}"
if gcloud scheduler jobs describe arxiv-watcher-daily --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}  Schedule already exists, updating...${NC}"
    gcloud scheduler jobs update http arxiv-watcher-daily \
        --location=$REGION \
        --schedule="0 6 * * *" \
        --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/arxiv-watcher:run" \
        --http-method=POST \
        --oauth-service-account-email=$PROJECT_ID@appspot.gserviceaccount.com \
        --project=$PROJECT_ID
else
    gcloud scheduler jobs create http arxiv-watcher-daily \
        --location=$REGION \
        --schedule="0 6 * * *" \
        --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/arxiv-watcher:run" \
        --http-method=POST \
        --oauth-service-account-email=$PROJECT_ID@appspot.gserviceaccount.com \
        --project=$PROJECT_ID
fi
echo -e "${GREEN}✅ ArXiv Watcher scheduled: Daily at 6am UTC${NC}\n"

# Schedule 2: Graph Updater (Daily at 2am UTC)
echo -e "${BLUE}[2/2] Creating schedule for Graph Updater...${NC}"
if gcloud scheduler jobs describe graph-updater-daily --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}  Schedule already exists, updating...${NC}"
    gcloud scheduler jobs update http graph-updater-daily \
        --location=$REGION \
        --schedule="0 2 * * *" \
        --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/graph-updater:run" \
        --http-method=POST \
        --oauth-service-account-email=$PROJECT_ID@appspot.gserviceaccount.com \
        --project=$PROJECT_ID
else
    gcloud scheduler jobs create http graph-updater-daily \
        --location=$REGION \
        --schedule="0 2 * * *" \
        --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/graph-updater:run" \
        --http-method=POST \
        --oauth-service-account-email=$PROJECT_ID@appspot.gserviceaccount.com \
        --project=$PROJECT_ID
fi
echo -e "${GREEN}✅ Graph Updater scheduled: Daily at 2am UTC${NC}\n"

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Cloud Scheduler setup complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Scheduled jobs:"
echo "  1. arxiv-watcher-daily  → Runs daily at 6am UTC"
echo "  2. graph-updater-daily  → Runs daily at 2am UTC"
echo ""
echo "To view schedules:"
echo "  gcloud scheduler jobs list --location=$REGION"
echo ""
echo "To manually trigger:"
echo "  gcloud scheduler jobs run arxiv-watcher-daily --location=$REGION"
echo "  gcloud scheduler jobs run graph-updater-daily --location=$REGION"
echo ""
