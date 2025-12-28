"""Configuration validation for the Digital Human Agent."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for the Digital Human Agent."""
    
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    tavus_api_key: str
    tavus_replica_id: str
    tavus_persona_id: str
    openai_api_key: str


class ConfigurationError(Exception):
    """Raised when configuration is invalid or incomplete."""
    pass


def validate_config(config: dict) -> AgentConfig:
    """
    Validate that all required configuration fields are present and non-empty.
    
    Args:
        config: Dictionary containing configuration values
        
    Returns:
        AgentConfig with validated values
        
    Raises:
        ConfigurationError: If any required field is missing or empty
    """
    required_fields = [
        'LIVEKIT_URL',
        'LIVEKIT_API_KEY',
        'LIVEKIT_API_SECRET',
        'TAVUS_API_KEY',
        'TAVUS_REPLICA_ID',
        'TAVUS_PERSONA_ID',
        'OPENAI_API_KEY',
    ]
    
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in config:
            missing_fields.append(field)
        elif not config[field] or not config[field].strip():
            empty_fields.append(field)
    
    if missing_fields:
        raise ConfigurationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    if empty_fields:
        raise ConfigurationError(f"Empty required fields: {', '.join(empty_fields)}")
    
    return AgentConfig(
        livekit_url=config['LIVEKIT_URL'].strip(),
        livekit_api_key=config['LIVEKIT_API_KEY'].strip(),
        livekit_api_secret=config['LIVEKIT_API_SECRET'].strip(),
        tavus_api_key=config['TAVUS_API_KEY'].strip(),
        tavus_replica_id=config['TAVUS_REPLICA_ID'].strip(),
        tavus_persona_id=config['TAVUS_PERSONA_ID'].strip(),
        openai_api_key=config['OPENAI_API_KEY'].strip(),
    )


def load_config_from_env() -> AgentConfig:
    """
    Load and validate configuration from environment variables.
    
    Returns:
        AgentConfig with validated values from environment
        
    Raises:
        ConfigurationError: If any required environment variable is missing or empty
    """
    config = {
        'LIVEKIT_URL': os.getenv('LIVEKIT_URL', ''),
        'LIVEKIT_API_KEY': os.getenv('LIVEKIT_API_KEY', ''),
        'LIVEKIT_API_SECRET': os.getenv('LIVEKIT_API_SECRET', ''),
        'TAVUS_API_KEY': os.getenv('TAVUS_API_KEY', ''),
        'TAVUS_REPLICA_ID': os.getenv('TAVUS_REPLICA_ID', ''),
        'TAVUS_PERSONA_ID': os.getenv('TAVUS_PERSONA_ID', ''),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
    }
    
    return validate_config(config)
