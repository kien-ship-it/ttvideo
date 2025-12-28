import { beforeAll, vi } from 'vitest';

// Mock LiveKit client
vi.mock('livekit-client', () => ({
    Room: vi.fn(),
    RoomEvent: {
        Connected: 'connected',
        Disconnected: 'disconnected',
        TrackSubscribed: 'trackSubscribed',
        TrackUnsubscribed: 'trackUnsubscribed',
        ParticipantConnected: 'participantConnected',
        ParticipantDisconnected: 'participantDisconnected',
    },
    ConnectionState: {
        Connected: 'connected',
        Connecting: 'connecting',
        Disconnected: 'disconnected',
        Reconnecting: 'reconnecting',
    },
    TrackKind: {
        Audio: 'audio',
        Video: 'video',
    },
    TrackSource: {
        Camera: 'camera',
        Microphone: 'microphone',
        ScreenShare: 'screen_share',
        Unknown: 'unknown',
    },
}));

// Mock LiveKit components
vi.mock('@livekit/components-react', () => ({
    useLocalParticipant: vi.fn(),
    useRoom: vi.fn(),
    useParticipants: vi.fn(),
    useTracks: vi.fn(),
    VideoTrack: vi.fn(),
    AudioTrack: vi.fn(),
}));

// Mock Next.js router
vi.mock('next/navigation', () => ({
    useRouter: vi.fn(() => ({
        push: vi.fn(),
        replace: vi.fn(),
        back: vi.fn(),
    })),
    useSearchParams: vi.fn(() => new URLSearchParams()),
    usePathname: vi.fn(() => '/'),
}));

// Setup DOM environment
beforeAll(() => {
    // Mock window.matchMedia
    Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
            matches: false,
            media: query,
            onchange: null,
            addListener: vi.fn(),
            removeListener: vi.fn(),
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
            dispatchEvent: vi.fn(),
        })),
    });
});