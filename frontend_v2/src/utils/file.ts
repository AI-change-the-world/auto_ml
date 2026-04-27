const IMAGE_EXTENSIONS = new Set([
  'jpg',
  'jpeg',
  'png',
  'webp',
  'bmp',
  'gif',
]);

const TEXT_EXTENSIONS = new Set([
  'txt',
  'md',
  'json',
  'csv',
  'tsv',
  'log',
  'xml',
  'yaml',
  'yml',
]);

export function getFileExtension(fileName: string): string {
  return fileName.split('.').pop()?.toLowerCase() ?? '';
}

export function isImageFileName(fileName: string): boolean {
  return IMAGE_EXTENSIONS.has(getFileExtension(fileName));
}

export function isTextFileName(fileName: string): boolean {
  return TEXT_EXTENSIONS.has(getFileExtension(fileName));
}
