import {
  AnnotationShape,
  createClassificationAnnotation,
  createBBoxAnnotation,
  createPolygonAnnotation,
  createOBBAnnotation,
  getOBBVertices,
} from '../types';
import type { Annotation, BBoxAnnotation, PolygonAnnotation, OBBAnnotation, Point } from '../types';

/**
 * 解析 YOLO 格式标注文本为 Annotation 数组
 * 根据每行数据长度自动判断格式：
 *   5 个值 = BBox (classId xCenter yCenter width height)
 *   9 个值 = OBB  (classId x1 y1 x2 y2 x3 y3 x4 y4)
 *   >5 且为奇数 = Polygon (classId x1 y1 x2 y2 ... xN yN)
 */
export function parseYoloAnnotations(
  fileContent: string,
  imageWidth: number,
  imageHeight: number,
): Annotation[] {
  const annotations: Annotation[] = [];
  const lines = fileContent.split('\n');

  for (const line of lines) {
    const parts = line.trim().split(/\s+/);
    if (parts.length < 1) continue;

    const classId = parseInt(parts[0], 10);
    if (Number.isNaN(classId)) continue;
    if (parts.length === 1) {
      annotations.push(createClassificationAnnotation(classId));
      continue;
    }

    const values = parts.slice(1).map((v) => parseFloat(v));

    if (values.length === 4) {
      // BBox: classId xCenter yCenter width height
      annotations.push(parseBBoxLine(classId, values, imageWidth, imageHeight));
    } else if (values.length === 8) {
      // OBB: classId x1 y1 x2 y2 x3 y3 x4 y4
      annotations.push(parseOBBLine(classId, values, imageWidth, imageHeight));
    } else if (values.length >= 6 && values.length % 2 === 0) {
      // Polygon: classId x1 y1 x2 y2 ... xN yN (至少 3 个点)
      annotations.push(parsePolygonLine(classId, values, imageWidth, imageHeight));
    }
  }

  return annotations;
}

/** 解析 BBox 行 */
function parseBBoxLine(
  classId: number,
  values: number[],
  imageWidth: number,
  imageHeight: number,
): BBoxAnnotation {
  const xCenter = Math.min(values[0], 1) * imageWidth;
  const yCenter = Math.min(values[1], 1) * imageHeight;
  const w = Math.min(values[2], 1) * imageWidth;
  const h = Math.min(values[3], 1) * imageHeight;
  const x = xCenter - w / 2;
  const y = yCenter - h / 2;
  return createBBoxAnnotation(x, y, w, h, classId);
}

/** 解析 OBB 行 (4 个顶点 → cx, cy, w, h, angle) */
function parseOBBLine(
  classId: number,
  values: number[],
  imageWidth: number,
  imageHeight: number,
): OBBAnnotation {
  // 4 个顶点，归一化坐标
  const pts: Point[] = [];
  for (let i = 0; i < 8; i += 2) {
    pts.push({
      x: Math.min(values[i], 1) * imageWidth,
      y: Math.min(values[i + 1], 1) * imageHeight,
    });
  }

  // 从 4 个顶点推算 cx, cy, w, h, angle
  const cx = (pts[0].x + pts[2].x) / 2;
  const cy = (pts[0].y + pts[2].y) / 2;

  // 第一条边的长度和角度
  const dx01 = pts[1].x - pts[0].x;
  const dy01 = pts[1].y - pts[0].y;
  const dx03 = pts[3].x - pts[0].x;
  const dy03 = pts[3].y - pts[0].y;
  const w = Math.sqrt(dx01 * dx01 + dy01 * dy01);
  const h = Math.sqrt(dx03 * dx03 + dy03 * dy03);
  const angle = Math.atan2(dy01, dx01);

  return createOBBAnnotation(cx, cy, w, h, angle, classId);
}

/** 解析 Polygon 行 */
function parsePolygonLine(
  classId: number,
  values: number[],
  imageWidth: number,
  imageHeight: number,
): PolygonAnnotation {
  const points: Point[] = [];
  for (let i = 0; i < values.length; i += 2) {
    points.push({
      x: Math.min(values[i], 1) * imageWidth,
      y: Math.min(values[i + 1], 1) * imageHeight,
    });
  }
  return createPolygonAnnotation(points, classId);
}

/**
 * 将 Annotation 数组转换为 YOLO 格式文本
 * 根据 annotation.shape 输出对应格式
 */
export function toYoloFormat(
  annotations: Annotation[],
  imageWidth: number,
  imageHeight: number,
): string {
  return annotations
    .filter((a) => a.classId >= 0)
    .map((a) => {
      switch (a.shape) {
        case AnnotationShape.BBox:
          return bboxToYolo(a, imageWidth, imageHeight);
        case AnnotationShape.OBB:
          return obbToYolo(a, imageWidth, imageHeight);
        case AnnotationShape.Polygon:
          return polygonToYolo(a, imageWidth, imageHeight);
        case AnnotationShape.Classification:
          return `${a.classId}`;
        default:
          return '';
      }
    })
    .filter(Boolean)
    .join('\n');
}

/** BBox → YOLO 格式 */
function bboxToYolo(a: BBoxAnnotation, imageWidth: number, imageHeight: number): string {
  const xCenter = (a.x + a.width / 2) / imageWidth;
  const yCenter = (a.y + a.height / 2) / imageHeight;
  const w = a.width / imageWidth;
  const h = a.height / imageHeight;
  return `${a.classId} ${xCenter.toFixed(6)} ${yCenter.toFixed(6)} ${w.toFixed(6)} ${h.toFixed(6)}`;
}

/** OBB → YOLO-OBB 格式 (4 个顶点归一化坐标) */
function obbToYolo(a: OBBAnnotation, imageWidth: number, imageHeight: number): string {
  const vertices: Point[] = getOBBVertices(a);
  const coords = vertices
    .map((p: Point) => `${(p.x / imageWidth).toFixed(6)} ${(p.y / imageHeight).toFixed(6)}`)
    .join(' ');
  return `${a.classId} ${coords}`;
}

/** Polygon → YOLO-Seg 格式 (多点归一化坐标) */
function polygonToYolo(a: PolygonAnnotation, imageWidth: number, imageHeight: number): string {
  if (a.points.length < 3) return '';
  const coords = a.points
    .map((p) => `${(p.x / imageWidth).toFixed(6)} ${(p.y / imageHeight).toFixed(6)}`)
    .join(' ');
  return `${a.classId} ${coords}`;
}
