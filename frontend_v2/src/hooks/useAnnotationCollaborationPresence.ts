import { useEffect, useMemo, useRef, useState } from 'react';
import { HocuspocusProvider } from '@hocuspocus/provider';
import * as Y from 'yjs';
import { heartbeatAnnotationPresence, leaveAnnotationPresence } from '../api/annotation';
import type {
  AnnotationCollaborator,
  AnnotationCollaboratorSummary,
  AnnotationPresenceHeartbeatRequest,
} from '../types';

const HEARTBEAT_INTERVAL_MS = 10_000;
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
  participantId?: string;
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

function buildAnnotationApiUrl(path: string) {
  const base = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
  return new URL(`${base}${path}`, window.location.origin).toString();
}

function sendPresenceLeaveBeacon(annotationId: number, participantId: string) {
  if (typeof window === 'undefined') return;
  const body = JSON.stringify({ participant_id: participantId });
  const url = buildAnnotationApiUrl(`/annotation/${annotationId}/presence/leave`);

  if (navigator.sendBeacon) {
    const sent = navigator.sendBeacon(url, new Blob([body], { type: 'application/json' }));
    if (sent) return;
  }

  void fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    keepalive: true,
  }).catch((error) => {
    console.warn('[annotation:presence] leave keepalive failed', { annotationId, participantId, error });
  });
}

function formatPresenceItems(items: AnnotationCollaboratorSummary[]) {
  return items.map((item) => ({
    participantId: item.participant_id,
    displayName: item.display_name,
    sampleItemId: item.sample_item_id,
  }));
}

function reportPresenceHeartbeat(annotationId: number, payload: AnnotationPresenceHeartbeatRequest) {
  return heartbeatAnnotationPresence(annotationId, payload)
    .then((items) => {
      console.info('[annotation:presence] heartbeat', {
        annotationId,
        participantId: payload.participant_id,
        displayName: payload.display_name,
        sampleItemId: payload.sample_item_id,
        online: formatPresenceItems(items),
      });
      return items;
    })
    .catch((error) => {
      console.warn('[annotation:presence] heartbeat failed', {
        annotationId,
        participantId: payload.participant_id,
        error,
      });
      return [];
    });
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
        id: raw.participantId || `${raw.collaboratorId}:${clientId}`,
        name: raw.name,
        color: raw.color,
        sampleItemId: raw.sampleItemId,
        local: clientId === awareness.clientID,
      };
    })
    .filter((item): item is AnnotationSampleEditor => Boolean(item));
}

function buildServerPresenceEditors(
  items: AnnotationCollaboratorSummary[],
  localParticipantId: string,
): AnnotationSampleEditor[] {
  return items
    .filter((item) => typeof item.sample_item_id === 'number')
    .map((item) => ({
      id: item.participant_id,
      name: item.display_name,
      color: getCollaboratorColor(null, item.participant_id),
      sampleItemId: item.sample_item_id as number,
      local: item.participant_id === localParticipantId,
    }));
}

function mergeEditors(
  serverEditors: AnnotationSampleEditor[],
  yjsEditors: AnnotationSampleEditor[],
) {
  const editorMap = new Map<string, AnnotationSampleEditor>();
  const upsertEditor = (editor: AnnotationSampleEditor) => {
    const key = editor.local ? 'local' : editor.id;
    editorMap.set(key, editor);
  };

  serverEditors.forEach(upsertEditor);
  yjsEditors.forEach(upsertEditor);
  const mergedEditors = Array.from(editorMap.values());
  const localEditor = mergedEditors.find((editor) => editor.local);
  if (!localEditor) return mergedEditors;
  return mergedEditors.filter((editor) => editor.local || editor.name !== localEditor.name);
}

