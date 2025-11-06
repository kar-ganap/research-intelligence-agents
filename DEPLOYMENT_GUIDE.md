# Deployment Guide - How to Deploy Without Breaking Things

## The Problem
When we deploy individual services manually, we often forget to:
1. Pass all required environment variables
2. Update dependent services
3. Update frontend configuration with new backend URLs

This causes cascading failures where one service can't reach another.

## The Solution: Service Dependency Management

### Quick Fix: Always Use the Main Script
```bash
source .env
./scripts/deploy_all_services.sh
```

This ensures all services are deployed with correct configurations and environment variables.

### When You Need to Deploy Just One Service

**RULE: Never deploy a service in isolation if it depends on or is depended upon by other services.**

#### Safe Single-Service Deployments:
Only these can be safely deployed alone:
- **Frontend only** - IF backend URLs haven't changed
- **Orchestrator** - But then you MUST redeploy API Gateway with new URL

#### Service Dependency Chain:
```
Frontend
   ↓ (needs API_BASE_URL)
API Gateway
   ↓ (needs ORCHESTRATOR_URL, GRAPH_SERVICE_URL)
Orchestrator + Graph Service
```

### Deployment Strategies

#### Strategy 1: Full Deployment (Safest)
Use when making ANY backend changes:
```bash
source .env
./scripts/deploy_all_services.sh
```

**Pros:**
- Everything stays in sync
- All environment variables correct
- No broken dependencies

**Cons:**
- Takes ~3-4 minutes
- Rebuilds everything

#### Strategy 2: Incremental Deployment (Faster, but requires care)

**Step 1:** Deploy backend services with Cloud Build
```bash
# Deploy orchestrator
gcloud builds submit --config src/services/orchestrator/cloudbuild.yaml --project research-intel-agents .

gcloud run deploy orchestrator \
  --image gcr.io/research-intel-agents/orchestrator:latest \
  --region us-central1 \
  --project research-intel-agents \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=research-intel-agents,GOOGLE_API_KEY=$GOOGLE_API_KEY,DEFAULT_MODEL=gemini-2.5-pro"

# Deploy graph-service
gcloud builds submit --config src/services/graph_service/cloudbuild.yaml --project research-intel-agents .

gcloud run deploy graph-service \
  --image gcr.io/research-intel-agents/graph-service:latest \
  --region us-central1 \
  --project research-intel-agents \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=research-intel-agents"
```

**Step 2:** Get the URLs and deploy API Gateway
```bash
ORCHESTRATOR_URL=$(gcloud run services describe orchestrator --region us-central1 --project research-intel-agents --format='value(status.url)')
GRAPH_SERVICE_URL=$(gcloud run services describe graph-service --region us-central1 --project research-intel-agents --format='value(status.url)')

gcloud run deploy api-gateway \
  --source src/services/api_gateway \
  --region us-central1 \
  --project research-intel-agents \
  --allow-unauthenticated \
  --set-env-vars="ORCHESTRATOR_URL=$ORCHESTRATOR_URL,GRAPH_SERVICE_URL=$GRAPH_SERVICE_URL,GOOGLE_CLOUD_PROJECT=research-intel-agents"
```

**Step 3:** Deploy Frontend with updated config
```bash
API_GATEWAY_URL=$(gcloud run services describe api-gateway --region us-central1 --project research-intel-agents --format='value(status.url)')

# Update config.js
cat > src/services/frontend/config.js <<EOF
// Auto-generated config - DO NOT EDIT MANUALLY
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8080'
    : '${API_GATEWAY_URL}';
EOF

gcloud run deploy frontend \
  --source src/services/frontend \
  --region us-central1 \
  --project research-intel-agents \
  --allow-unauthenticated
```

#### Strategy 3: Frontend-Only Deployment
Safe ONLY if you're changing frontend code without touching backend APIs:

```bash
gcloud run deploy frontend \
  --source src/services/frontend \
  --region us-central1 \
  --project research-intel-agents \
  --allow-unauthenticated
```

**When is this safe?**
- CSS/styling changes
- UI text changes
- Client-side logic changes
- Graph visualization tweaks

**When is this NOT safe?**
- Backend API URLs changed
- API Gateway was redeployed
- New API endpoints added

## Improved Solution: Infrastructure as Code

### What We Should Build

Create a `deploy_service.sh` script that handles dependencies automatically:

```bash
#!/bin/bash
# Usage: ./scripts/deploy_service.sh <service-name>
# Automatically handles dependent services

SERVICE=$1

case $SERVICE in
  orchestrator)
    # Deploy orchestrator, then update API gateway
    ;;
  graph-service)
    # Deploy graph service, then update API gateway
    ;;
  api-gateway)
    # Get URLs for dependent services first, then deploy
    ;;
  frontend)
    # Get API gateway URL first, update config, then deploy
    ;;
  all)
    # Full deployment
    ;;
esac
```

### Even Better: Use Terraform or Pulumi

Benefits:
1. **Declarative config** - Define desired state, not steps
2. **Automatic dependency resolution** - Services deployed in correct order
3. **State management** - Know what's currently deployed
4. **Rollback capability** - Easy to revert
5. **Environment variables stored** - No manual env var management

Example Terraform structure:
```hcl
resource "google_cloud_run_service" "orchestrator" {
  name     = "orchestrator"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/research-intel-agents/orchestrator:latest"
        env {
          name  = "GOOGLE_API_KEY"
          value = var.google_api_key
        }
      }
    }
  }
}

resource "google_cloud_run_service" "api_gateway" {
  name     = "api-gateway"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/research-intel-agents/api-gateway:latest"
        env {
          name  = "ORCHESTRATOR_URL"
          value = google_cloud_run_service.orchestrator.status[0].url
        }
      }
    }
  }

  # Automatic dependency
  depends_on = [google_cloud_run_service.orchestrator]
}
```

## Current Action Items

### Immediate (Today):
1. ✅ Use `deploy_all_services.sh` for all deployments
2. ✅ Document this in DEPLOYMENT_GUIDE.md
3. Document the service dependency chain

### Short-term (This Week):
1. Create `deploy_service.sh` with automatic dependency handling
2. Add environment variable validation to deployment scripts
3. Add deployment health checks after each service

### Long-term (Next Sprint):
1. Migrate to Terraform/Pulumi for infrastructure as code
2. Set up CI/CD pipeline (GitHub Actions or Cloud Build triggers)
3. Implement blue-green or canary deployments
4. Add automated rollback on health check failures

## Emergency Recovery

If everything is broken:
```bash
# 1. Check what's deployed
gcloud run services list --region us-central1 --project research-intel-agents

# 2. Check logs for each service
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-gateway" \
  --limit 50 --project research-intel-agents

# 3. Redeploy everything from scratch
source .env
./scripts/deploy_all_services.sh

# 4. If that fails, check .env has GOOGLE_API_KEY set
echo $GOOGLE_API_KEY
```

## Best Practices Moving Forward

1. **Always test locally first** if possible
2. **Use the deployment script** - don't deploy manually
3. **Check logs immediately** after deployment
4. **Verify health endpoints** before declaring success
5. **Keep track of what changed** - commit before deploying
6. **Have a rollback plan** - know the previous working revision
