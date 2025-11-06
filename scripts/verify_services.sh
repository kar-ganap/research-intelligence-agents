#!/bin/bash
#
# Service Verification Script
#
# Verifies all deployed services are healthy and functional
# Returns 0 if all checks pass, 1 if any check fails
#

set -e

PROJECT_ID="research-intel-agents"
REGION="us-central1"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo "=========================================="
echo "Service Verification Script"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "=========================================="
echo ""

# Function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    local max_retries=${4:-3}
    local retry_delay=${5:-5}

    echo -n "Checking $name... "

    for i in $(seq 1 $max_retries); do
        if [ $i -gt 1 ]; then
            echo -n "(retry $i/$max_retries) "
            sleep $retry_delay
        fi

        response=$(curl -s -w "\n%{http_code}" "$url" 2>&1 || echo "000")
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n-1)

        if [ "$status_code" == "$expected_status" ]; then
            echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
            PASSED=$((PASSED + 1))
            return 0
        fi
    done

    echo -e "${RED}✗ FAIL${NC} (HTTP $status_code, expected $expected_status)"
    echo "  URL: $url"
    echo "  Response: ${body:0:200}"
    FAILED=$((FAILED + 1))
    return 1
}

# Function to check JSON endpoint with validation
check_json_endpoint() {
    local name=$1
    local url=$2
    local jq_filter=$3
    local expected_value=$4
    local max_retries=${5:-3}
    local retry_delay=${6:-5}

    echo -n "Checking $name... "

    for i in $(seq 1 $max_retries); do
        if [ $i -gt 1 ]; then
            echo -n "(retry $i/$max_retries) "
            sleep $retry_delay
        fi

        response=$(curl -s "$url" 2>&1 || echo "{}")

        if echo "$response" | jq -e "$jq_filter" > /dev/null 2>&1; then
            actual_value=$(echo "$response" | jq -r "$jq_filter")
            if [ "$actual_value" == "$expected_value" ]; then
                echo -e "${GREEN}✓ PASS${NC} ($jq_filter = $expected_value)"
                PASSED=$((PASSED + 1))
                return 0
            fi
        fi
    done

    echo -e "${RED}✗ FAIL${NC}"
    echo "  URL: $url"
    echo "  Filter: $jq_filter"
    echo "  Expected: $expected_value"
    echo "  Response: ${response:0:200}"
    FAILED=$((FAILED + 1))
    return 1
}

# Get service URLs
echo "Fetching service URLs..."
API_GATEWAY_URL=$(gcloud run services describe api-gateway --region=$REGION --project=$PROJECT_ID --format='value(status.url)' 2>/dev/null || echo "")
ORCHESTRATOR_URL=$(gcloud run services describe orchestrator --region=$REGION --project=$PROJECT_ID --format='value(status.url)' 2>/dev/null || echo "")
GRAPH_SERVICE_URL=$(gcloud run services describe graph-service --region=$REGION --project=$PROJECT_ID --format='value(status.url)' 2>/dev/null || echo "")
FRONTEND_URL=$(gcloud run services describe frontend --region=$REGION --project=$PROJECT_ID --format='value(status.url)' 2>/dev/null || echo "")

echo ""
echo "Service URLs:"
echo "  API Gateway:   $API_GATEWAY_URL"
echo "  Orchestrator:  $ORCHESTRATOR_URL"
echo "  Graph Service: $GRAPH_SERVICE_URL"
echo "  Frontend:      $FRONTEND_URL"
echo ""

# Check if services are deployed
if [ -z "$API_GATEWAY_URL" ]; then
    echo -e "${RED}✗ FAIL${NC} API Gateway not deployed"
    exit 1
fi

if [ -z "$ORCHESTRATOR_URL" ]; then
    echo -e "${RED}✗ FAIL${NC} Orchestrator not deployed"
    exit 1
fi

if [ -z "$GRAPH_SERVICE_URL" ]; then
    echo -e "${RED}✗ FAIL${NC} Graph Service not deployed"
    exit 1
fi

if [ -z "$FRONTEND_URL" ]; then
    echo -e "${RED}✗ FAIL${NC} Frontend not deployed"
    exit 1
fi

echo "=========================================="
echo "Running Health Checks"
echo "=========================================="
echo ""

# API Gateway checks
echo "--- API Gateway ---"
check_json_endpoint "API Gateway health" "$API_GATEWAY_URL/health" ".status" "healthy"
echo ""

# Orchestrator checks
echo "--- Orchestrator ---"
check_json_endpoint "Orchestrator health" "$ORCHESTRATOR_URL/health" ".status" "healthy"
echo ""

# Graph Service checks
echo "--- Graph Service ---"
check_json_endpoint "Graph Service health" "$GRAPH_SERVICE_URL/health" ".status" "healthy"
check_endpoint "Graph Service /graph" "$GRAPH_SERVICE_URL/graph" 200
check_endpoint "Graph Service /relationships" "$GRAPH_SERVICE_URL/relationships" 200
echo ""

# Frontend checks
echo "--- Frontend ---"
check_endpoint "Frontend root" "$FRONTEND_URL/" 200
echo ""

echo "=========================================="
echo "Running Functional Tests"
echo "=========================================="
echo ""

# Test Q&A endpoint (this was the broken one)
echo "--- Q&A Functionality ---"
echo -n "Testing Q&A endpoint... "
qa_response=$(curl -s -X POST "$API_GATEWAY_URL/api/ask" \
    -H "Content-Type: application/json" \
    -d '{"question": "test"}' 2>&1 || echo "{}")

# Check if response has error
if echo "$qa_response" | jq -e '.error' > /dev/null 2>&1; then
    error_msg=$(echo "$qa_response" | jq -r '.error')
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Error: $error_msg"
    FAILED=$((FAILED + 1))
elif echo "$qa_response" | jq -e '.answer' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Unexpected response format"
    echo "  Response: ${qa_response:0:200}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Test graph data has categories
echo "--- Graph Data Quality ---"
echo -n "Testing graph node categories... "
graph_data=$(curl -s "$GRAPH_SERVICE_URL/graph" 2>&1 || echo "{}")

if echo "$graph_data" | jq -e '.nodes[0].primary_category' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} - Nodes missing primary_category field"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test papers have published dates
echo -n "Testing paper published dates... "
papers_response=$(curl -s "$ORCHESTRATOR_URL/papers" 2>&1 || echo "{}")

if echo "$papers_response" | jq -e '.papers[0].published' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Papers missing published dates"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ VERIFICATION FAILED${NC}"
    echo ""
    echo "Some checks failed. Review the output above for details."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  VERIFICATION PASSED WITH WARNINGS${NC}"
    echo ""
    echo "All critical checks passed but some warnings were found."
    exit 0
else
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo ""
    echo "All services are healthy and functional!"
    exit 0
fi
