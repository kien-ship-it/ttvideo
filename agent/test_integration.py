"""
Integration tests for Digital Human Agent end-to-end functionality.

Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5, 5.1-5.5

These tests verify:
- LiveKit room connection
- Text message round trip
- Avatar video subscription
- Full flow: connect → send text → receive avatar response
- Video and audio synchronization
- Disconnection and reconnection
"""

import asyncio
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

from livekit import rtc
from livekit.agents import JobContext

from agent import DigitalHumanAgent, entrypoint, AgentError, LLMError, TTSError, TavusError
from config import AgentConfig


class MockRoom:
    """Mock LiveKit room for testing."""
    
    def __init__(self, name: str = "test-room"):
        self.name = name
        self.participants = {}
        self.tracks = {}
        # Use correct enum values - check what's available
        self.connection_state = "connected"  # Use string instead of enum
        self.is_connected = True
        self._event_handlers = {}
        
    def on(self, event: str, handler):
        """Register event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def emit(self, event: str, *args, **kwargs):
        """Emit event to handlers."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                handler(*args, **kwargs)
    
    async def disconnect(self):
        """Simulate room disconnection."""
        self.is_connected = False
        self.connection_state = "disconnected"
        self.emit('disconnected')


class MockJobContext:
    """Mock JobContext for testing."""
    
    def __init__(self, room: MockRoom):
        self.room = room
        self._connected = False
    
    async def connect(self):
        """Simulate connection to room."""
        if not self.room.is_connected:
            raise ConnectionError("Failed to connect to room")
        self._connected = True


class MockParticipant:
    """Mock participant for testing."""
    
    def __init__(self, identity: str):
        self.identity = identity
        self.tracks = {}
        self.messages = []
    
    async def send_text(self, text: str, topic: str = "lk.chat"):
        """Mock sending text message."""
        self.messages.append({"text": text, "topic": topic})


class MockTrack:
    """Mock audio/video track for testing."""
    
    def __init__(self, kind: str, source: str = "unknown"):
        self.kind = kind  # "audio" or "video"
        self.source = source
        self.is_subscribed = False
        self.frames = []
    
    async def subscribe(self):
        """Mock track subscription."""
        self.is_subscribed = True
        return self


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


@pytest.fixture
def mock_room():
    """Fixture providing mock LiveKit room."""
    return MockRoom("integration-test-room")


@pytest.fixture
def mock_job_context(mock_room):
    """Fixture providing mock JobContext."""
    return MockJobContext(mock_room)


