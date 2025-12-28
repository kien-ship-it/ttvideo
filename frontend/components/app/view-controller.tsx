'use client';

import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { ConnectionError } from '@/components/app/connection-error';
import { SessionView } from '@/components/app/session-view';
import { WelcomeView } from '@/components/app/welcome-view';
import { useConnectionRetry } from '@/hooks/useConnectionRetry';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(SessionView);
const MotionConnectionError = motion.create(ConnectionError);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

/**
 * ViewController manages the main view states including connection errors.
 *
 * Requirements:
 * - 1.3: Display error message and offer retry option
 * - 8.2: Display disconnection message and attempt reconnection
 * - 8.3: Display user-friendly error message
 * - 8.4: Stop retrying after 3 attempts and prompt user to refresh
 */
export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const connectionRetry = useConnectionRetry();

  // Show error view if max retries reached or there's an error while not connected
  const showError =
    connectionRetry.maxRetriesReached ||
    (connectionRetry.lastError && !isConnected && connectionRetry.retryCount > 0);

  return (
    <AnimatePresence mode="wait">
      {/* Connection error view */}
      {showError && !isConnected && (
        <MotionConnectionError
          key="connection-error"
          {...VIEW_MOTION_PROPS}
          errorMessage={connectionRetry.lastError}
          retryCount={connectionRetry.retryCount}
          maxRetriesReached={connectionRetry.maxRetriesReached}
          isRetrying={connectionRetry.isRetrying}
          onRetry={connectionRetry.retry}
          className="mx-4 max-w-md"
        />
      )}
      {/* Welcome view */}
      {!isConnected && !showError && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={start}
        />
      )}
      {/* Session view */}
      {isConnected && (
        <MotionSessionView key="session-view" {...VIEW_MOTION_PROPS} appConfig={appConfig} />
      )}
    </AnimatePresence>
  );
}
