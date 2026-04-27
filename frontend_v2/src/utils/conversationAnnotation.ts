import { v4 as uuidv4 } from 'uuid';

export type ConversationAnnotationMode = 'llm' | 'mllm';
export type ConversationMessageRole = 'user' | 'assistant';
const CONVERSATION_ANNOTATION_SUFFIX = '.annotation.json';

export interface ConversationMessage {
  id: string;
  role: ConversationMessageRole;
  content: string;
}

export interface ConversationAnnotationEntry {
  systemPrompt: string;
  messages: ConversationMessage[];
}

interface StoredConversationMessage {
  role: ConversationMessageRole;
  content: string;
}

interface ConversationAnnotationDocument {
  version: 1;
  mode: ConversationAnnotationMode;
  system_prompt?: string;
  messages: StoredConversationMessage[];
}

export function buildConversationAnnotationFileName(fileName: string): string {
  return `${fileName}${CONVERSATION_ANNOTATION_SUFFIX}`;
}

export function parseConversationAnnotationFileName(fileName: string): string | null {
  const trimmed = fileName.trim();
  if (!trimmed.endsWith(CONVERSATION_ANNOTATION_SUFFIX)) {
    return null;
  }
  return trimmed.slice(0, -CONVERSATION_ANNOTATION_SUFFIX.length) || null;
}

export function createConversationMessage(
  role: ConversationMessageRole = 'user',
  content = '',
): ConversationMessage {
  return {
    id: uuidv4(),
    role,
    content,
  };
}

export function parseConversationAnnotationContent(
  content: string | null | undefined,
): ConversationAnnotationEntry {
  const text = content?.trim();
  if (!text) return createEmptyConversationAnnotationEntry();

  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) {
      return {
        systemPrompt: '',
        messages: normalizeConversationMessages(parsed),
      };
    }
    if (parsed && typeof parsed === 'object' && Array.isArray((parsed as ConversationAnnotationDocument).messages)) {
      return {
        systemPrompt: typeof (parsed as ConversationAnnotationDocument).system_prompt === 'string'
          ? (parsed as ConversationAnnotationDocument).system_prompt ?? ''
          : '',
        messages: normalizeConversationMessages((parsed as ConversationAnnotationDocument).messages),
      };
    }
  } catch {
    // ignore malformed legacy content
  }

  return createEmptyConversationAnnotationEntry();
}

export function serializeConversationAnnotationContent(
  mode: ConversationAnnotationMode,
  entry: ConversationAnnotationEntry,
): string {
  const normalized = normalizeConversationMessages(entry.messages);
  const payload: ConversationAnnotationDocument = {
    version: 1,
    mode,
    system_prompt: entry.systemPrompt.trim() || undefined,
    messages: normalized.map((item) => ({
      role: item.role,
      content: item.content,
    })),
  };
  return JSON.stringify(payload, null, 2);
}

export function createEmptyConversationAnnotationEntry(): ConversationAnnotationEntry {
  return {
    systemPrompt: '',
    messages: [],
  };
}

export function normalizeConversationMessages(values: unknown[]): ConversationMessage[] {
  const items: ConversationMessage[] = [];
  values.forEach((value) => {
    if (!value || typeof value !== 'object') return;
    const role = (value as StoredConversationMessage).role;
    const content = (value as StoredConversationMessage).content;
    if ((role !== 'user' && role !== 'assistant') || typeof content !== 'string') return;
    items.push({
      id: uuidv4(),
      role,
      content,
    });
  });
  return items;
}
