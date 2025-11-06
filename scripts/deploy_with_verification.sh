#!/bin/bash
#
# Deploy with Verification Script
#
# Deploys a service to Cloud Run with automatic verification and rollback
# Usage: ./deploy_with_verification.sh <service-name> [options]
#

set -e

PROJECT_ID="research-intel-agents"
REGION="us-central1"
MAX_RETRIES=3
VERIFICATION_DELAY=30

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help message
show_help() {
    cat << EOF
Usage: $0 <service-name> [options]

Deploy a service to Cloud Run with automatic verification and rollback.

Arguments:
  service-name          Name of the service to deploy (required)
                        Options: api-gateway, orchestrator, graph-service, frontend

Options:
  --source DIR          Source directory (default: current directory or service-specific)
  --env-vars VARS       Environment variables (comma-separated KEY=VALUE pairs)
  --skip-verify         Skip verification after deployment
  --no-rollback         Don't rollback on failure
  -h, --help            Show this help message

Examples:
  $0 orchestrator
  $0 graph-service --source .
  $0 orchestrator --env-vars="GOOGLE_API_KEY=\${GOOGLE_API_KEY},DEFAULT_MODEL=gemini-2.5-pro"

EOF
}

# Parse arguments
SERVICE_NAME=""
SOURCE_DIR=""
ENV_VARS=""
SKIP_VERIFY=false
NO_ROLLBACK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --source)
            SOURCE_DIR="$2"
            shift 2
            ;;
        --env-vars)
            ENV_VARS="$2"
            shift 2
            ;;
        --skip-verify)
            SKIP_VERIFY=true
            shift
            ;;
        --no-rollback)
            NO_ROLLBACK=true
            shift
            ;;
        -*)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            if [ -z "$SERVICE_NAME" ]; then
                SERVICE_NAME="$1"
            else
                echo "Error: Multiple service names provided"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate service name
if [ -z "$SERVICE_NAME" ]; then
    echo -e "${RED}Error: Service name is required${NC}"
    show_help
    exit 1
fi

# Set default source directories for each service
if [ -z "$SOURCE_DIR" ]; then
    case "$SERVICE_NAME" in
        api-gateway)
            SOURCE_DIR="."
            ;;
        orchestrator)
            SOURCE_DIR="."
            ;;
        graph-service)
            SOURCE_DIR="."
            ;;
        frontend)
            SOURCE_DIR="src/services/frontend"
            ;;
        *)
            SOURCE_DIR="."
            ;;
    esac
fi

echo "=========================================="
echo -e "${BLUE}Deployment with Verification${NC}"
echo "=========================================="
echo "Service:  $SERVICE_NAME"
echo "Source:   $SOURCE_DIR"
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
if [ -n "$ENV_VARS" ]; then
    echo "Env Vars: $ENV_VARS"
fi
echo "=========================================="
echo ""

# Get current revision before deployment
echo "Fetching current revision..."
PREVIOUS_REVISION=$(gcloud run services describe "$SERVICE_NAME" \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.latestReadyRevisionName)' 2>/dev/null || echo "")

if [ -n "$PREVIOUS_REVISION" ]; then
    echo -e "${GREEN}Current revision: $PREVIOUS_REVISION${NC}"
    echo "This will be used for rollback if deployment fails."
else
    echo -e "${YELLOW}Warning: No previous revision found. Rollback will not be available.${NC}"
    NO_ROLLBACK=true
fi
echo ""

# Build deploy command
DEPLOY_CMD="gcloud run deploy $SERVICE_NAME --source $SOURCE_DIR --region=$REGION --project=$PROJECT_ID --allow-unauthenticated"

