import { useEffect, useMemo, useRef } from 'react';
import { HocuspocusProvider } from '@hocuspocus/provider';
import * as Y from 'yjs';
import type { Annotation } from '../types';
import { useAnnotationStore } from '../stores/annotationStore';
import { useDatasetStore } from '../stores/datasetStore';

const LOCAL_ORIGIN = 'auto-ml-local-annotation-store';

interface UseAnnotationCollaborationDocumentOptions {
  enabled: boolean;
  annotationId?: number | null;
  sampleItemId?: number | null;
  collaboratorToken?: string | null;
  collaboratorName?: string | null;
}

function serializeAnnotation(annotation: Annotation): Record<string, unknown> {
  return { ...annotation };
}

function parseAnnotation(value: unknown): Annotation | null {
  if (!value || typeof value !== 'object') return null;
  const raw = value as Partial<Annotation>;
  if (!raw.uuid || !raw.shape) return null;
  return raw as Annotation;
}

function encodeUpdate(update: Uint8Array) {
  let binary = '';
  update.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return window.btoa(binary);
}

function writeCollaborationSnapshot(doc: Y.Doc) {
  if (typeof window === 'undefined') return;
  const update = Y.encodeStateAsUpdate(doc);
  useDatasetStore.setState({ collaborationState: encodeUpdate(update) });
}

export function useAnnotationCollaborationDocument({
  enabled,
  annotationId,
  sampleItemId,
  collaboratorToken,
  collaboratorName,
}: UseAnnotationCollaborationDocumentOptions) {
  const annotations = useAnnotationStore((state) => state.annotations);
  const setAnnotations = useAnnotationStore((state) => state.setAnnotations);
  const providerRef = useRef<HocuspocusProvider | null>(null);
  const docRef = useRef<Y.Doc | null>(null);

  const roomId = useMemo(() => {
    if (!enabled || !annotationId || !sampleItemId) return null;
    return `annotation:${annotationId}:sample:${sampleItemId}`;
  }, [annotationId, enabled, sampleItemId]);

  useEffect(() => {
    if (!roomId) return undefined;

    const doc = new Y.Doc();
    const map = doc.getMap<Record<string, unknown>>('annotations');
    docRef.current = doc;
    useDatasetStore.setState({ collaborationState: null });

    const observer = (event: Y.YMapEvent<Record<string, unknown>>) => {
      if (event.transaction.origin === LOCAL_ORIGIN) return;
      const nextAnnotations = Array.from(map.values())
        .map(parseAnnotation)
        .filter((item): item is Annotation => Boolean(item));
      setAnnotations(nextAnnotations);
      writeCollaborationSnapshot(doc);
    };
    map.observe(observer);

    const wsUrl = import.meta.env.VITE_ANNOTATION_COLLAB_WS_URL as string | undefined;
    if (wsUrl) {
      const provider = new HocuspocusProvider({
        url: wsUrl,
        name: roomId,
        document: doc,
        token: collaboratorToken || null,
      });
      provider.awareness?.setLocalStateField('user', {
        name: collaboratorName || '匿名标注员',
      });
      providerRef.current = provider;
    }

    return () => {
      providerRef.current?.destroy();
      providerRef.current = null;
      map.unobserve(observer);
      doc.destroy();
      docRef.current = null;
    };
  }, [collaboratorName, collaboratorToken, roomId, setAnnotations]);

  useEffect(() => {
    const doc = docRef.current;
    if (!doc) return;
    const map = doc.getMap<Record<string, unknown>>('annotations');
      doc.transact(() => {
      const nextIds = new Set(annotations.map((item) => item.uuid));
      Array.from(map.keys()).forEach((uuid) => {
        if (!nextIds.has(uuid)) map.delete(uuid);
      });
      annotations.forEach((annotation) => {
        map.set(annotation.uuid, serializeAnnotation(annotation));
      });
    }, LOCAL_ORIGIN);
    writeCollaborationSnapshot(doc);
  }, [annotations]);
}
