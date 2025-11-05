#!/bin/bash
#
# Deploy All Services with Auto URL Discovery
#
# Deploys all Cloud Run services and automatically updates URLs
# so services always point to the latest deployments.
#
# Cloud Run doesn't require stopping services - new revisions are
# deployed and traffic is automatically shifted to the new revision.
# Old revisions are kept for rollback but don't consume resources.
#

set -e  # Exit on error

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-research-intel-agents}"
REGION="us-central1"

echo "================================================================"
echo "Deploying Research Intelligence Platform to Cloud Run"
echo "================================================================"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Step 1: Delete all existing services for clean deployment
echo "Step 1/5: Cleaning up existing services..."
echo ""

for service in frontend api-gateway orchestrator graph-service; do
    echo "→ Checking if $service exists..."
    if gcloud run services describe $service --region $REGION --project $PROJECT_ID &>/dev/null; then
        echo "  Deleting $service..."
        gcloud run services delete $service --region $REGION --project $PROJECT_ID --quiet
        echo "  ✓ Deleted $service"
    else
        echo "  ✓ $service does not exist (skipping)"
    fi
done

# Deploy backend services first (no dependencies)
echo ""
echo "Step 2/5: Deploying backend services..."
echo ""

echo "→ Deploying Orchestrator..."
cp src/services/orchestrator/Dockerfile Dockerfile
ORCHESTRATOR_OUTPUT=$(gcloud run deploy orchestrator \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --quiet 2>&1)
echo "$ORCHESTRATOR_OUTPUT"
ORCHESTRATOR_URL=$(echo "$ORCHESTRATOR_OUTPUT" | grep -o 'Service URL: .*' | sed 's/Service URL: //' | tr -d '[:space:]' | sed 's/\x1b\[[0-9;]*m//g')
rm Dockerfile

echo "→ Deploying Graph Service..."
cp src/services/graph_service/Dockerfile Dockerfile
GRAPH_OUTPUT=$(gcloud run deploy graph-service \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --quiet 2>&1)
echo "$GRAPH_OUTPUT"
GRAPH_SERVICE_URL=$(echo "$GRAPH_OUTPUT" | grep -o 'Service URL: .*' | sed 's/Service URL: //' | tr -d '[:space:]' | sed 's/\x1b\[[0-9;]*m//g')
rm Dockerfile

# Get backend URLs
echo ""
echo "Step 3/5: Backend service URLs captured from deployment:"
echo "✓ Orchestrator: $ORCHESTRATOR_URL"
echo "✓ Graph Service: $GRAPH_SERVICE_URL"

# Deploy API Gateway with backend URLs
echo ""
echo "Step 4/5: Deploying API Gateway..."
cp src/services/api_gateway/Dockerfile Dockerfile
API_GATEWAY_OUTPUT=$(gcloud run deploy api-gateway \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "ORCHESTRATOR_URL=$ORCHESTRATOR_URL,GRAPH_SERVICE_URL=$GRAPH_SERVICE_URL,GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --quiet 2>&1)
echo "$API_GATEWAY_OUTPUT"
API_GATEWAY_URL=$(echo "$API_GATEWAY_OUTPUT" | grep -o 'Service URL: .*' | sed 's/Service URL: //' | tr -d '[:space:]' | sed 's/\x1b\[[0-9;]*m//g')
rm Dockerfile
echo "✓ API Gateway: $API_GATEWAY_URL"

# Update frontend config with API Gateway URL
echo ""
echo "Step 5/5: Updating frontend config and deploying..."

# Generate timestamp for cache-busting
CACHE_BUST_VERSION=$(date +%Y%m%d%H%M%S)

# Create a config.js file for the frontend
cat > src/services/frontend/config.js <<EOF
// Auto-generated config - DO NOT EDIT MANUALLY
// Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8080'
    : '${API_GATEWAY_URL}';
EOF

# Update HTML to load config.js in head section with cache-busting
# First, remove any existing config.js script tags and comments
sed -i.bak '/<script.*src="config\.js/d; /Load config FIRST/d' src/services/frontend/index.html

# Then add config.js as first script in head (after title) with proper newlines
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS sed
    sed -i.bak "/<title>.*<\/title>/a\\
\ \ \ \ <!-- Load config FIRST to ensure API_BASE_URL is defined before app.js runs -->\\
\ \ \ \ <script type=\"text/javascript\" src=\"config.js?v=${CACHE_BUST_VERSION}\"></script>
" src/services/frontend/index.html
else
    # Linux sed
    sed -i.bak "/<title>.*<\/title>/a\    <!-- Load config FIRST to ensure API_BASE_URL is defined before app.js runs -->\n    <script type=\"text/javascript\" src=\"config.js?v=${CACHE_BUST_VERSION}\"></script>" src/services/frontend/index.html
fi

rm -f src/services/frontend/index.html.bak

echo "→ Deploying Frontend..."
FRONTEND_OUTPUT=$(gcloud run deploy frontend \
  --source src/services/frontend \
  --region $REGION \
  --allow-unauthenticated \
  --quiet 2>&1)
echo "$FRONTEND_OUTPUT"
FRONTEND_URL=$(echo "$FRONTEND_OUTPUT" | grep -o 'Service URL: .*' | sed 's/Service URL: //' | tr -d '[:space:]' | sed 's/\x1b\[[0-9;]*m//g')
echo "✓ Frontend: $FRONTEND_URL"

echo ""
echo "================================================================"
echo "✅ Deployment Complete!"
echo "================================================================"
echo ""
echo "Service URLs:"
echo "  Frontend:      $FRONTEND_URL"
echo "  API Gateway:   $API_GATEWAY_URL"
echo "  Orchestrator:  $ORCHESTRATOR_URL"
echo "  Graph Service: $GRAPH_SERVICE_URL"
echo ""
echo "🚀 Open your app: $FRONTEND_URL"
echo ""