if [ -n "$ENV_VARS" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --set-env-vars=\"$ENV_VARS\""
fi

# Deploy the service
echo "=========================================="
echo -e "${BLUE}Step 1: Deploying Service${NC}"
echo "=========================================="
echo "Running: $DEPLOY_CMD"
echo ""

DEPLOY_OUTPUT=$(mktemp)
if eval "$DEPLOY_CMD" 2>&1 | tee "$DEPLOY_OUTPUT"; then
    echo ""
    echo -e "${GREEN}✓ Deployment succeeded${NC}"
else
    echo ""
    echo -e "${RED}✗ Deployment failed${NC}"
    rm -f "$DEPLOY_OUTPUT"
    exit 1
fi

# Get new revision
NEW_REVISION=$(gcloud run services describe "$SERVICE_NAME" \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.latestReadyRevisionName)' 2>/dev/null || echo "")

echo -e "${GREEN}New revision: $NEW_REVISION${NC}"
echo ""
rm -f "$DEPLOY_OUTPUT"

# Skip verification if requested
if [ "$SKIP_VERIFY" = true ]; then
    echo -e "${YELLOW}Skipping verification (--skip-verify flag)${NC}"
    echo -e "${GREEN}✅ Deployment complete${NC}"
    exit 0
fi

# Wait for service to be ready
echo "=========================================="
echo -e "${BLUE}Step 2: Waiting for Service to be Ready${NC}"
echo "=========================================="
echo "Waiting ${VERIFICATION_DELAY}s for service to stabilize..."
sleep $VERIFICATION_DELAY
echo -e "${GREEN}✓ Wait complete${NC}"
echo ""

# Verify the deployment
echo "=========================================="
echo -e "${BLUE}Step 3: Verifying Deployment${NC}"
echo "=========================================="

# Run verification script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_SCRIPT="$SCRIPT_DIR/verify_services.sh"

if [ ! -f "$VERIFY_SCRIPT" ]; then
    echo -e "${YELLOW}Warning: Verification script not found at $VERIFY_SCRIPT${NC}"
    echo -e "${YELLOW}Skipping verification${NC}"
    echo -e "${GREEN}✅ Deployment complete (unverified)${NC}"
    exit 0
fi

VERIFICATION_FAILED=false
if bash "$VERIFY_SCRIPT"; then
    echo ""
    echo -e "${GREEN}✓ Verification passed${NC}"
else
    echo ""
    echo -e "${RED}✗ Verification failed${NC}"
    VERIFICATION_FAILED=true
fi

# Handle verification failure
if [ "$VERIFICATION_FAILED" = true ]; then
    echo ""
    echo "=========================================="
    echo -e "${RED}Deployment Verification Failed${NC}"
    echo "=========================================="

    if [ "$NO_ROLLBACK" = true ] || [ -z "$PREVIOUS_REVISION" ]; then
        echo -e "${YELLOW}Rollback not available or disabled${NC}"
        echo -e "${RED}❌ Deployment failed - manual intervention required${NC}"
        exit 1
    fi

    echo "Attempting to rollback to previous revision: $PREVIOUS_REVISION"
    echo ""

    # Rollback to previous revision
    if gcloud run services update-traffic "$SERVICE_NAME" \
        --region=$REGION \
        --project=$PROJECT_ID \
        --to-revisions="$PREVIOUS_REVISION=100" 2>&1; then

        echo ""
        echo -e "${GREEN}✓ Rollback successful${NC}"
        echo "Service has been restored to revision: $PREVIOUS_REVISION"
        echo ""

        # Optionally delete the failed revision
        echo "Cleaning up failed revision: $NEW_REVISION"
        if gcloud run revisions delete "$NEW_REVISION" \
            --region=$REGION \
            --project=$PROJECT_ID \
            --quiet 2>&1; then
            echo -e "${GREEN}✓ Failed revision deleted${NC}"
        else
            echo -e "${YELLOW}Warning: Could not delete failed revision${NC}"
        fi

        echo ""
        echo -e "${RED}❌ Deployment failed and was rolled back${NC}"
        exit 1
    else
        echo ""
        echo -e "${RED}✗ Rollback failed${NC}"
        echo -e "${RED}❌ Manual intervention required${NC}"
        echo ""
        echo "To manually rollback, run:"
        echo "  gcloud run services update-traffic $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --to-revisions=$PREVIOUS_REVISION=100"
        exit 1
    fi
fi

# Success
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Deployment Successful${NC}"
echo "=========================================="
echo "Service:  $SERVICE_NAME"
echo "Revision: $NEW_REVISION"
echo "Status:   Verified and healthy"
echo ""

exit 0
