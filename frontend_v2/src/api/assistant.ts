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

export interface AssistantStreamEvent {
  event: 'plan' | 'tool' | 'answer_delta' | 'done' | 'error';
  data: {
    id?: string;
    tool_name?: string;
    label?: string;
    status?: 'running' | 'completed' | 'failed';
    detail?: string;
    delta?: string;
    actions?: AssistantChatResponse['actions'];
    message?: string;
  };
}

function buildAssistantStreamUrl() {
  const base = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
  return new URL(`${base}/assistant/chat/stream`, window.location.origin).toString();
}

export async function streamWorkbenchAssistant(
  data: {
    content: string;
    page_context?: string;
    language?: string;
  },
  onEvent: (event: AssistantStreamEvent) => void,
  signal?: AbortSignal,
) {
  const response = await fetch(buildAssistantStreamUrl(), {
    method: 'POST',
    headers: {
      Accept: 'text/event-stream',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
    signal,
  });
  if (!response.ok) {
    let message = `智能助手请求失败（HTTP ${response.status}）`;
    try {
      const payload = await response.json();
      message = payload?.detail || payload?.message || message;
    } catch {
      // Keep the HTTP status when the server did not return JSON.
    }
    throw new Error(message);
  }
  if (!response.body) {
    throw new Error('浏览器不支持读取智能助手流式响应');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let eventName = '';
  let eventData: string[] = [];

  const dispatch = () => {
    if (!eventName || eventData.length === 0) {
      eventName = '';
      eventData = [];
      return;
    }
    const currentEventName = eventName;
    const rawData = eventData.join('\n');
    eventName = '';
    eventData = [];
    if (!rawData) return;
    try {
      onEvent({ event: currentEventName as AssistantStreamEvent['event'], data: JSON.parse(rawData) });
    } catch {
      throw new Error('智能助手返回了无法解析的事件');
    }
  };

  const consume = (chunk: string) => {
    buffer += chunk.replace(/\r\n/g, '\n');
    const records = buffer.split('\n\n');
    buffer = records.pop() || '';
    for (const record of records) {
      for (const line of record.split('\n')) {
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          eventData.push(line.slice(5).trimStart());
        }
      }
      dispatch();
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    consume(decoder.decode(value, { stream: true }));
  }
  consume(decoder.decode());
  if (buffer.trim()) {
    consume('\n\n');
  }
}
