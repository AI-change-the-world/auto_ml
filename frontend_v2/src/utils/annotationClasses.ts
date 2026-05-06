function normalizeClassItems(items: unknown[]): string[] {
  const seen = new Set<string>();
  const classes: string[] = [];

  for (const item of items) {
    const className = String(item).trim();
    if (!className || seen.has(className)) continue;
    seen.add(className);
    classes.push(className);
  }

  return classes;
}

function parseClassText(text: string): string[] {
  return normalizeClassItems(text.split(/[,\n\r;；，]+/));
}

export function parseAnnotationClasses(rawClasses: string | string[] | null | undefined): string[] {
  if (!rawClasses) return [];
  if (Array.isArray(rawClasses)) return normalizeClassItems(rawClasses);

  try {
    const parsed = JSON.parse(rawClasses);
    if (Array.isArray(parsed)) return normalizeClassItems(parsed);
    if (typeof parsed === 'string') return parseClassText(parsed);
  } catch {
    return parseClassText(rawClasses);
  }

  return [];
}

export function serializeAnnotationClasses(rawClasses: string | string[] | null | undefined): string {
  return JSON.stringify(parseAnnotationClasses(rawClasses));
}
