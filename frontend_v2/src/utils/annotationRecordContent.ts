import { parseClassificationAnnotationContent } from './classification';

export function getRecordLabelText(content: Record<string, unknown> | null | undefined): string {
  if (!content) return '';
  const direct = content.label_text ?? content.yolo ?? content.content;
  return typeof direct === 'string' ? direct : '';
}

export function buildYoloRecordContent(
  labelText: string,
  imageWidth: number,
  imageHeight: number,
): Record<string, unknown> {
  return {
    format: 'yolo',
    label_text: labelText,
    image_width: imageWidth,
    image_height: imageHeight,
  };
}

export function getRecordClassIds(content: Record<string, unknown> | null | undefined): number[] {
  if (!content) return [];
  if (Array.isArray(content.class_ids)) {
    return parseClassificationAnnotationContent(JSON.stringify(content.class_ids));
  }
  if (typeof content.class_id === 'number' || typeof content.class_id === 'string') {
    return parseClassificationAnnotationContent(String(content.class_id));
  }
  const labelText = getRecordLabelText(content);
  return parseClassificationAnnotationContent(labelText);
}

export function buildClassificationRecordContent(classIds: number[]): Record<string, unknown> {
  return {
    format: 'classification',
    class_ids: classIds,
  };
}
