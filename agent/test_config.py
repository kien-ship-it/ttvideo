"""
Tests for configuration validation.

Property 4: Agent Configuration Completeness
Validates: Requirements 7.1-7.5
"""

import pytest
from hypothesis import given, strategies as st, settings

from config import AgentConfig, ConfigurationError, validate_config


# Required fields for a complete configuration
REQUIRED_FIELDS = [
    'LIVEKIT_URL',
    'LIVEKIT_API_KEY',
    'LIVEKIT_API_SECRET',
    'TAVUS_API_KEY',
    'TAVUS_REPLICA_ID',
    'TAVUS_PERSONA_ID',
    'OPENAI_API_KEY',
]


def create_valid_config() -> dict:
    """Create a valid configuration dictionary."""
    return {
        'LIVEKIT_URL': 'wss://test.livekit.cloud',
        'LIVEKIT_API_KEY': 'test_api_key',
        'LIVEKIT_API_SECRET': 'test_api_secret',
        'TAVUS_API_KEY': 'test_tavus_key',
        'TAVUS_REPLICA_ID': 'r_test_replica',
        'TAVUS_PERSONA_ID': 'p_test_persona',
        'OPENAI_API_KEY': 'sk-test-openai-key',
    }


# Strategy for generating non-empty strings (valid config values)
non_empty_string = st.text(min_size=1).filter(lambda s: s.strip())


# Strategy for generating whitespace-only strings
whitespace_only = st.text(alphabet=' \t\n\r', min_size=0, max_size=10)


class TestConfigValidation:
    """Unit tests for configuration validation."""
    
    def test_valid_config_returns_agent_config(self):
        """Test that a valid configuration returns an AgentConfig instance."""
        config = create_valid_config()
        result = validate_config(config)
        
        assert isinstance(result, AgentConfig)
        assert result.livekit_url == 'wss://test.livekit.cloud'
        assert result.livekit_api_key == 'test_api_key'
        assert result.livekit_api_secret == 'test_api_secret'
        assert result.tavus_api_key == 'test_tavus_key'
        assert result.tavus_replica_id == 'r_test_replica'
        assert result.tavus_persona_id == 'p_test_persona'
        assert result.openai_api_key == 'sk-test-openai-key'
    
    def test_missing_field_raises_error(self):
        """Test that missing a required field raises ConfigurationError."""
        for field in REQUIRED_FIELDS:
            config = create_valid_config()
            del config[field]
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_config(config)
            
            assert field in str(exc_info.value)
    
    def test_empty_field_raises_error(self):
        """Test that an empty required field raises ConfigurationError."""
        for field in REQUIRED_FIELDS:
            config = create_valid_config()
            config[field] = ''
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_config(config)
            
            assert field in str(exc_info.value)
    
    def test_whitespace_only_field_raises_error(self):
        """Test that a whitespace-only field raises ConfigurationError."""
        for field in REQUIRED_FIELDS:
            config = create_valid_config()
            config[field] = '   \t\n  '
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_config(config)
            
            assert field in str(exc_info.value)


class TestConfigPropertyBased:
    """
    Property-based tests for configuration validation.
    
    Feature: realtime-digital-human, Property 4: Agent Configuration Completeness
    Validates: Requirements 7.1-7.5
    
    *For any* valid Agent configuration, it SHALL contain:
    - LIVEKIT_URL (non-empty string)
    - LIVEKIT_API_KEY (non-empty string)
    - LIVEKIT_API_SECRET (non-empty string)
    - TAVUS_API_KEY (non-empty string)
    - TAVUS_REPLICA_ID (non-empty string)
    - TAVUS_PERSONA_ID (non-empty string)
    - OPENAI_API_KEY (non-empty string for LLM/TTS)
    """
    
    @given(
        livekit_url=non_empty_string,
        livekit_api_key=non_empty_string,
        livekit_api_secret=non_empty_string,
        tavus_api_key=non_empty_string,
        tavus_replica_id=non_empty_string,
        tavus_persona_id=non_empty_string,
        openai_api_key=non_empty_string,
    )
    @settings(max_examples=100)
    def test_complete_config_always_valid(
        self,
        livekit_url: str,
        livekit_api_key: str,
        livekit_api_secret: str,
        tavus_api_key: str,
        tavus_replica_id: str,
        tavus_persona_id: str,
        openai_api_key: str,
    ):
        """
        Property: For any configuration with all non-empty required fields,
        validation SHALL succeed and return an AgentConfig.
        
        Feature: realtime-digital-human, Property 4: Agent Configuration Completeness
        Validates: Requirements 7.1-7.5
        """
        config = {
            'LIVEKIT_URL': livekit_url,
            'LIVEKIT_API_KEY': livekit_api_key,
            'LIVEKIT_API_SECRET': livekit_api_secret,
            'TAVUS_API_KEY': tavus_api_key,
            'TAVUS_REPLICA_ID': tavus_replica_id,
            'TAVUS_PERSONA_ID': tavus_persona_id,
            'OPENAI_API_KEY': openai_api_key,
        }
        
        result = validate_config(config)
        
        # Verify all fields are present in the result
        assert result.livekit_url == livekit_url.strip()
        assert result.livekit_api_key == livekit_api_key.strip()
        assert result.livekit_api_secret == livekit_api_secret.strip()
        assert result.tavus_api_key == tavus_api_key.strip()
        assert result.tavus_replica_id == tavus_replica_id.strip()
        assert result.tavus_persona_id == tavus_persona_id.strip()
        assert result.openai_api_key == openai_api_key.strip()
    
    @given(
        missing_field=st.sampled_from(REQUIRED_FIELDS),
    )
    @settings(max_examples=100)
    def test_missing_field_always_rejected(self, missing_field: str):
        """
        Property: For any configuration missing a required field,
        validation SHALL fail with ConfigurationError.
        
        Feature: realtime-digital-human, Property 4: Agent Configuration Completeness
        Validates: Requirements 7.1-7.5
        """
        config = create_valid_config()
        del config[missing_field]
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config)
        
        assert missing_field in str(exc_info.value)
    
    @given(
        empty_field=st.sampled_from(REQUIRED_FIELDS),
        whitespace=whitespace_only,
    )
    @settings(max_examples=100)
    def test_whitespace_field_always_rejected(self, empty_field: str, whitespace: str):
        """
        Property: For any configuration with a whitespace-only required field,
        validation SHALL fail with ConfigurationError.
        
        Feature: realtime-digital-human, Property 4: Agent Configuration Completeness
        Validates: Requirements 7.1-7.5
        """
        config = create_valid_config()
        config[empty_field] = whitespace
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config)
        
        assert empty_field in str(exc_info.value)
