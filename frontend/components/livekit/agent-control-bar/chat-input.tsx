import { useEffect, useRef, useState } from 'react';
import { motion } from 'motion/react';
import { PaperPlaneRightIcon, SpinnerIcon } from '@phosphor-icons/react/dist/ssr';
import { Button } from '@/components/livekit/button';

const MOTION_PROPS = {
  variants: {
    hidden: {
      height: 0,
      opacity: 0,
      marginBottom: 0,
    },
    visible: {
      height: 'auto',
      opacity: 1,
      marginBottom: 12,
    },
  },
  initial: 'hidden',
  transition: {
    duration: 0.3,
    ease: 'easeOut',
  },
};

/**
 * Validates that input text is not empty or whitespace-only.
 * Requirements: 2.3 - Reject whitespace-only input
 *
 * @param text - The input text to validate
 * @returns true if the text is valid (non-empty, non-whitespace), false otherwise
 */
export function isValidTextInput(text: string): boolean {
  return text.trim().length > 0;
}

interface ChatInputProps {
  chatOpen: boolean;
  isAgentAvailable?: boolean;
  /** Whether the agent is currently processing a request (thinking/speaking) */
  isAgentProcessing?: boolean;
  onSend?: (message: string) => void;
}

/**
 * ChatInput component for sending text messages to the digital human agent.
 *
 * Requirements:
 * - 2.1: Send text via LiveKit's sendText() to lk.chat topic
 * - 2.2: Clear input field after successful submission
 * - 2.3: Reject whitespace-only input
 * - 2.4: Disable input while processing
 * - 2.5: Display "Processing" state indicator (handled by parent via isAgentProcessing)
 */
export function ChatInput({
  chatOpen,
  isAgentAvailable = false,
  isAgentProcessing = false,
  onSend = async () => {},
}: ChatInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isSending, setIsSending] = useState(false);
  const [message, setMessage] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Requirement 2.3: Reject whitespace-only input
    if (!isValidTextInput(message)) {
      return;
    }

    try {
      setIsSending(true);
      // Requirement 2.1: Send text via LiveKit (handled by onSend callback)
      await onSend(message.trim());
      // Requirement 2.2: Clear input field after successful submission
      setMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  };

  // Requirement 2.3: Disable submit button for invalid input
  // Requirement 2.4: Disable input while processing (isSending or isAgentProcessing)
  const isInputDisabled = !chatOpen || isSending || isAgentProcessing;
  const isSubmitDisabled =
    isSending || isAgentProcessing || !isAgentAvailable || !isValidTextInput(message);

  useEffect(() => {
    // Refocus on input when chat opens and agent is available and not processing
    if (chatOpen && isAgentAvailable && !isAgentProcessing) {
      inputRef.current?.focus();
    }
  }, [chatOpen, isAgentAvailable, isAgentProcessing]);

  // Get placeholder text based on state
  const getPlaceholder = (): string => {
    if (isAgentProcessing) {
      return 'Waiting for response...';
    }
    if (!isAgentAvailable) {
      return 'Waiting for agent...';
    }
    return 'Type something...';
  };

  return (
    <motion.div
      inert={!chatOpen}
      {...MOTION_PROPS}
      animate={chatOpen ? 'visible' : 'hidden'}
      className="border-input/50 flex w-full items-start overflow-hidden border-b"
    >
      <form
        onSubmit={handleSubmit}
        className="mb-3 flex grow items-end gap-2 rounded-md pl-1 text-sm"
      >
        <input
          autoFocus
          ref={inputRef}
          type="text"
          value={message}
          disabled={isInputDisabled}
          placeholder={getPlaceholder()}
          onChange={(e) => setMessage(e.target.value)}
          className="h-8 flex-1 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Chat message input"
          aria-describedby={isAgentProcessing ? 'processing-hint' : undefined}
        />
        {isAgentProcessing && (
          <span id="processing-hint" className="sr-only">
            Agent is processing your previous message
          </span>
        )}
        <Button
          size="icon"
          type="submit"
          disabled={isSubmitDisabled}
          variant={isSubmitDisabled ? 'secondary' : 'primary'}
          title={isSending || isAgentProcessing ? 'Processing...' : 'Send'}
          className="self-start"
          aria-label={isSending || isAgentProcessing ? 'Processing message' : 'Send message'}
        >
          {isSending || isAgentProcessing ? (
            <SpinnerIcon className="animate-spin" weight="bold" />
          ) : (
            <PaperPlaneRightIcon weight="bold" />
          )}
        </Button>
      </form>
    </motion.div>
  );
}
