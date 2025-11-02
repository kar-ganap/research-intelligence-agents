#!/bin/bash
#
# Setup Pub/Sub Topics and Subscriptions
#
# This script creates the Pub/Sub infrastructure needed for:
# - ArXiv Watcher → Intake Pipeline communication
# - Intake Pipeline → Alert Worker communication
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
    echo "Usage: GOOGLE_CLOUD_PROJECT=your-project-id bash scripts/setup_pubsub.sh"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Pub/Sub Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Project ID: ${GREEN}$PROJECT_ID${NC}"
echo -e "Region: ${GREEN}$REGION${NC}"
echo ""

# Topic 1: arxiv-candidates
# Published by: ArXiv Watcher Job
# Consumed by: Intake Pipeline Job
echo -e "${BLUE}Creating topic: arxiv-candidates${NC}"
if gcloud pubsub topics describe arxiv-candidates --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}  Topic already exists, skipping${NC}"
else
    gcloud pubsub topics create arxiv-candidates \
        --project=$PROJECT_ID
    echo -e "${GREEN}  ✅ Created topic: arxiv-candidates${NC}"
fi

echo -e "${BLUE}Creating subscription: arxiv-candidates-sub${NC}"
if gcloud pubsub subscriptions describe arxiv-candidates-sub --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}  Subscription already exists, skipping${NC}"
else
    gcloud pubsub subscriptions create arxiv-candidates-sub \
        --topic=arxiv-candidates \
        --ack-deadline=600 \
        --message-retention-duration=7d \
        --project=$PROJECT_ID
    echo -e "${GREEN}  ✅ Created subscription: arxiv-candidates-sub${NC}"
fi

echo ""

# Topic 2: arxiv-matches
# Published by: Intake Pipeline Job (via matching logic)
# Consumed by: Alert Worker
echo -e "${BLUE}Creating topic: arxiv-matches${NC}"
if gcloud pubsub topics describe arxiv-matches --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}  Topic already exists, skipping${NC}"
else
    gcloud pubsub topics create arxiv-matches \
        --project=$PROJECT_ID
    echo -e "${GREEN}  ✅ Created topic: arxiv-matches${NC}"
fi

echo -e "${BLUE}Creating subscription: arxiv-matches-sub${NC}"
if gcloud pubsub subscriptions describe arxiv-matches-sub --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}  Subscription already exists, skipping${NC}"
else
    gcloud pubsub subscriptions create arxiv-matches-sub \
        --topic=arxiv-matches \
        --ack-deadline=60 \
        --message-retention-duration=7d \
        --project=$PROJECT_ID
    echo -e "${GREEN}  ✅ Created subscription: arxiv-matches-sub${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Pub/Sub setup complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Topics created:"
echo "  1. arxiv-candidates  → Used by ArXiv Watcher → Intake Pipeline"
echo "  2. arxiv-matches     → Used by Intake Pipeline → Alert Worker"
echo ""
echo "Subscriptions created:"
echo "  1. arxiv-candidates-sub  → Intake Pipeline pulls from here"
echo "  2. arxiv-matches-sub     → Alert Worker pulls from here"
echo ""
echo "To verify:"
echo "  gcloud pubsub topics list --project=$PROJECT_ID"
echo "  gcloud pubsub subscriptions list --project=$PROJECT_ID"
echo ""