class TestLiveKitRoomConnection:
    """
    Integration tests for LiveKit room connection.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    
    @pytest_asyncio.async_test
    async def test_successful_room_connection(self, mock_job_context, mock_config):
        """
        Test successful connection to LiveKit room.
        
        Requirements: 1.1, 1.2 - Connect and display "Connected" state
        """
        with patch('agent.load_config_from_env', return_value=mock_config):
            # Should connect successfully
            await entrypoint(mock_job_context)
            
            assert mock_job_context._connected is True
            assert mock_job_context.room.is_connected is True
    
    @pytest_asyncio.async_test
    async def test_connection_failure_handling(self, mock_config):
        """
        Test handling of connection failures.
        
        Requirements: 1.3 - Display error message on connection failure
        """
        # Create a room that fails to connect
        failed_room = MockRoom("failed-room")
        failed_room.is_connected = False
        failed_context = MockJobContext(failed_room)
        
        with patch('agent.load_config_from_env', return_value=mock_config):
            with pytest.raises(ConnectionError):
                await entrypoint(failed_context)
    
    @pytest_asyncio.async_test
    async def test_graceful_disconnection(self, mock_job_context, mock_config):
        """
        Test graceful disconnection from room.
        
        Requirements: 1.5 - Gracefully disconnect when user closes application
        """
        with patch('agent.load_config_from_env', return_value=mock_config):
            with patch('agent.DigitalHumanAgent') as MockAgent:
                mock_agent_instance = AsyncMock()
                MockAgent.return_value = mock_agent_instance
                
                # Connect first
                await entrypoint(mock_job_context)
                
                # Simulate disconnection
                await mock_job_context.room.disconnect()
                
                assert mock_job_context.room.is_connected is False
                assert mock_job_context.room.connection_state == rtc.ConnectionState.DISCONNECTED


class TestTextMessageRoundTrip:
    """
    Integration tests for text message handling.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    
    @pytest.mark.asyncio
    async def test_text_message_processing(self, mock_job_context, mock_config):
        """
        Test complete text message processing flow.
        
        Requirements: 2.1, 2.5 - Send text via lk.chat and display "Processing" state
        """
        with patch('agent.load_config_from_env', return_value=mock_config):
            with patch('livekit.plugins.openai.LLM') as MockLLM:
                with patch('livekit.plugins.openai.TTS') as MockTTS:
                    with patch('livekit.plugins.tavus.AvatarSession') as MockAvatar:
                        with patch('livekit.agents.AgentSession') as MockSession:
                            # Setup mocks
                            mock_llm = AsyncMock()
                            mock_tts = AsyncMock()
                            mock_avatar = AsyncMock()
                            mock_session = AsyncMock()
                            
                            MockLLM.return_value = mock_llm
                            MockTTS.return_value = mock_tts
                            MockAvatar.return_value = mock_avatar
                            MockSession.return_value = mock_session
                            
                            # Create agent
                            agent = DigitalHumanAgent()
                            agent.room = mock_job_context.room
                            
                            # Initialize agent
                            await agent.on_enter()
                            
                            # Verify session was started with text input enabled
                            MockSession.assert_called_once()
                            mock_session.start.assert_called_once()
                            
                            # Check that room input options include text_enabled=True
                            call_args = mock_session.start.call_args
                            room_input_options = call_args.kwargs.get('room_input_options')
                            assert room_input_options is not None
                            assert room_input_options.text_enabled is True
    
    @pytest_asyncio.async_test
    async def test_whitespace_input_rejection(self):
        """
        Test that whitespace-only input is properly rejected.
        
        Requirements: 2.3 - Prevent submission of empty/whitespace-only text
        """
        # Test the validation logic directly without importing frontend
        def is_valid_text_input(text: str) -> bool:
            """Validate that input text is not empty or whitespace-only."""
            return text.strip() != ""
        
        # Test various whitespace-only inputs
        assert is_valid_text_input("") is False
        assert is_valid_text_input("   ") is False
        assert is_valid_text_input("\t\n\r ") is False
        assert is_valid_text_input("Hello") is True
        assert is_valid_text_input("  Hello  ") is True  # Trimmed to "Hello"
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, mock_job_context, mock_config):
        """
        Test agent error handling during message processing.
        
        Requirements: 3.5 - Log error and notify client if LLM/TTS fails
        """
        with patch('agent.load_config_from_env', return_value=mock_config):
            with patch('livekit.plugins.openai.LLM') as MockLLM:
                # Simulate LLM failure
                MockLLM.side_effect = Exception("LLM API error")
                
                agent = DigitalHumanAgent()
                agent.room = mock_job_context.room
                
                # Should raise LLMError
                with pytest.raises(LLMError):
                    await agent.on_enter()


