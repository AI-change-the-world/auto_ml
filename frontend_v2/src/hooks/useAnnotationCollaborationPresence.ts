import { useEffect, useMemo, useRef, useState } from 'react';
import { HocuspocusProvider } from '@hocuspocus/provider';
import * as Y from 'yjs';
import type { AnnotationCollaborator } from '../types';

const PRESENCE_COLORS = [
  '#1677ff',
  '#13a8a8',
  '#52c41a',
  '#fa8c16',
  '#eb2f96',
  '#722ed1',
  '#2f54eb',
  '#a0d911',
];

export interface AnnotationSampleEditor {
  id: string;
  name: string;
  color: string;
  sampleItemId: number;
  local: boolean;
}

interface UseAnnotationCollaborationPresenceOptions {
  enabled: boolean;
  annotationId?: number | null;
  sampleItemId?: number | null;
  collaborator?: AnnotationCollaborator | null;
  participantName?: string | null;
}

interface RawPresenceState {
  collaboratorId: number;
  name: string;
  color: string;
  sampleItemId: number;
  updatedAt: number;
}

function hashText(value: string) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function getCollaboratorColor(collaborator?: AnnotationCollaborator | null, participantId = 'local') {
  const seed = collaborator ? `${collaborator.id}:${collaborator.display_name}` : participantId;
  return PRESENCE_COLORS[hashText(seed) % PRESENCE_COLORS.length];
}

function readLocalParticipantId() {
  if (typeof window === 'undefined') return 'local';
  const storageKey = 'auto_ml.annotation.local_participant_id';
  const existing = window.localStorage.getItem(storageKey);
  if (existing) return existing;
  const next = `local-${Math.random().toString(36).slice(2, 8)}`;
  window.localStorage.setItem(storageKey, next);
  return next;
}

function getLocalParticipantName(participantId: string) {
  return `用户-${participantId.replace(/^local-/, '')}`;
}

function isRawPresenceState(value: unknown): value is RawPresenceState {
  if (!value || typeof value !== 'object') return false;
  const raw = value as Partial<RawPresenceState>;
  return (
    typeof raw.collaboratorId === 'number'
    && typeof raw.name === 'string'
    && typeof raw.color === 'string'
    && typeof raw.sampleItemId === 'number'
    && typeof raw.updatedAt === 'number'
  );
}

function collectEditors(provider: HocuspocusProvider) {
  const awareness = provider.awareness;
  if (!awareness) return [];

  return Array.from(awareness.getStates().entries())
    .map(([clientId, state]) => {
      const raw = state.annotationPresence;
      if (!isRawPresenceState(raw)) return null;
      return {
        id: `${raw.collaboratorId}:${clientId}`,
        name: raw.name,
        color: raw.color,
        sampleItemId: raw.sampleItemId,
        local: clientId === awareness.clientID,
      };
    })
    .filter((item): item is AnnotationSampleEditor => Boolean(item));
}

export function useAnnotationCollaborationPresence({
  enabled,
  annotationId,
  sampleItemId,
  collaborator,
  participantName,
}: UseAnnotationCollaborationPresenceOptions) {
  const [editors, setEditors] = useState<AnnotationSampleEditor[]>([]);
  const providerRef = useRef<HocuspocusProvider | null>(null);
  const localParticipantIdRef = useRef(readLocalParticipantId());

  const roomId = useMemo(() => {
    if (!enabled || !annotationId) return null;
    return `annotation:${annotationId}:presence`;
  }, [annotationId, enabled]);

  const localPresence = useMemo<RawPresenceState | null>(() => {
    if (!enabled || !sampleItemId) return null;
    const localParticipantId = localParticipantIdRef.current;
    return {
      collaboratorId: collaborator?.id ?? -Math.abs(hashText(localParticipantId)),
      name: collaborator?.display_name || participantName || getLocalParticipantName(localParticipantId),
      color: getCollaboratorColor(collaborator, localParticipantId),
      sampleItemId,
      updatedAt: Date.now(),
    };
  }, [collaborator, enabled, participantName, sampleItemId]);

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_ANNOTATION_COLLAB_WS_URL as string | undefined;
    if (!roomId || !wsUrl) return undefined;

    const doc = new Y.Doc();
    const provider = new HocuspocusProvider({
      url: wsUrl,
      name: roomId,
      document: doc,
      token: collaborator?.token || null,
    });
    providerRef.current = provider;

    const syncEditors = () => {
      setEditors(collectEditors(provider));
    };

    provider.awareness?.on('change', syncEditors);
    syncEditors();

    return () => {
      provider.awareness?.setLocalState(null);
      provider.awareness?.off('change', syncEditors);
      provider.destroy();
      doc.destroy();
      providerRef.current = null;
    };
  }, [collaborator?.token, roomId]);

  useEffect(() => {
    const provider = providerRef.current;
    if (!provider?.awareness) {
      setEditors(localPresence ? [{
        id: `${localPresence.collaboratorId}:local`,
        name: localPresence.name,
        color: localPresence.color,
        sampleItemId: localPresence.sampleItemId,
        local: true,
      }] : []);
      return;
    }

    if (localPresence) {
      provider.awareness.setLocalStateField('annotationPresence', localPresence);
    } else {
      provider.awareness.setLocalState(null);
    }
    setEditors(collectEditors(provider));
  }, [localPresence]);

  return editors;
}
