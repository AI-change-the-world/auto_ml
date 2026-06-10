import { create } from 'zustand';
import { message } from 'antd';
import {
  createAnnotationCollaborationSession,
} from '../api/annotation';
import {
  type AnnotationCollaborator,
} from '../types';

const TOKEN_STORAGE_PREFIX = 'auto_ml.annotation.collaborator_token';

function getTokenStorageKey(annotationId: number) {
  return `${TOKEN_STORAGE_PREFIX}.${annotationId}`;
}

function readStoredToken(annotationId: number): string | undefined {
  if (typeof window === 'undefined') return undefined;
  return window.localStorage.getItem(getTokenStorageKey(annotationId)) || undefined;
}

function writeStoredToken(annotationId: number, token: string) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(getTokenStorageKey(annotationId), token);
}

interface AnnotationCollaborationState {
  collaborator: AnnotationCollaborator | null;
  loading: boolean;
  initializedAnnotationId: number | null;

  initialize: (annotationId: number) => Promise<void>;
  reset: () => void;
}

export const useAnnotationCollaborationStore = create<AnnotationCollaborationState>((set, get) => ({
  collaborator: null,
  loading: false,
  initializedAnnotationId: null,

  initialize: async (annotationId: number) => {
    const current = get();
    if (current.initializedAnnotationId === annotationId && current.collaborator) return;

    set({ loading: true });
    try {
      const session = await createAnnotationCollaborationSession(annotationId, readStoredToken(annotationId));
      const collaborator = session.collaborator;
      writeStoredToken(annotationId, collaborator.token);
      set({ collaborator, initializedAnnotationId: annotationId });
    } catch (error) {
      console.error('Failed to initialize collaborative annotation:', error);
      message.error('初始化协作标注失败');
    } finally {
      set({ loading: false });
    }
  },

  reset: () => {
    set({
      collaborator: null,
      loading: false,
      initializedAnnotationId: null,
    });
  },
}));
