import { NextRequest, NextResponse } from 'next/server';
import { AccessToken, type VideoGrant } from 'livekit-server-sdk';

interface TokenRequest {
  roomName: string;
  participantName: string;
}

interface TokenResponse {
  token: string;
  serverUrl: string;
}

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

// Don't cache the results
export const revalidate = 0;

export async function POST(req: NextRequest) {
  try {
    // Validate environment variables
    if (!LIVEKIT_URL) {
      return NextResponse.json({ error: 'LIVEKIT_URL is not configured' }, { status: 500 });
    }
    if (!API_KEY) {
      return NextResponse.json({ error: 'LIVEKIT_API_KEY is not configured' }, { status: 500 });
    }
    if (!API_SECRET) {
      return NextResponse.json({ error: 'LIVEKIT_API_SECRET is not configured' }, { status: 500 });
    }

    // Parse and validate request body
    let body: TokenRequest;
    try {
      body = await req.json();
    } catch {
      return NextResponse.json({ error: 'Invalid JSON in request body' }, { status: 400 });
    }

    const { roomName, participantName } = body;

    // Validate required parameters
    if (!roomName || typeof roomName !== 'string' || !roomName.trim()) {
      return NextResponse.json(
        { error: 'roomName is required and must be a non-empty string' },
        { status: 400 }
      );
    }

    if (!participantName || typeof participantName !== 'string' || !participantName.trim()) {
      return NextResponse.json(
        { error: 'participantName is required and must be a non-empty string' },
        { status: 400 }
      );
    }

    // Generate a unique participant identity
    const participantIdentity = `${participantName.trim()}_${Date.now()}`;

    // Create access token
    const token = await createAccessToken(
      participantIdentity,
      participantName.trim(),
      roomName.trim()
    );

    const response: TokenResponse = {
      token,
      serverUrl: LIVEKIT_URL,
    };

    return NextResponse.json(response, {
      headers: {
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    console.error('Token generation error:', error);
    return NextResponse.json({ error: 'Failed to generate token' }, { status: 500 });
  }
}

async function createAccessToken(
  identity: string,
  name: string,
  roomName: string
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    identity,
    name,
    ttl: '15m',
  });

  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };

  at.addGrant(grant);

  return at.toJwt();
}
