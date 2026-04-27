export function parseClassificationAnnotationContent(content: string | null | undefined): number[] {
  const text = content?.trim();
  if (!text) return [];

  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) {
      return normalizeClassificationLabelIds(parsed);
    }
    if (typeof parsed === 'number' || typeof parsed === 'string') {
      return normalizeClassificationLabelIds([parsed]);
    }
    if (parsed && typeof parsed === 'object') {
      const classIds = (parsed as { class_ids?: unknown }).class_ids;
      if (Array.isArray(classIds)) {
        return normalizeClassificationLabelIds(classIds);
      }
    }
  } catch {
    // 兼容旧格式：单个整数或换行/逗号分隔
  }

  return normalizeClassificationLabelIds(text.split(/[\s,]+/).filter(Boolean));
}

export function serializeClassificationAnnotationContent(classIds: number[]): string {
  const normalized = normalizeClassificationLabelIds(classIds);
  if (normalized.length === 0) return '';
  if (normalized.length === 1) return String(normalized[0]);
  return JSON.stringify(normalized);
}

export function normalizeClassificationLabelIds(values: unknown[]): number[] {
  const normalized = values
    .map((value) => {
      if (typeof value === 'number') return Math.trunc(value);
      if (typeof value === 'string' && value.trim() !== '') return Number.parseInt(value, 10);
      return Number.NaN;
    })
    .filter((value) => Number.isInteger(value) && value >= 0);

  return Array.from(new Set(normalized)).sort((a, b) => a - b);
}

export function buildClassificationLabelFileName(fileName: string): string {
  return fileName.replace(/\.[^.]+$/, '.txt');
}