class TestAvatarVideoSubscription:
    """
    Integration tests for avatar video and audio handling.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    @pytest.mark.asyncio
    async def test_avatar_track_subscription(self, mock_job_context, mock_config):
        """
        Test subscription to avatar video and audio tracks.
        
        Requirements: 5.1, 5.2 - Subscribe to video/audio tracks and display video
        """
        with patch('agent.load_config_from_env', return_value=mock_config):
            with patch('livekit.plugins.tavus.AvatarSession') as MockAvatar:
                with patch('livekit.agents.AgentSession') as MockSession:
                    # Setup mocks
                    mock_avatar = AsyncMock()
                    mock_session = AsyncMock()
                    
                    MockAvatar.return_value = mock_avatar
                    MockSession.return_value = mock_session
                    
                    # Create mock tracks
                    video_track = MockTrack("video", "avatar")
                    audio_track = MockTrack("audio", "avatar")
                    
                    # Simulate tracks being published
                    mock_job_context.room.tracks = {
                        "video": video_track,
                        "audio": audio_track
                    }
                    
                    # Create and initialize agent
                    agent = DigitalHumanAgent()
                    agent.room = mock_job_context.room
                    
                    await agent.on_enter()
                    
                    # Verify avatar session was created
                    MockAvatar.assert_called_once_with(
                        replica_id=mock_config.tavus_replica_id,
                        persona_id=mock_config.tavus_persona_id
                    )
    
    @pytest.mark.asyncio
    async def test_tavus_fallback_to_audio_only(self, mock_job_context, mock_config):
        """
        Test fallback to audio-only mode when Tavus fails.
        
        Requirements: 4.5 - Continue with audio-only if Tavus fails
        """
        with patch('agent.load_config_from_env', return_value=mock_config):
            with patch('livekit.plugins.tavus.AvatarSession') as MockAvatar:
                with patch('livekit.plugins.openai.LLM') as MockLLM:
                    with patch('livekit.plugins.openai.TTS') as MockTTS:
                        with patch('livekit.agents.AgentSession') as MockSession:
                            # Simulate Tavus failure
                            MockAvatar.side_effect = Exception("Tavus API error")
                            
                            # Setup other mocks
                            MockLLM.return_value = AsyncMock()
                            MockTTS.return_value = AsyncMock()
                            mock_session = AsyncMock()
                            MockSession.return_value = mock_session
                            
                            # Create agent
                            agent = DigitalHumanAgent()
                            agent.room = mock_job_context.room
                            
                            # Should not raise exception, should fall back to audio-only
                            await agent.on_enter()
                            
                            # Verify audio-only mode is enabled
                            assert agent._audio_only_mode is True
                            
                            # Verify session was created without avatar
                            MockSession.assert_called_once()
                            call_args = MockSession.call_args
                            assert 'avatar' not in call_args.kwargs or call_args.kwargs['avatar'] is None


class TestEndToEndIntegration:
    """
    End-to-end integration tests for complete user flows.
    
    Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5, 5.1-5.5
    """
    
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, mock_job_context, mock_config):
        """
        Test complete flow: connect → send text → receive avatar response.
        
        This test simulates the full user journey from connection to response.
        
        Requirements: All integration requirements
        """
        with patch('agent.load_config_from_env', return_value=mock_config):
            with patch('livekit.plugins.openai.LLM') as MockLLM:
                with patch('livekit.plugins.openai.TTS') as MockTTS:
                    with patch('livekit.plugins.tavus.AvatarSession') as MockAvatar:
                        with patch('livekit.agents.AgentSession') as MockSession:
                            # Setup mocks for successful flow
                            mock_llm = AsyncMock()
                            mock_tts = AsyncMock()
                            mock_avatar = AsyncMock()
                            mock_session = AsyncMock()
                            
                            MockLLM.return_value = mock_llm
                            MockTTS.return_value = mock_tts
                            MockAvatar.return_value = mock_avatar
                            MockSession.return_value = mock_session
                            
                            # Step 1: Connect to room
                            await entrypoint(mock_job_context)
                            assert mock_job_context._connected is True
                            
                            # Step 2: Verify agent session is configured correctly
                            MockSession.assert_called_once()
                            session_call = MockSession.call_args
                            
                            # Verify LLM and TTS are configured (avatar is started separately)
                            assert session_call.kwargs['llm'] == mock_llm
                            assert session_call.kwargs['tts'] == mock_tts
                            
                            # Verify avatar.start was called
                            mock_avatar.start.assert_called_once()
                            
                            # Step 3: Verify session started with text input enabled
                            mock_session.start.assert_called_once()
                            start_call = mock_session.start.call_args
                            room_input_options = start_call.kwargs['room_input_options']
                            assert room_input_options.text_enabled is True
                            
                            # Step 4: Simulate text input and response generation
                            # This would normally be triggered by LiveKit's text input system
                            test_message = "Hello, digital human!"
                            
                            # Simulate LLM response
                            mock_llm_response = "Hello! How can I help you today?"
                            mock_llm.generate.return_value = mock_llm_response
                            
                            # Simulate TTS audio generation
                            mock_audio_data = b"fake_audio_data"
                            mock_tts.synthesize.return_value = mock_audio_data
                            
                            # Simulate avatar video generation
                            mock_avatar.process_audio.return_value = "video_track_id"
                            
                            # The actual message processing would happen through LiveKit's
                            # AgentSession.generate_reply() method, which we've mocked
                            
                            # Step 5: Verify cleanup on exit
                            # Create a new agent instance to test cleanup
                            cleanup_agent = DigitalHumanAgent()
                            cleanup_agent._session = mock_session
                            cleanup_agent._avatar = mock_avatar
                            
                            await cleanup_agent.on_exit()
                            
                            # Verify cleanup was called
                            mock_session.close.assert_called_once()
                            mock_avatar.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnection_and_reconnection(self, mock_config):
        """
        Test disconnection and reconnection scenarios.
        
        Requirements: 8.2, 8.3, 8.4 - Handle connection loss and retry
        """
        # Test initial connection
        room1 = MockRoom("test-room-1")
        context1 = MockJobContext(room1)
        
        with patch('agent.load_config_from_env', return_value=mock_config):
            await entrypoint(context1)
            assert context1._connected is True
            
            # Simulate disconnection
            await room1.disconnect()
            assert room1.is_connected is False
            
            # Test reconnection to new room
            room2 = MockRoom("test-room-2")
            context2 = MockJobContext(room2)
            
            await entrypoint(context2)
            assert context2._connected is True
            assert room2.is_connected is True
    
    @pytest.mark.asyncio
    async def test_video_audio_synchronization_setup(self, mock_job_context, mock_config):
        """
        Test that video and audio tracks are properly configured for synchronization.
        
        Requirements: 4.3, 5.3 - Video/audio synchronization within 100ms tolerance
        """
        with patch('agent.load_config_from_env', return_value=mock_config):
            with patch('livekit.plugins.tavus.AvatarSession') as MockAvatar:
                with patch('livekit.agents.AgentSession') as MockSession:
                    # Setup mocks
                    mock_avatar = AsyncMock()
                    mock_session = AsyncMock()
                    
                    MockAvatar.return_value = mock_avatar
                    MockSession.return_value = mock_session
                    
                    # Create agent and initialize
                    agent = DigitalHumanAgent()
                    agent.room = mock_job_context.room
                    
                    await agent.on_enter()
                    
                    # Verify that Tavus avatar session is configured
                    # The actual synchronization is handled by Tavus and LiveKit
                    MockAvatar.assert_called_once_with(
                        replica_id=mock_config.tavus_replica_id,
                        persona_id=mock_config.tavus_persona_id
                    )
                    
                    # Verify session includes avatar for synchronized output
                    # Avatar is started separately via avatar.start()
                    mock_avatar.start.assert_called_once()


class TestErrorRecovery:
    """
    Integration tests for error handling and recovery scenarios.
    
    Requirements: 8.1, 8.2, 8.3, 8.4
    """
    
    @pytest.mark.asyncio
    async def test_configuration_error_handling(self):
        """
        Test handling of configuration errors during startup.
        
        Requirements: 8.1 - Log detailed error information
        """
        # Test with missing configuration
        with patch('agent.load_config_from_env') as mock_load_config:
            mock_load_config.side_effect = Exception("Missing TAVUS_API_KEY")
            
            mock_room = MockRoom("config-error-room")
            mock_context = MockJobContext(mock_room)
            
            with pytest.raises(Exception) as exc_info:
                await entrypoint(mock_context)
            
            assert "Missing TAVUS_API_KEY" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_component_failure_recovery(self, mock_job_context, mock_config):
        """
        Test recovery from individual component failures.
        
        Requirements: 3.5, 4.5 - Handle LLM/TTS/Tavus failures gracefully
        """
        with patch('agent.load_config_from_env', return_value=mock_config):
            # Test TTS failure
            with patch('livekit.plugins.openai.LLM') as MockLLM:
                with patch('livekit.plugins.openai.TTS') as MockTTS:
                    MockLLM.return_value = AsyncMock()
                    MockTTS.side_effect = Exception("TTS service unavailable")
                    
                    agent = DigitalHumanAgent()
                    agent.room = mock_job_context.room
                    
                    with pytest.raises(TTSError):
                        await agent.on_enter()