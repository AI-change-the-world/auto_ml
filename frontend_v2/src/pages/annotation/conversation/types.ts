import type { ConversationAnnotationEntry } from '../../../utils/conversationAnnotation';

export interface PreviewState {
  loading: boolean;
  url?: string;
  textContent?: string;
  error?: string;
}

export interface ConversationFileRow {
  sampleItemId: number;
  fileName: string;
  messageCount: number;
  dirty: boolean;
  source: 'dataset' | 'manual';
}

export type ConversationEntriesBySample = Record<number, ConversationAnnotationEntry>;
