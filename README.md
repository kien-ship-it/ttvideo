# Real-Time Digital Human

A real-time interactive digital human application that enables natural conversations with a Tavus-powered avatar. Built with LiveKit for WebRTC infrastructure, OpenAI for LLM and TTS, and Tavus for lip-sync video rendering.

## Architecture

```
┌─────────────────┐     WebRTC      ┌─────────────────┐     Plugin      ┌─────────────────┐
│   Next.js       │◄───────────────►│  LiveKit Agent  │◄───────────────►│   Tavus         │
│   Frontend      │                 │  (Python)       │                 │  (Rendering)    │
│                 │                 │                 │                 │                 │
│  - Text Input   │  lk.chat topic  │  - LLM (OpenAI) │  Audio Stream   │  - Lip Sync     │
│  - Video Player │◄───────────────►│  - TTS (OpenAI) │◄───────────────►│  - Video Gen    │
│  - State UI     │                 │  - Tavus Plugin │                 │  - Phoenix-4    │
└─────────────────┘                 └─────────────────┘                 └─────────────────┘
```

## Features

- **Real-time conversation** with a digital avatar
- **Sub-3-second latency** through streaming processing
- **Lip-sync video** powered by Tavus Phoenix-4 model
- **Automatic fallback** to audio-only if video fails
- **Connection retry** with user-friendly error handling

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 15, React 19, TypeScript, TailwindCSS |
| Agent | Python, LiveKit Agents SDK |
| LLM | OpenAI GPT-4 |
| TTS | OpenAI TTS |
| Avatar | Tavus CVI |
| WebRTC | LiveKit |

## Project Structure

```
ttvideo/
├── frontend/          # Next.js frontend application
│   ├── app/           # Next.js app router
│   ├── components/    # React components
│   └── hooks/         # Custom React hooks
├── agent/             # Python LiveKit agent
│   ├── agent.py       # Main agent implementation
│   └── config.py      # Configuration management
└── README.md
```

## Prerequisites

- Node.js 18+
- Python 3.10+
- pnpm
- LiveKit Cloud account
- OpenAI API key
- Tavus API credentials

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ttvideo.git
cd ttvideo
```

### 2. Frontend Setup

```bash
cd frontend
pnpm install
cp .env.example .env.local
```

Edit `.env.local` with your LiveKit credentials:

```env
LIVEKIT_API_KEY=<your_api_key>
LIVEKIT_API_SECRET=<your_api_secret>
LIVEKIT_URL=wss://<project-subdomain>.livekit.cloud
```

### 3. Agent Setup

```bash
cd agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your API credentials:

```env
LIVEKIT_API_KEY=<your_api_key>
LIVEKIT_API_SECRET=<your_api_secret>
LIVEKIT_URL=wss://<project-subdomain>.livekit.cloud
OPENAI_API_KEY=<your_openai_api_key>
TAVUS_API_KEY=<your_tavus_api_key>
TAVUS_REPLICA_ID=<your_replica_id>
TAVUS_PERSONA_ID=<your_persona_id>
```

## Running the Application

### Start the Frontend

```bash
cd frontend
pnpm dev
```

The frontend will be available at `http://localhost:3000`.

### Start the Agent

```bash
cd agent
source venv/bin/activate
python agent.py dev
```

## Data Flow

1. User types text → Frontend validates and sends via LiveKit
2. Agent receives text → Processes with LLM → Generates audio via TTS
3. Audio forwarded to Tavus → Generates lip-sync video → Publishes to LiveKit
4. Frontend receives video/audio tracks → Displays speaking avatar

## Testing

### Frontend Tests

```bash
cd frontend
pnpm test
```

### Agent Tests

```bash
cd agent
pytest
```

## License

MIT
