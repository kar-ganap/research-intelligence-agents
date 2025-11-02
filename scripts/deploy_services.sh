#!/bin/bash
#
# Deploy Cloud Run Services
# - API Gateway
# - Orchestrator
# - Graph Service
# - Frontend
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-""}
REGION=${REGION:-"us-central1"}

echo -e "${BLUE}Deploying Cloud Run Services...${NC}\n"

# Deploy API Gateway
echo -e "${BLUE}[1/4] Deploying API Gateway...${NC}"
gcloud run deploy api-gateway \
  --source ./src/services/api_gateway \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --project $PROJECT_ID

API_GATEWAY_URL=$(gcloud run services describe api-gateway --region $REGION --format="value(status.url)" --project $PROJECT_ID)
echo -e "${GREEN}✅ API Gateway deployed: $API_GATEWAY_URL${NC}\n"

# Deploy Orchestrator
echo -e "${BLUE}[2/4] Deploying Orchestrator...${NC}"
gcloud run deploy orchestrator \
  --source ./src/services/orchestrator \
  --platform managed \
  --region $REGION \
  --no-allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --project $PROJECT_ID

ORCHESTRATOR_URL=$(gcloud run services describe orchestrator --region $REGION --format="value(status.url)" --project $PROJECT_ID)
echo -e "${GREEN}✅ Orchestrator deployed: $ORCHESTRATOR_URL${NC}\n"

# Deploy Graph Service
echo -e "${BLUE}[3/4] Deploying Graph Service...${NC}"
gcloud run deploy graph-service \
  --source ./src/services/graph_service \
  --platform managed \
  --region $REGION \
  --no-allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --max-instances 5 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --project $PROJECT_ID

GRAPH_SERVICE_URL=$(gcloud run services describe graph-service --region $REGION --format="value(status.url)" --project $PROJECT_ID)
echo -e "${GREEN}✅ Graph Service deployed: $GRAPH_SERVICE_URL${NC}\n"

# Update API Gateway with service URLs
echo -e "${BLUE}Updating API Gateway with service URLs...${NC}"
gcloud run services update api-gateway \
  --region $REGION \
  --update-env-vars ORCHESTRATOR_URL=$ORCHESTRATOR_URL,GRAPH_SERVICE_URL=$GRAPH_SERVICE_URL \
  --project $PROJECT_ID

echo -e "${GREEN}✅ API Gateway updated with service URLs${NC}\n"

# Deploy Frontend
echo -e "${BLUE}[4/4] Deploying Frontend...${NC}"
gcloud run deploy frontend \
  --source ./src/services/frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --timeout 30 \
  --max-instances 5 \
  --set-env-vars API_URL=$API_GATEWAY_URL \
  --project $PROJECT_ID

FRONTEND_URL=$(gcloud run services describe frontend --region $REGION --format="value(status.url)" --project $PROJECT_ID)
echo -e "${GREEN}✅ Frontend deployed: $FRONTEND_URL${NC}\n"

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All services deployed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Service URLs:"
echo "  API Gateway:   $API_GATEWAY_URL"
echo "  Orchestrator:  $ORCHESTRATOR_URL (internal)"
echo "  Graph Service: $GRAPH_SERVICE_URL (internal)"
echo "  Frontend:      $FRONTEND_URL"
echo ""
echo "Try it out:"
echo "  Open: $FRONTEND_URL"
echo "  Or test API: curl -X POST $API_GATEWAY_URL/api/ask -H 'Content-Type: application/json' -d '{\"question\":\"Who are the authors of BERT?\"}'"
echo ""