export function useAnnotationCollaborationPresence({
  enabled,
  annotationId,
  sampleItemId,
  collaborator,
  participantName,
}: UseAnnotationCollaborationPresenceOptions) {
  const [editors, setEditors] = useState<AnnotationSampleEditor[]>([]);
  const [serverPresenceEditors, setServerPresenceEditors] = useState<AnnotationSampleEditor[]>([]);
  const [connectedPresenceRoomId, setConnectedPresenceRoomId] = useState<string | null>(null);
  const providerRef = useRef<HocuspocusProvider | null>(null);
  const localParticipantIdRef = useRef(readLocalParticipantId());
  const presencePayloadRef = useRef<AnnotationPresenceHeartbeatRequest | null>(null);
  const collabWsUrl = (import.meta.env.VITE_ANNOTATION_COLLAB_WS_URL as string | undefined)?.trim();

  const roomId = useMemo(() => {
    if (!enabled || !annotationId) return null;
    return `annotation:${annotationId}:presence`;
  }, [annotationId, enabled]);

  const activeAnnotationId = useMemo(() => {
    if (!enabled || !annotationId || !Number.isFinite(annotationId)) return null;
    return annotationId;
  }, [annotationId, enabled]);

  const participantDisplayName = useMemo(() => {
    const localParticipantId = localParticipantIdRef.current;
    return collaborator?.display_name || participantName || getLocalParticipantName(localParticipantId);
  }, [collaborator?.display_name, participantName]);

  const presencePayload = useMemo<AnnotationPresenceHeartbeatRequest | null>(() => {
    if (!activeAnnotationId) return null;
    return {
      participant_id: localParticipantIdRef.current,
      display_name: participantDisplayName,
      sample_item_id: sampleItemId ?? null,
    };
  }, [activeAnnotationId, participantDisplayName, sampleItemId]);

  const presenceHeartbeatEnabled = Boolean(
    activeAnnotationId && (!collabWsUrl || connectedPresenceRoomId === roomId),
  );

  const localPresence = useMemo<RawPresenceState | null>(() => {
    if (!enabled || !sampleItemId) return null;
    const localParticipantId = localParticipantIdRef.current;
    return {
      participantId: localParticipantId,
      collaboratorId: collaborator?.id ?? -Math.abs(hashText(localParticipantId)),
      name: participantDisplayName,
      color: getCollaboratorColor(collaborator, localParticipantId),
      sampleItemId,
      updatedAt: Date.now(),
    };
  }, [collaborator, enabled, participantDisplayName, sampleItemId]);

  useEffect(() => {
    presencePayloadRef.current = presencePayload;
  }, [presencePayload]);

  useEffect(() => {
    if (!activeAnnotationId || !presencePayload || !presenceHeartbeatEnabled) return;

    void reportPresenceHeartbeat(activeAnnotationId, presencePayload).then((items) => {
      setServerPresenceEditors(buildServerPresenceEditors(items, localParticipantIdRef.current));
    });
  }, [activeAnnotationId, presenceHeartbeatEnabled, presencePayload]);

  useEffect(() => {
    if (!activeAnnotationId || !presenceHeartbeatEnabled) return undefined;
    const participantId = localParticipantIdRef.current;

    const sendHeartbeat = () => {
      const payload = presencePayloadRef.current;
      if (!payload) return;
      void reportPresenceHeartbeat(activeAnnotationId, payload).then((items) => {
        setServerPresenceEditors(buildServerPresenceEditors(items, participantId));
      });
    };

    const timer = window.setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);
    const handlePageHide = () => {
      console.info('[annotation:presence] pagehide leave', { annotationId: activeAnnotationId, participantId });
      sendPresenceLeaveBeacon(activeAnnotationId, participantId);
    };
    window.addEventListener('pagehide', handlePageHide);

    return () => {
      window.clearInterval(timer);
      window.removeEventListener('pagehide', handlePageHide);
      setServerPresenceEditors([]);
      leaveAnnotationPresence(activeAnnotationId, participantId)
        .then((items) => {
          console.info('[annotation:presence] leave', {
            annotationId: activeAnnotationId,
            participantId,
            online: formatPresenceItems(items),
          });
        })
        .catch((error) => {
          console.warn('[annotation:presence] leave failed', { annotationId: activeAnnotationId, participantId, error });
        });
    };
  }, [activeAnnotationId, presenceHeartbeatEnabled]);

  useEffect(() => {
    if (!roomId || !collabWsUrl) {
      setConnectedPresenceRoomId(null);
      return undefined;
    }

    setConnectedPresenceRoomId((currentRoomId) => (currentRoomId === roomId ? null : currentRoomId));
    const doc = new Y.Doc();
    const provider = new HocuspocusProvider({
      url: collabWsUrl,
      name: roomId,
      document: doc,
      token: collaborator?.token || null,
    });
    providerRef.current = provider;

    const syncEditors = () => {
      setEditors(collectEditors(provider));
    };
    const syncProviderStatus = ({ status }: { status: string }) => {
      console.info('[annotation:presence] yjs status', { roomId, status });
      setConnectedPresenceRoomId((currentRoomId) => {
        if (status === 'connected') return roomId;
        if (currentRoomId === roomId) return null;
        return currentRoomId;
      });
    };

    provider.awareness?.on('change', syncEditors);
    provider.on('status', syncProviderStatus);
    syncEditors();

    return () => {
      provider.awareness?.setLocalState(null);
      provider.awareness?.off('change', syncEditors);
      provider.off('status', syncProviderStatus);
      provider.destroy();
      doc.destroy();
      providerRef.current = null;
      setConnectedPresenceRoomId((currentRoomId) => (currentRoomId === roomId ? null : currentRoomId));
    };
  }, [collabWsUrl, collaborator?.token, roomId]);

  useEffect(() => {
    const provider = providerRef.current;
    if (!provider?.awareness) {
      setEditors(localPresence ? [{
        id: localPresence.participantId || `${localPresence.collaboratorId}:local`,
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

  return useMemo(
    () => mergeEditors(serverPresenceEditors, editors),
    [editors, serverPresenceEditors],
  );
}
