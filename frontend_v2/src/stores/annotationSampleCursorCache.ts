const SAMPLE_CURSOR_STORAGE_KEY = 'auto_ml.annotation.sample_cursor';

export interface SampleCursorCacheItem {
  sampleId: number;
  sampleName: string;
  updatedAt: number;
}

export type SampleCursorCache = Record<number, SampleCursorCacheItem>;

export function readSampleCursorCache(): SampleCursorCache {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(SAMPLE_CURSOR_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, SampleCursorCacheItem>;
    const cache: SampleCursorCache = {};
    Object.entries(parsed).forEach(([key, value]) => {
      const annotationId = Number(key);
      if (!Number.isFinite(annotationId) || !value || typeof value.sampleId !== 'number') return;
      cache[annotationId] = value;
    });
    return cache;
  } catch {
    return {};
  }
}

export function writeSampleCursorCache(cache: SampleCursorCache) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(SAMPLE_CURSOR_STORAGE_KEY, JSON.stringify(cache));
  } catch {
    // Ignore localStorage failures; cursor restore is best-effort.
  }
}
