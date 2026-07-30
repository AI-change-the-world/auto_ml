import apiClient from './client';
import type {
  AssistantChatResponse,
  AssistantConfig,
  AssistantConfigUpdateRequest,
  Result,
} from '../types';

export async function getAssistantConfig() {
  const res = await apiClient.get<Result<AssistantConfig>>('/assistant/config');
  return res.data.data;
}

export async function updateAssistantConfig(data: AssistantConfigUpdateRequest) {
  const res = await apiClient.put<Result<AssistantConfig>>('/assistant/config', data);
  return res.data.data;
}

export async function askWorkbenchAssistant(data: {
  content: string;
  page_context?: string;
  language?: string;
}) {
  const res = await apiClient.post<Result<AssistantChatResponse>>('/assistant/chat', data);
  return res.data.data;
}
