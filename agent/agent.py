"""
Digital Human Agent - LiveKit Agent with Tavus Avatar Rendering.

This agent handles:
- LLM processing (OpenAI GPT-4o)
- TTS generation (OpenAI)
- Tavus avatar rendering for lip-sync video

Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 3.5, 4.5, 8.1
"""

import logging
import traceback

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import openai, tavus

from config import ConfigurationError, load_config_from_env

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("digital-human-agent")

# System prompt for the digital assistant persona
DEFAULT_SYSTEM_PROMPT = """You are a helpful and friendly digital assistant. 
You communicate clearly and concisely, providing accurate and useful information.
You maintain a professional yet approachable tone in all interactions.
When you don't know something, you honestly say so rather than making up information."""


class DigitalHumanAgent(Agent):
    """
    Digital Human Agent that processes user text input via LLM,
    generates speech via TTS, and renders video via Tavus.
    """
    
    def __init__(self, instructions: str = DEFAULT_SYSTEM_PROMPT):
        super().__init__(instructions=instructions)

    async def on_enter(self) -> None:
        """Called when the agent enters the session - generate initial greeting."""
        logger.info("Agent entered session, generating greeting...")
        self.session.generate_reply(
            instructions="Greet the user warmly and offer your assistance."
        )


async def entrypoint(ctx: JobContext) -> None:
    """
    Agent entrypoint - called when a job is dispatched to this worker.
    """
    logger.info(f"Agent job started for room: {ctx.room.name}")
    
    # Validate configuration
    try:
        config = load_config_from_env()
        logger.info("Configuration validated successfully")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # Connect to the room
    try:
        await ctx.connect()
        logger.info(f"Connected to room: {ctx.room.name}")
    except Exception as e:
        logger.error(f"Failed to connect to room: {e}")
        raise
    
    # Initialize components
    audio_only_mode = False
    
    # Create LLM (using gpt-4o-mini - more widely available)
    llm = openai.LLM(
        model="gpt-4",
        temperature=0.7,
    )
    logger.info("LLM initialized")
    
    # Create TTS
    tts = openai.TTS(voice="alloy")
    logger.info("TTS initialized")
    
    # Create AgentSession
    session = AgentSession(
        llm=llm,
        tts=tts,
    )
    
    # Create the agent
    agent = DigitalHumanAgent(instructions=DEFAULT_SYSTEM_PROMPT)
    
    # Initialize Tavus avatar (with fallback to audio-only)
    avatar = None
    try:
        logger.info("Initializing Tavus avatar...")
        avatar = tavus.AvatarSession(
            replica_id=config.tavus_replica_id,
            persona_id=config.tavus_persona_id,
        )
        logger.info(f"Tavus avatar created with replica_id={config.tavus_replica_id}")
        
    except Exception as e:
        logger.warning(f"Tavus avatar initialization failed, falling back to audio-only: {e}")
        audio_only_mode = True
    
    # Start the session with or without avatar
    try:
        if avatar and not audio_only_mode:
            # Start session with Tavus avatar for video
            await session.start(
                agent=agent,
                room=ctx.room,
                avatar=avatar,
                room_input_options=RoomInputOptions(text_enabled=True),
            )
            logger.info("AgentSession started with Tavus avatar (video mode)")
        else:
            # Start session without avatar (audio-only)
            await session.start(
                agent=agent,
                room=ctx.room,
                room_input_options=RoomInputOptions(text_enabled=True),
            )
            logger.info("AgentSession started in audio-only mode")
        
    except Exception as e:
        logger.error(f"Failed to start session: {e}\n{traceback.format_exc()}")
        raise


def prewarm(proc: JobProcess) -> None:
    """Prewarm function - validate configuration at startup."""
    logger.info("Prewarming agent process...")
    try:
        load_config_from_env()
        logger.info("Configuration validated during prewarm")
    except ConfigurationError as e:
        logger.warning(f"Configuration incomplete: {e}")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
