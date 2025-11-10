"""
Configuration management for Research Intelligence Platform
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# ADK Configuration
# ============================================================================

# Unified app name for the Research Intelligence Platform
# Used by all agents and runners for session management
APP_NAME = os.getenv("ADK_APP_NAME", "research_intelligence_platform")

# Default session identifiers
DEFAULT_USER_ID = os.getenv("ADK_DEFAULT_USER_ID", "system")


# ============================================================================
# GCP and Agent Configuration Classes
# ============================================================================

@dataclass
class GCPConfig:
    """GCP configuration"""
    project_id: str
    region: str
    credentials_path: Optional[str]
    google_api_key: str


@dataclass
class AgentConfig:
    """Agent configuration"""
    default_model: str
    temperature: float  # Deprecated - use per-agent temperatures below
    max_tokens: int
    timeout: int

    # Per-agent temperature settings (Option B: Optimized for Hackathon/Discovery)
    entity_temperature: float = 0.2  # Structured extraction - needs consistency
    relationship_temperature: float = 0.7  # Discovery - maximize graph density (proven optimal)
    graph_query_temperature: float = 0.1  # Classification - needs determinism
    answer_temperature: float = 0.4  # Synthesis - slightly creative but grounded
    confidence_temperature: float = 0.2  # Analytical scoring - needs consistency


@dataclass
class Config:
    """Main configuration"""
    gcp: GCPConfig
    agent: AgentConfig
    env: str
    debug: bool


def load_config() -> Config:
    """Load configuration from environment variables"""
    return Config(
        gcp=GCPConfig(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT', ''),
            region=os.getenv('GCP_REGION', 'us-central1'),
            credentials_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            google_api_key=os.getenv('GOOGLE_API_KEY', '')
        ),
        agent=AgentConfig(
            default_model=os.getenv('DEFAULT_MODEL', 'gemini-2.5-pro'),
            temperature=float(os.getenv('DEFAULT_TEMPERATURE', '0.3')),
            max_tokens=int(os.getenv('DEFAULT_MAX_TOKENS', '2048')),
            timeout=int(os.getenv('DEFAULT_TIMEOUT', '30'))
        ),
        env=os.getenv('ENV', 'development'),
        debug=os.getenv('DEBUG', 'false').lower() == 'true'
    )


# Global config instance
config = load_config()
