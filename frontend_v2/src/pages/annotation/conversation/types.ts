import type { ConversationAnnotationEntry } from '../../../utils/conversationAnnotation';

export interface PreviewState {
  loading: boolean;
  url?: string;
  textContent?: string;
  error?: string;
}

export interface ConversationFileRow {
  fileName: string;
  messageCount: number;
  dirty: boolean;
  source: 'dataset' | 'manual';
}

export type ConversationEntriesByFile = Record<string, ConversationAnnotationEntry>;
