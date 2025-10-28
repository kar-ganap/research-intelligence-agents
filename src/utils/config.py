"""
Configuration management for Research Intelligence Platform
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class GCPConfig:
    """GCP configuration"""
    project_id: str
    region: str
    credentials_path: Optional[str]


@dataclass
class AgentConfig:
    """Agent configuration"""
    default_model: str
    temperature: float
    max_tokens: int
    timeout: int


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
            credentials_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        ),
        agent=AgentConfig(
            default_model=os.getenv('DEFAULT_MODEL', 'gemini-2.0-flash-exp'),
            temperature=float(os.getenv('DEFAULT_TEMPERATURE', '0.3')),
            max_tokens=int(os.getenv('DEFAULT_MAX_TOKENS', '2048')),
            timeout=int(os.getenv('DEFAULT_TIMEOUT', '30'))
        ),
        env=os.getenv('ENV', 'development'),
        debug=os.getenv('DEBUG', 'false').lower() == 'true'
    )


# Global config instance
config = load_config()
