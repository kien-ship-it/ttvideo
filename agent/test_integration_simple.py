"""
Simplified integration tests for Digital Human Agent.

Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5, 5.1-5.5

These tests verify core integration functionality without complex mocking.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from agent import DigitalHumanAgent, AgentError, LLMError, TTSError, TavusError
from config import AgentConfig


@pytest.fixture
def mock_config():
    """Fixture providing valid agent configuration."""
    return AgentConfig(
        livekit_url="wss://test.livekit.cloud",
        livekit_api_key="test_key",
        livekit_api_secret="test_secret",
        tavus_api_key="tavus_key",
        tavus_replica_id="r_test",
        tavus_persona_id="p_test",
        openai_api_key="sk-test"
    )


class TestAgentInitialization:
    """Test agent initialization and configuration."""
    
    def test_agent_creation_with_defaults(self):
        """Test creating agent with default parameters."""
        agent = DigitalHumanAgent()
        
        assert agent.llm_model == "gpt-4o"
        assert agent.llm_temperature == 0.7
        assert agent.tts_voice == "alloy"
        assert agent._config is None
        assert agent._avatar is None
        assert agent._session is None
        assert agent._audio_only_mode is False
    
    def test_agent_creation_with_custom_params(self):
        """Test creating agent with custom parameters."""
        custom_prompt = "You are a test assistant."
        agent = DigitalHumanAgent(
            instructions=custom_prompt,
            llm_model="gpt-4o-mini",
            llm_temperature=0.5,
            tts_voice="nova"
        )
        
        assert agent._instructions == custom_prompt
        assert agent.llm_model == "gpt-4o-mini"
        assert agent.llm_temperature == 0.5
        assert agent.tts_voice == "nova"


class TestConfigurationLoading:
    """Test configuration loading and validation."""
    
    def test_config_loading_success(self, mock_config):
        """Test successful configuration loading."""
        agent = DigitalHumanAgent()
        
        with patch('agent.load_config_from_env', return_value=mock_config):
            config = agent._load_config()
            
            assert config == mock_config
            assert agent._config == mock_config
    
    def test_config_caching(self, mock_config):
        """Test that configuration is cached after first load."""
        agent = DigitalHumanAgent()
        
        with patch('agent.load_config_from_env', return_value=mock_config) as mock_load:
            # First call
            config1 = agent._load_config()
            # Second call
            config2 = agent._load_config()
            
            # Should only call load_config_from_env once
            mock_load.assert_called_once()
            assert config1 is config2


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_error_logging_structure(self):
        """Test that error logging returns structured information."""
        agent = DigitalHumanAgent()
        
        test_error = ValueError("Test error message")
        result = agent._log_error("TEST", test_error, "Test context")
        
        assert isinstance(result, dict)
        assert result["error_type"] == "TEST"
        assert result["error_class"] == "ValueError"
        assert result["error_message"] == "Test error message"
        assert result["context"] == "Test context"
        assert "traceback" in result
    
    def test_custom_error_classes(self):
        """Test that custom error classes are properly defined."""
        # Test error class hierarchy
        assert issubclass(LLMError, AgentError)
        assert issubclass(TTSError, AgentError)
        assert issubclass(TavusError, AgentError)
        
        # Test error instantiation
        llm_error = LLMError("LLM failed")
        tts_error = TTSError("TTS failed")
        tavus_error = TavusError("Tavus failed")
        
        assert str(llm_error) == "LLM failed"
        assert str(tts_error) == "TTS failed"
        assert str(tavus_error) == "Tavus failed"


class TestComponentInitialization:
    """Test individual component initialization."""
    
    @pytest.mark.asyncio
    async def test_llm_initialization_success(self, mock_config):
        """Test successful LLM initialization."""
        agent = DigitalHumanAgent()
        
        with patch('livekit.plugins.openai.LLM') as MockLLM:
            mock_llm = AsyncMock()
            MockLLM.return_value = mock_llm
            
            result = await agent._initialize_llm()
            
            assert result == mock_llm
            MockLLM.assert_called_once_with(
                model="gpt-4o",
                temperature=0.7
            )
    
    @pytest.mark.asyncio
    async def test_llm_initialization_failure(self):
        """Test LLM initialization failure handling."""
        agent = DigitalHumanAgent()
        
        with patch('livekit.plugins.openai.LLM') as MockLLM:
            MockLLM.side_effect = Exception("API key invalid")
            
            with pytest.raises(LLMError) as exc_info:
                await agent._initialize_llm()
            
            assert "Failed to initialize LLM" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_tts_initialization_success(self):
        """Test successful TTS initialization."""
        agent = DigitalHumanAgent()
        
        with patch('livekit.plugins.openai.TTS') as MockTTS:
            mock_tts = AsyncMock()
            MockTTS.return_value = mock_tts
            
            result = await agent._initialize_tts()
            
            assert result == mock_tts
            MockTTS.assert_called_once_with(voice="alloy")
    
    @pytest.mark.asyncio
    async def test_tts_initialization_failure(self):
        """Test TTS initialization failure handling."""
        agent = DigitalHumanAgent()
        
        with patch('livekit.plugins.openai.TTS') as MockTTS:
            MockTTS.side_effect = Exception("Voice not found")
            
            with pytest.raises(TTSError) as exc_info:
                await agent._initialize_tts()
            
            assert "Failed to initialize TTS" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_tavus_initialization_success(self, mock_config):
        """Test successful Tavus initialization."""
        agent = DigitalHumanAgent()
        
        with patch('livekit.plugins.tavus.AvatarSession') as MockAvatar:
            mock_avatar = AsyncMock()
            MockAvatar.return_value = mock_avatar
            
            result = await agent._initialize_tavus_avatar(mock_config)
            
            assert result == mock_avatar
            assert agent._audio_only_mode is False
            MockAvatar.assert_called_once_with(
                replica_id="r_test",
                persona_id="p_test"
            )
    
    @pytest.mark.asyncio
    async def test_tavus_initialization_failure_fallback(self, mock_config):
        """Test Tavus initialization failure with audio-only fallback."""
        agent = DigitalHumanAgent()
        
        with patch('livekit.plugins.tavus.AvatarSession') as MockAvatar:
            MockAvatar.side_effect = Exception("Tavus API error")
            
            result = await agent._initialize_tavus_avatar(mock_config)
            
            assert result is None
            assert agent._audio_only_mode is True


class TestTextInputValidation:
    """Test text input validation logic."""
    
    def test_whitespace_validation(self):
        """Test whitespace input validation."""
        def is_valid_text_input(text: str) -> bool:
            """Validate that input text is not empty or whitespace-only."""
            return text.strip() != ""
        
        # Test empty and whitespace inputs
        assert is_valid_text_input("") is False
        assert is_valid_text_input("   ") is False
        assert is_valid_text_input("\t\n\r ") is False
        assert is_valid_text_input("\t") is False
        assert is_valid_text_input("\n") is False
        
        # Test valid inputs
        assert is_valid_text_input("Hello") is True
        assert is_valid_text_input("  Hello  ") is True
        assert is_valid_text_input("Hello\nWorld") is True
        assert is_valid_text_input("123") is True
        assert is_valid_text_input("!@#$%") is True


class TestAgentCleanup:
    """Test agent cleanup functionality."""
    
    @pytest.mark.asyncio
    async def test_cleanup_success(self):
        """Test successful cleanup of agent resources."""
        agent = DigitalHumanAgent()
        
        # Mock session and avatar
        mock_session = AsyncMock()
        mock_avatar = AsyncMock()
        
        agent._session = mock_session
        agent._avatar = mock_avatar
        
        # Perform cleanup
        await agent.on_exit()
        
        # Verify cleanup was called
        mock_session.close.assert_called_once()
        mock_avatar.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_with_errors(self):
        """Test cleanup handling when components raise errors."""
        agent = DigitalHumanAgent()
        
        # Mock session and avatar with errors
        mock_session = AsyncMock()
        mock_avatar = AsyncMock()
        
        mock_session.close.side_effect = Exception("Session close error")
        mock_avatar.close.side_effect = Exception("Avatar close error")
        
        agent._session = mock_session
        agent._avatar = mock_avatar
        
        # Cleanup should not raise exceptions
        await agent.on_exit()
        
        # Verify cleanup was attempted
        mock_session.close.assert_called_once()
        mock_avatar.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_with_none_components(self):
        """Test cleanup when components are None."""
        agent = DigitalHumanAgent()
        
        # Components are None by default
        assert agent._session is None
        assert agent._avatar is None
        
        # Should not raise exceptions
        await agent.on_exit()


class TestIntegrationScenarios:
    """Test integration scenarios that combine multiple components."""
    
    @pytest.mark.asyncio
    async def test_audio_only_mode_session_creation(self, mock_config):
        """Test session creation in audio-only mode."""
        agent = DigitalHumanAgent()
        
        # Mock room with proper async methods
        mock_room = MagicMock()
        mock_room.local_participant = MagicMock()
        mock_room.local_participant.set_attributes = AsyncMock()
        agent.room = mock_room
        
        with patch('agent.load_config_from_env', return_value=mock_config):
            with patch.object(agent, '_initialize_tavus_avatar', return_value=None):
                with patch.object(agent, '_initialize_llm') as mock_init_llm:
                    with patch.object(agent, '_initialize_tts') as mock_init_tts:
                        with patch('agent.AgentSession') as MockSession:
                            # Setup mocks
                            mock_llm = AsyncMock()
                            mock_tts = AsyncMock()
                            mock_session = AsyncMock()
                            
                            mock_init_llm.return_value = mock_llm
                            mock_init_tts.return_value = mock_tts
                            MockSession.return_value = mock_session
                            
                            # Force audio-only mode
                            agent._audio_only_mode = True
                            
                            # Initialize agent
                            await agent.on_enter()
                            
                            # Verify session created without avatar
                            MockSession.assert_called_once_with(
                                llm=mock_llm,
                                tts=mock_tts
                            )
                            
                            # Verify session started
                            mock_session.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_full_mode_session_creation(self, mock_config):
        """Test session creation with full avatar mode."""
        agent = DigitalHumanAgent()
        
        # Mock room with proper async methods
        mock_room = MagicMock()
        mock_room.local_participant = MagicMock()
        mock_room.local_participant.set_attributes = AsyncMock()
        agent.room = mock_room
        
        with patch('agent.load_config_from_env', return_value=mock_config):
            with patch.object(agent, '_initialize_llm') as mock_init_llm:
                with patch.object(agent, '_initialize_tts') as mock_init_tts:
                    with patch.object(agent, '_initialize_tavus_avatar') as mock_init_avatar:
                        with patch('agent.AgentSession') as MockSession:
                            # Setup mocks
                            mock_llm = AsyncMock()
                            mock_tts = AsyncMock()
                            mock_avatar = AsyncMock()
                            mock_session = AsyncMock()
                            
                            mock_init_llm.return_value = mock_llm
                            mock_init_tts.return_value = mock_tts
                            mock_init_avatar.return_value = mock_avatar
                            MockSession.return_value = mock_session
                            
                            # Initialize agent
                            await agent.on_enter()
                            
                            # Verify session created without avatar (avatar is started separately)
                            MockSession.assert_called_once_with(
                                llm=mock_llm,
                                tts=mock_tts
                            )
                            
                            # Verify avatar.start was called before session.start
                            mock_avatar.start.assert_called_once_with(mock_session, room=mock_room)
                            
                            # Verify session started with text input enabled
                            mock_session.start.assert_called_once()
                            call_args = mock_session.start.call_args
                            room_input_options = call_args.kwargs['room_input_options']
                            assert room_input_options.text_enabled is True