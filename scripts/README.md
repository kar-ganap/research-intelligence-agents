# Deployment Scripts

## Quick Start

```bash
# Deploy everything
source .env
./scripts/deploy_all_services.sh
```

That's it. One command.

## Available Scripts

### `deploy_all_services.sh` - Main deployment script
Deploys all services using Cloud Build with pre-built base image (fast).

- Uses base image → 30 seconds per service (vs 5 minutes)
- Includes automatic verification
- Handles all dependencies

### `verify_services.sh` - Verification only
Tests all endpoints without deploying.

### `deploy_with_verification.sh` - Single service with rollback
Deploy one service with automatic rollback on failure.

Example:
```bash
source .env
./scripts/deploy_with_verification.sh orchestrator
```

## How It Works

**Base Image Strategy:**
- Pre-built base image contains all Python dependencies
- Services only copy code changes
- Result: 30 second deployments instead of 5 minutes

**Verification:**
- Automatically runs after deployment
- Tests health endpoints, Q&A, graph data
- Rolls back on failure

**Cloud Build:**
Each Python service has a `cloudbuild.yaml` that:
1. Builds from base image
2. Pushes to Container Registry
3. Deploys to Cloud Run

## Files

```
scripts/
├── deploy_all_services.sh          # THE MAIN ONE
├── verify_services.sh               # Verification
├── deploy_with_verification.sh      # Single service + rollback
└── README.md                        # This file
```

## Rebuild Base Image

Only needed when dependencies change:

```bash
docker build -t gcr.io/research-intel-agents/base:latest -f Dockerfile.base .
docker push gcr.io/research-intel-agents/base:latest
```
