const IMAGE_EXTENSIONS = new Set([
  'jpg',
  'jpeg',
  'png',
  'webp',
  'bmp',
  'gif',
]);

export function getFileExtension(fileName: string): string {
  return fileName.split('.').pop()?.toLowerCase() ?? '';
}

export function isImageFileName(fileName: string): boolean {
  return IMAGE_EXTENSIONS.has(getFileExtension(fileName));
}
