#!/bin/bash
#
# Master Deployment Script for Research Intelligence Platform
#
# Deploys all components to Google Cloud Run:
# - 4 Services (API Gateway, Orchestrator, Graph Service, Frontend)
# - 3 Jobs (ArXiv Watcher, Intake Pipeline, Graph Updater)
# - 1 Worker (Alert Worker)
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-""}
REGION=${REGION:-"us-central1"}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}ERROR: GOOGLE_CLOUD_PROJECT environment variable not set${NC}"
    echo "Usage: GOOGLE_CLOUD_PROJECT=your-project-id bash scripts/deploy_all.sh"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Research Intelligence Platform${NC}"
echo -e "${BLUE}  Full Cloud Run Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Project ID: ${GREEN}$PROJECT_ID${NC}"
echo -e "Region: ${GREEN}$REGION${NC}"
echo ""

# Step 1: Setup Pub/Sub
echo -e "${BLUE}[Step 1/4] Setting up Pub/Sub...${NC}"
bash scripts/setup_pubsub.sh
echo -e "${GREEN}✅ Pub/Sub setup complete${NC}"
echo ""

# Step 2: Deploy Services
echo -e "${BLUE}[Step 2/4] Deploying Cloud Run Services...${NC}"
bash scripts/deploy_services.sh
echo -e "${GREEN}✅ Services deployed${NC}"
echo ""

# Step 3: Deploy Jobs and Worker
echo -e "${BLUE}[Step 3/4] Deploying Cloud Run Jobs and Worker...${NC}"
bash scripts/deploy_jobs.sh
echo -e "${GREEN}✅ Jobs and Worker deployed${NC}"
echo ""

# Step 4: Setup Cloud Scheduler
echo -e "${BLUE}[Step 4/4] Setting up Cloud Scheduler...${NC}"
bash scripts/setup_scheduler.sh
echo -e "${GREEN}✅ Cloud Scheduler configured${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Services deployed:"
echo "  1. API Gateway      - Entry point for all requests"
echo "  2. Orchestrator     - Multi-agent ADK coordination"
echo "  3. Graph Service    - Knowledge graph queries"
echo "  4. Frontend         - Web UI"
echo ""
echo "Jobs deployed:"
echo "  1. ArXiv Watcher    - Daily paper fetching (scheduled)"
echo "  2. Intake Pipeline  - Parallel paper processing"
echo "  3. Graph Updater    - Batch relationship detection (scheduled)"
echo ""
echo "Worker deployed:"
echo "  1. Alert Worker     - Pub/Sub notification consumer"
echo ""
echo "To get service URLs:"
echo "  gcloud run services list --platform managed --region $REGION"
echo ""
echo "To view logs:"
echo "  gcloud run services logs read api-gateway --region $REGION"
echo ""
