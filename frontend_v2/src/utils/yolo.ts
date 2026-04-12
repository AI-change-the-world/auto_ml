import { createBBoxAnnotation } from '../types';
import type { BBoxAnnotation } from '../types';

/**
 * 解析 YOLO 格式标注文本为 BBoxAnnotation 数组
 * YOLO 格式: classId xCenter yCenter width height (归一化坐标 0~1)
 */
export function parseYoloAnnotations(
  fileContent: string,
  imageWidth: number,
  imageHeight: number,
): BBoxAnnotation[] {
  const annotations: BBoxAnnotation[] = [];
  const lines = fileContent.split('\n');

  for (const line of lines) {
    const parts = line.trim().split(/\s+/);
    if (parts.length < 5) continue;

    const classId = parseInt(parts[0], 10);
    const xCenter = Math.min(parseFloat(parts[1]), 1) * imageWidth;
    const yCenter = Math.min(parseFloat(parts[2]), 1) * imageHeight;
    const w = Math.min(parseFloat(parts[3]), 1) * imageWidth;
    const h = Math.min(parseFloat(parts[4]), 1) * imageHeight;

    const x = xCenter - w / 2;
    const y = yCenter - h / 2;

    annotations.push(createBBoxAnnotation(x, y, w, h, classId));
  }

  return annotations;
}

/**
 * 将 BBoxAnnotation 数组转换为 YOLO 格式文本
 * 输出归一化坐标
 */
export function toYoloFormat(
  annotations: BBoxAnnotation[],
  imageWidth: number,
  imageHeight: number,
): string {
  return annotations
    .filter((a) => a.classId >= 0)
    .map((a) => {
      const xCenter = (a.x + a.width / 2) / imageWidth;
      const yCenter = (a.y + a.height / 2) / imageHeight;
      const w = a.width / imageWidth;
      const h = a.height / imageHeight;
      return `${a.classId} ${xCenter.toFixed(6)} ${yCenter.toFixed(6)} ${w.toFixed(6)} ${h.toFixed(6)}`;
    })
    .join('\n');
}
