'use client';

import React from 'react';
import { ArrowClockwise, WarningCircle } from '@phosphor-icons/react';
import { Button } from '@/components/livekit/button';
import { cn } from '@/lib/utils';

interface ConnectionErrorProps {
  /** Error message to display */
  errorMessage: string | null;
  /** Current retry attempt number */
  retryCount: number;
  /** Maximum retry attempts allowed */
  maxRetries?: number;
  /** Whether max retries have been reached */
  maxRetriesReached: boolean;
  /** Whether currently retrying */
  isRetrying: boolean;
  /** Callback to trigger manual retry */
  onRetry: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * ConnectionError component displays connection error states
 * with retry functionality.
 *
 * Requirements:
 * - 1.3: Display error message and offer retry option
 * - 8.2: Display disconnection message
 * - 8.3: Display user-friendly error message
 * - 8.4: Prompt user to refresh after 3 failed attempts
 */
export function ConnectionError({
  errorMessage,
  retryCount,
  maxRetries = 3,
  maxRetriesReached,
  isRetrying,
  onRetry,
  className,
}: ConnectionErrorProps) {
  // Don't render if no error
  if (!errorMessage && !maxRetriesReached && !isRetrying) {
    return null;
  }

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4 rounded-lg border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-950/30',
        className
      )}
      role="alert"
      aria-live="assertive"
    >
      <WarningCircle weight="fill" className="h-12 w-12 text-red-500 dark:text-red-400" />

      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-red-700 dark:text-red-300">
          {maxRetriesReached ? 'Connection Failed' : 'Connection Error'}
        </h3>

        <p className="text-sm text-red-600 dark:text-red-400">
          {maxRetriesReached
            ? 'Unable to establish connection after multiple attempts.'
            : errorMessage || 'An error occurred while connecting.'}
        </p>

        {isRetrying && (
          <p className="text-sm text-red-500 dark:text-red-400">
            Retrying... ({retryCount}/{maxRetries})
          </p>
        )}
      </div>

      {maxRetriesReached ? (
        <div className="flex flex-col gap-2">
          <Button
            variant="primary"
            size="default"
            onClick={() => window.location.reload()}
            className="gap-2"
          >
            <ArrowClockwise weight="bold" className="h-4 w-4" />
            Refresh Page
          </Button>
          <p className="text-xs text-red-500 dark:text-red-400">
            Please refresh the page to try again
          </p>
        </div>
      ) : (
        <Button
          variant="secondary"
          size="default"
          onClick={onRetry}
          disabled={isRetrying}
          className="gap-2"
        >
          <ArrowClockwise weight="bold" className={cn('h-4 w-4', isRetrying && 'animate-spin')} />
          {isRetrying ? 'Retrying...' : 'Retry Connection'}
        </Button>
      )}
    </div>
  );
}
