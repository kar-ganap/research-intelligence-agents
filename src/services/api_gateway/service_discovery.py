"""
Service Discovery for Cloud Run

Dynamically discovers service URLs by querying Cloud Run API.
This ensures URLs are always up-to-date even after redeployments.
"""

import os
import subprocess
import logging
import json
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache TTL: 5 minutes (services don't redeploy that often)
CACHE_TTL_SECONDS = 300


@lru_cache(maxsize=10)
def get_service_url(service_name: str, region: str = 'us-central1', project_id: str = None) -> str:
    """
    Get the URL for a Cloud Run service by name.

    Uses gcloud CLI to query the latest service URL.
    Results are cached to avoid repeated API calls.

    Args:
        service_name: Name of the Cloud Run service (e.g., 'orchestrator')
        region: GCP region (default: us-central1)
        project_id: GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)

    Returns:
        Service URL (e.g., 'https://orchestrator-xxx.run.app')

    Raises:
        RuntimeError: If service discovery fails
    """

    # Get project ID
    if not project_id:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')

    if not project_id:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT environment variable not set")

    try:
        # Use gcloud to get service URL
        cmd = [
            'gcloud', 'run', 'services', 'describe',
            service_name,
            f'--region={region}',
            f'--project={project_id}',
            '--format=value(status.url)'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to discover {service_name}: {result.stderr}")

        url = result.stdout.strip()

        if not url:
            raise RuntimeError(f"No URL found for service: {service_name}")

        logger.info(f"Discovered {service_name} at {url}")
        return url

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout while discovering service: {service_name}")
    except Exception as e:
        raise RuntimeError(f"Service discovery failed for {service_name}: {e}")


def get_orchestrator_url() -> str:
    """Get Orchestrator service URL."""
    # Check environment variable first (for local dev)
    env_url = os.environ.get('ORCHESTRATOR_URL')
    if env_url:
        return env_url

    # Otherwise discover via Cloud Run API
    return get_service_url('orchestrator')


def get_graph_service_url() -> str:
    """Get Graph Service URL."""
    # Check environment variable first (for local dev)
    env_url = os.environ.get('GRAPH_SERVICE_URL')
    if env_url:
        return env_url

    # Otherwise discover via Cloud Run API
    return get_service_url('graph-service')


def get_api_gateway_url() -> str:
    """Get API Gateway URL (own service)."""
    # Check environment variable first
    env_url = os.environ.get('API_GATEWAY_URL')
    if env_url:
        return env_url

    # Otherwise discover via Cloud Run API
    return get_service_url('api-gateway')
