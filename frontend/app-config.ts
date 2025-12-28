export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  // for LiveKit Cloud Sandbox
  sandboxId?: string;
  agentName?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Digital Human',
  pageTitle: 'Digital Human Assistant',
  pageDescription: 'Talk to our AI-powered digital human',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#6366f1',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#818cf8',
  startButtonText: 'Start Conversation',

  // for LiveKit Cloud Sandbox
  sandboxId: undefined,
  agentName: undefined,
};
