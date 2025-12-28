"""
Unit tests for Digital Human Agent configuration and initialization.

Requirements: 3.1, 7.1-7.5
"""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from config import ConfigurationError


class TestDigitalHumanAgentInit:
    """Unit tests for DigitalHumanAgent initialization."""
    
    def test_agent_init_with_default_values(self):
        """Test agent initialization with default parameter values."""
        # Import here to avoid import errors if livekit not installed
        from agent import DigitalHumanAgent, DEFAULT_SYSTEM_PROMPT
        
        agent = DigitalHumanAgent()
        
        assert agent.llm_model == "gpt-4o"
        assert agent.llm_temperature == 0.7
        assert agent.tts_voice == "alloy"
        assert agent._instructions == DEFAULT_SYSTEM_PROMPT
    
    def test_agent_init_with_custom_values(self):
        """Test agent initialization with custom parameter values."""
        from agent import DigitalHumanAgent
        
        custom_prompt = "You are a custom assistant."
        agent = DigitalHumanAgent(
            instructions=custom_prompt,
            llm_model="gpt-4o-mini",
            llm_temperature=0.5,
            tts_voice="nova",
        )
        
        assert agent.llm_model == "gpt-4o-mini"
        assert agent.llm_temperature == 0.5
        assert agent.tts_voice == "nova"
        assert agent._instructions == custom_prompt
    
    def test_agent_init_config_not_loaded_initially(self):
        """Test that config is not loaded until needed."""
        from agent import DigitalHumanAgent
        
        agent = DigitalHumanAgent()
        
        assert agent._config is None
        assert agent._avatar is None
        assert agent._session is None


