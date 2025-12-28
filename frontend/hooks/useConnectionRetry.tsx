'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { ConnectionState, DisconnectReason, RoomEvent } from 'livekit-client';
import { useSessionContext } from '@livekit/components-react';
import { toastAlert } from '@/components/livekit/alert-toast';

/**
 * Connection retry configuration
 * Requirements: 8.4 - Retry limit of 3 attempts
 */
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 2000; // 2 seconds between retries

export interface ConnectionRetryState {
    /** Current retry attempt (0 = initial, 1-3 = retry attempts) */
    retryCount: number;
    /** Whether we're currently in a retry cycle */
    isRetrying: boolean;
    /** Whether max retries have been exhausted */
    maxRetriesReached: boolean;
    /** Last error message */
    lastError: string | null;
}

export interface UseConnectionRetryReturn extends ConnectionRetryState {
    /** Manually trigger a retry */
    retry: () => void;
    /** Reset retry state (e.g., after successful connection) */
    reset: () => void;
}

/**
 * Hook to manage connection retry logic with a 3-attempt limit.
 *
 * Requirements:
 * - 1.3: Display error message and offer retry option
 * - 8.2: Display disconnection message and attempt reconnection
 * - 8.3: Display user-friendly error message
 * - 8.4: Stop retrying after 3 attempts and prompt user to refresh
 */
export function useConnectionRetry(): UseConnectionRetryReturn {
    const { isConnected, start, room } = useSessionContext();

    const [state, setState] = useState<ConnectionRetryState>({
        retryCount: 0,
        isRetrying: false,
        maxRetriesReached: false,
        lastError: null,
    });

    const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const wasConnectedRef = useRef(false);
    const isRetryingRef = useRef(false);
    const userInitiatedDisconnectRef = useRef(false);

    // Clear any pending retry timeout
    const clearRetryTimeout = useCallback(() => {
        if (retryTimeoutRef.current) {
            clearTimeout(retryTimeoutRef.current);
            retryTimeoutRef.current = null;
        }
    }, []);

    // Reset retry state
    const reset = useCallback(() => {
        clearRetryTimeout();
        isRetryingRef.current = false;
        userInitiatedDisconnectRef.current = false;
        setState({
            retryCount: 0,
            isRetrying: false,
            maxRetriesReached: false,
            lastError: null,
        });
    }, [clearRetryTimeout]);

    // Attempt to reconnect
    const attemptReconnect = useCallback(async () => {
        if (isRetryingRef.current) return;

        setState((prev) => {
            const newRetryCount = prev.retryCount + 1;

            if (newRetryCount > MAX_RETRY_ATTEMPTS) {
                return {
                    ...prev,
                    isRetrying: false,
                    maxRetriesReached: true,
                };
            }

            return {
                ...prev,
                retryCount: newRetryCount,
                isRetrying: true,
                maxRetriesReached: false,
            };
        });

        isRetryingRef.current = true;

        try {
            await start();
            // Success - will be handled by isConnected effect
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Connection failed';
            setState((prev) => ({
                ...prev,
                lastError: errorMessage,
                isRetrying: false,
            }));
            isRetryingRef.current = false;

            // Check if we should retry again
            setState((prev) => {
                if (prev.retryCount < MAX_RETRY_ATTEMPTS) {
                    // Schedule another retry
                    clearRetryTimeout();
                    retryTimeoutRef.current = setTimeout(() => {
                        attemptReconnect();
                    }, RETRY_DELAY_MS);
                } else {
                    // Max retries reached
                    toastAlert({
                        title: 'Connection failed',
                        description:
                            'Unable to connect after 3 attempts. Please refresh the page to try again.',
                    });
                    return {
                        ...prev,
                        maxRetriesReached: true,
                        isRetrying: false,
                    };
                }
                return prev;
            });
        }
    }, [start, clearRetryTimeout]);

    // Manual retry function
    const retry = useCallback(() => {
        if (state.maxRetriesReached) {
            // Reset and try again from scratch
            reset();
        }
        attemptReconnect();
    }, [state.maxRetriesReached, reset, attemptReconnect]);

    // Track connection state changes
    useEffect(() => {
        if (isConnected) {
            // Successfully connected - reset retry state
            wasConnectedRef.current = true;
            isRetryingRef.current = false;
            reset();
        }
    }, [isConnected, reset]);

    // Listen for room disconnection events
    useEffect(() => {
        if (!room) return;

        const handleDisconnected = (reason?: DisconnectReason) => {
            // Skip reconnection for user-initiated disconnections
            if (reason === DisconnectReason.CLIENT_INITIATED) {
                userInitiatedDisconnectRef.current = true;
                wasConnectedRef.current = false;
                clearRetryTimeout();
                return;
            }

            // Only handle unexpected disconnections (not user-initiated)
            if (!wasConnectedRef.current || userInitiatedDisconnectRef.current) return;

            const errorMessage =
                reason !== undefined
                    ? `Disconnected: ${DisconnectReason[reason]}`
                    : 'Connection lost unexpectedly';

            setState((prev) => ({
                ...prev,
                lastError: errorMessage,
            }));

            if (state.retryCount < MAX_RETRY_ATTEMPTS && !state.maxRetriesReached) {
                toastAlert({
                    title: 'Connection lost',
                    description: `Attempting to reconnect... (${state.retryCount + 1}/${MAX_RETRY_ATTEMPTS})`,
                });

                // Schedule retry
                clearRetryTimeout();
                retryTimeoutRef.current = setTimeout(() => {
                    attemptReconnect();
                }, RETRY_DELAY_MS);
            }
        };

        const handleConnectionStateChanged = (connectionState: ConnectionState) => {
            // Don't trigger reconnect for user-initiated disconnections
            if (connectionState === ConnectionState.Disconnected &&
                wasConnectedRef.current &&
                !userInitiatedDisconnectRef.current) {
                handleDisconnected(undefined);
            }
        };

        room.on(RoomEvent.Disconnected, handleDisconnected);
        room.on(RoomEvent.ConnectionStateChanged, handleConnectionStateChanged);

        return () => {
            room.off(RoomEvent.Disconnected, handleDisconnected);
            room.off(RoomEvent.ConnectionStateChanged, handleConnectionStateChanged);
        };
    }, [room, state.retryCount, state.maxRetriesReached, clearRetryTimeout, attemptReconnect]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            clearRetryTimeout();
        };
    }, [clearRetryTimeout]);

    return {
        ...state,
        retry,
        reset,
    };
}
