export interface AssistantConfig {
  enabled: boolean;
  provider_display_name?: string | null;
  provider_kind?: string | null;
  base_url?: string | null;
  api_key_configured: boolean;
  model?: string | null;
  timeout_seconds?: number | null;
  temperature?: number | null;
  max_tokens?: number | null;
  system_prompt?: string | null;
}

export interface AssistantConfigUpdateRequest {
  enabled: boolean;
  base_url?: string;
  api_key?: string;
  model?: string;
  timeout_seconds: number;
  temperature: number;
  max_tokens: number;
  system_prompt?: string;
}

export interface AssistantAction {
  key: string;
  label: string;
  path: string;
}

export interface AssistantChatResponse {
  content: string;
  actions: AssistantAction[];
}