class TestAgentConfigLoading:
    """Tests for agent configuration loading."""
    
    def test_load_config_with_valid_env(self):
        """Test loading config when all environment variables are set."""
        from agent import DigitalHumanAgent
        
        env_vars = {
            'LIVEKIT_URL': 'wss://test.livekit.cloud',
            'LIVEKIT_API_KEY': 'test_key',
            'LIVEKIT_API_SECRET': 'test_secret',
            'TAVUS_API_KEY': 'tavus_key',
            'TAVUS_REPLICA_ID': 'r_test',
            'TAVUS_PERSONA_ID': 'p_test',
            'OPENAI_API_KEY': 'sk-test',
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            agent = DigitalHumanAgent()
            config = agent._load_config()
            
            assert config.livekit_url == 'wss://test.livekit.cloud'
            assert config.livekit_api_key == 'test_key'
            assert config.tavus_replica_id == 'r_test'
            assert config.openai_api_key == 'sk-test'
    
    def test_load_config_with_missing_env_raises_error(self):
        """Test that missing environment variables raise ConfigurationError."""
        from agent import DigitalHumanAgent
        
        # Clear all relevant env vars
        env_vars = {
            'LIVEKIT_URL': '',
            'LIVEKIT_API_KEY': '',
            'LIVEKIT_API_SECRET': '',
            'TAVUS_API_KEY': '',
            'TAVUS_REPLICA_ID': '',
            'TAVUS_PERSONA_ID': '',
            'OPENAI_API_KEY': '',
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            agent = DigitalHumanAgent()
            
            with pytest.raises(ConfigurationError):
                agent._load_config()
    
    def test_config_cached_after_first_load(self):
        """Test that config is cached after first load."""
        from agent import DigitalHumanAgent
        
        env_vars = {
            'LIVEKIT_URL': 'wss://test.livekit.cloud',
            'LIVEKIT_API_KEY': 'test_key',
            'LIVEKIT_API_SECRET': 'test_secret',
            'TAVUS_API_KEY': 'tavus_key',
            'TAVUS_REPLICA_ID': 'r_test',
            'TAVUS_PERSONA_ID': 'p_test',
            'OPENAI_API_KEY': 'sk-test',
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            agent = DigitalHumanAgent()
            
            config1 = agent._load_config()
            config2 = agent._load_config()
            
            # Should be the same object (cached)
            assert config1 is config2


class TestEntrypoint:
    """Tests for the agent entrypoint function."""
    
    def test_entrypoint_validates_config_first(self):
        """Test that entrypoint validates configuration before connecting."""
        from agent import load_config_from_env
        
        # With missing config, should raise ConfigurationError
        env_vars = {
            'LIVEKIT_URL': '',
            'LIVEKIT_API_KEY': '',
            'LIVEKIT_API_SECRET': '',
            'TAVUS_API_KEY': '',
            'TAVUS_REPLICA_ID': '',
            'TAVUS_PERSONA_ID': '',
            'OPENAI_API_KEY': '',
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with pytest.raises(ConfigurationError):
                load_config_from_env()


class TestPrewarm:
    """Tests for the prewarm function."""
    
    def test_prewarm_validates_config(self):
        """Test that prewarm attempts to validate configuration."""
        from agent import prewarm
        
        env_vars = {
            'LIVEKIT_URL': 'wss://test.livekit.cloud',
            'LIVEKIT_API_KEY': 'test_key',
            'LIVEKIT_API_SECRET': 'test_secret',
            'TAVUS_API_KEY': 'tavus_key',
            'TAVUS_REPLICA_ID': 'r_test',
            'TAVUS_PERSONA_ID': 'p_test',
            'OPENAI_API_KEY': 'sk-test',
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            # Should not raise - just logs warning if config incomplete
            mock_proc = MagicMock()
            prewarm(mock_proc)  # Should complete without error


class TestAgentErrorHandling:
    """Tests for agent error handling functionality.
    
    Requirements: 3.5, 4.5, 8.1
    """
    
    def test_agent_error_classes_exist(self):
        """Test that custom error classes are defined."""
        from agent import AgentError, LLMError, TTSError, TavusError
        
        # Verify inheritance
        assert issubclass(LLMError, AgentError)
        assert issubclass(TTSError, AgentError)
        assert issubclass(TavusError, AgentError)
    
    def test_agent_has_audio_only_mode_flag(self):
        """Test that agent has audio-only mode flag for Tavus fallback."""
        from agent import DigitalHumanAgent
        
        agent = DigitalHumanAgent()
        
        # Should default to False
        assert agent._audio_only_mode is False
    
    def test_log_error_method_exists(self):
        """Test that _log_error method exists for detailed error logging."""
        from agent import DigitalHumanAgent
        
        agent = DigitalHumanAgent()
        
        # Method should exist
        assert hasattr(agent, '_log_error')
        assert callable(agent._log_error)
    
    def test_log_error_returns_error_details(self):
        """Test that _log_error returns structured error information."""
        from agent import DigitalHumanAgent
        
        agent = DigitalHumanAgent()
        
        test_error = ValueError("Test error message")
        result = agent._log_error("TEST", test_error, "Test context")
        
        assert result is not None
        assert result["error_type"] == "TEST"
        assert result["error_class"] == "ValueError"
        assert result["error_message"] == "Test error message"
        assert result["context"] == "Test context"
        assert "traceback" in result
    
    def test_initialize_tavus_avatar_method_exists(self):
        """Test that _initialize_tavus_avatar method exists."""
        from agent import DigitalHumanAgent
        
        agent = DigitalHumanAgent()
        
        assert hasattr(agent, '_initialize_tavus_avatar')
        assert callable(agent._initialize_tavus_avatar)
    
    def test_initialize_llm_method_exists(self):
        """Test that _initialize_llm method exists."""
        from agent import DigitalHumanAgent
        
        agent = DigitalHumanAgent()
        
        assert hasattr(agent, '_initialize_llm')
        assert callable(agent._initialize_llm)
    
    def test_initialize_tts_method_exists(self):
        """Test that _initialize_tts method exists."""
        from agent import DigitalHumanAgent
        
        agent = DigitalHumanAgent()
        
        assert hasattr(agent, '_initialize_tts')
        assert callable(agent._initialize_tts)


class TestAgentErrorMessages:
    """Tests for error message formatting.
    
    Requirements: 8.1 - Log detailed error information
    """
    
    def test_llm_error_message_format(self):
        """Test LLMError message formatting."""
        from agent import LLMError
        
        error = LLMError("API key invalid")
        assert "API key invalid" in str(error)
    
    def test_tts_error_message_format(self):
        """Test TTSError message formatting."""
        from agent import TTSError
        
        error = TTSError("Voice not found")
        assert "Voice not found" in str(error)
    
    def test_tavus_error_message_format(self):
        """Test TavusError message formatting."""
        from agent import TavusError
        
        error = TavusError("Replica ID invalid")
        assert "Replica ID invalid" in str(error)
    
    def test_agent_error_message_format(self):
        """Test AgentError message formatting."""
        from agent import AgentError
        
        error = AgentError("Session failed to start")
        assert "Session failed to start" in str(error)
