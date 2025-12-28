'use client';

import React from 'react';
import { cn } from '@/lib/utils';

/**
 * System states for the digital human interface
 * Maps to Requirements 9.1: distinct visual states
 */
export type SystemState =
  | 'connecting'
  | 'connected'
  | 'listening'
  | 'processing'
  | 'speaking'
  | 'error';

interface StateConfig {
  label: string;
  color: string;
  bgColor: string;
  pulseColor?: string;
}

const stateConfig: Record<SystemState, StateConfig> = {
  connecting: {
    label: 'Connecting...',
    color: 'text-yellow-600 dark:text-yellow-400',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    pulseColor: 'bg-yellow-500',
  },
  connected: {
    label: 'Connected',
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    pulseColor: 'bg-green-500',
  },
  listening: {
    label: 'Listening',
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    pulseColor: 'bg-blue-500',
  },
  processing: {
    label: 'Thinking...',
    color: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    pulseColor: 'bg-purple-500',
  },
  speaking: {
    label: 'Speaking',
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    pulseColor: 'bg-green-500',
  },
  error: {
    label: 'Error',
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    pulseColor: 'bg-red-500',
  },
};

interface StateIndicatorProps {
  state: SystemState;
  className?: string;
}

/**
 * StateIndicator component displays the current system state
 * with appropriate visual feedback.
 *
 * Requirements: 9.1, 9.3, 5.4
 * - Displays distinct visual states
 * - Updates UI within 100ms (handled by React state)
 * - Shows speaking indicator when avatar is active
 */
export function StateIndicator({ state, className }: StateIndicatorProps) {
  const config = stateConfig[state];
  const isAnimated = state === 'connecting' || state === 'processing' || state === 'speaking';

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-all duration-100',
        config.bgColor,
        config.color,
        className
      )}
      role="status"
      aria-live="polite"
    >
      {/* Status dot with optional pulse animation */}
      <span className="relative flex h-2 w-2">
        {isAnimated && (
          <span
            className={cn(
              'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
              config.pulseColor
            )}
          />
        )}
        <span className={cn('relative inline-flex h-2 w-2 rounded-full', config.pulseColor)} />
      </span>

      {/* State label */}
      <span>{config.label}</span>
    </div>
  );
}

/**
 * Maps LiveKit agent state to our SystemState
 * LiveKit states: 'disconnected' | 'connecting' | 'initializing' | 'listening' | 'thinking' | 'speaking'
 */
export function mapAgentStateToSystemState(
  agentState: string | undefined,
  isConnected: boolean,
  hasError: boolean
): SystemState {
  if (hasError) return 'error';
  if (!isConnected) return 'connecting';

  switch (agentState) {
    case 'speaking':
      return 'speaking';
    case 'thinking':
      return 'processing';
    case 'listening':
      return 'listening';
    case 'initializing':
    case 'connecting':
      return 'connecting';
    default:
      return isConnected ? 'connected' : 'connecting';
  }
}
