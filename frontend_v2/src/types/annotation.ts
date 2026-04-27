import { v4 as uuidv4 } from 'uuid';

/** 标注模式 */
export enum LabelMode {
  Edit = 'edit',
  Add = 'add',
}

/** 标注形状类型 */
export enum AnnotationShape {
  BBox = 'bbox',
  Polygon = 'polygon',
  OBB = 'obb',
  Classification = 'classification',
}

/** 2D 坐标点 */
export interface Point {
  x: number;
  y: number;
}

/** 标注基础字段 */
interface BaseAnnotation {
  uuid: string;
  classId: number;
  visible: boolean;
  selected: boolean;
}

/** 边界框标注 */
export interface BBoxAnnotation extends BaseAnnotation {
  shape: AnnotationShape.BBox;
  x: number;
  y: number;
  width: number;
  height: number;
}

/** 多边形标注（分割） */
export interface PolygonAnnotation extends BaseAnnotation {
  shape: AnnotationShape.Polygon;
  points: Point[];
}

/** 旋转框标注（OBB） */
export interface OBBAnnotation extends BaseAnnotation {
  shape: AnnotationShape.OBB;
  cx: number;
  cy: number;
  width: number;
  height: number;
  angle: number; // 弧度
}

/** 分类标注（整图分类） */
export interface ClassificationAnnotation extends BaseAnnotation {
  shape: AnnotationShape.Classification;
}

/** 联合标注类型 */
export type Annotation = BBoxAnnotation | PolygonAnnotation | OBBAnnotation | ClassificationAnnotation;

/** 创建新的边界框标注 */
export function createBBoxAnnotation(
  x: number,
  y: number,
  width: number,
  height: number,
  classId: number = -1,
): BBoxAnnotation {
  return {
    shape: AnnotationShape.BBox,
    uuid: uuidv4(),
    x,
    y,
    width,
    height,
    classId,
    visible: true,
    selected: false,
  };
}

/** 创建新的多边形标注 */
export function createPolygonAnnotation(
  points: Point[],
  classId: number = -1,
): PolygonAnnotation {
  return {
    shape: AnnotationShape.Polygon,
    uuid: uuidv4(),
    points,
    classId,
    visible: true,
    selected: false,
  };
}

/** 创建新的 OBB 标注 */
export function createOBBAnnotation(
  cx: number,
  cy: number,
  width: number,
  height: number,
  angle: number = 0,
  classId: number = -1,
): OBBAnnotation {
  return {
    shape: AnnotationShape.OBB,
    uuid: uuidv4(),
    cx,
    cy,
    width,
    height,
    angle,
    classId,
    visible: true,
    selected: false,
  };
}

/** 创建新的分类标注 */
export function createClassificationAnnotation(
  classId: number = -1,
): ClassificationAnnotation {
  return {
    shape: AnnotationShape.Classification,
    uuid: uuidv4(),
    classId,
    visible: true,
    selected: false,
  };
}

/** 获取 OBB 的 4 个顶点坐标（顺时针） */
export function getOBBVertices(obb: OBBAnnotation): [Point, Point, Point, Point] {
  const cos = Math.cos(obb.angle);
  const sin = Math.sin(obb.angle);
  const hw = obb.width / 2;
  const hh = obb.height / 2;
  const corners: [number, number][] = [
    [-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh],
  ];
  return corners.map(([dx, dy]) => ({
    x: obb.cx + dx * cos - dy * sin,
    y: obb.cy + dx * sin + dy * cos,
  })) as [Point, Point, Point, Point];
}

/** 获取多边形的包围盒中心 */
export function getPolygonCenter(poly: PolygonAnnotation): Point {
  if (poly.points.length === 0) return { x: 0, y: 0 };
  const sum = poly.points.reduce((acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y }), { x: 0, y: 0 });
  return { x: sum.x / poly.points.length, y: sum.y / poly.points.length };
}

/** YOLO 格式标签 */
export interface YoloLabel {
  classId: number;
  xCenter: number;
  yCenter: number;
  width: number;
  height: number;
}

/** 标注项目创建请求 */
export interface AnnotationCreate {
  name: string;
  annotation_type?: number;
  classes?: string;
  storage_type?: number;
  prompt?: string;
  assist_pipeline?: string;
  dataset_id?: number;
}

/** 标注类型标签 */
export const AnnotationTypeLabels: Record<number, string> = {
  0: '检测',
  1: '分类',
  2: '分割',
  3: 'MLLM',
  4: '姿态',
};

export const AnnotationTypeColors: Record<number, string> = {
  0: 'blue',
  1: 'green',
  2: 'orange',
  3: 'purple',
  4: 'cyan',
};

export const AnnotationTypeIconKeys: Record<number, string> = {
  0: 'bbox',
  1: 'classification',
  2: 'polygon',
  3: 'mllm',
  4: 'pose',
};

/** 标注项目响应 */
export interface AnnotationProject {
  id: number;
  name: string;
  annotation_type: number;
  classes: string | null;
  storage_type: number;
  save_path: string | null;
  prompt: string | null;
  assist_pipeline: string | null;
  dataset_id: number | null;
  created_at: string;
  updated_at: string;
}

/** 标注文件响应 */
export interface AnnotationFile {
  id: number;
  annotation_id: number;
  file_name: string;
  save_path: string | null;
  content: string | null;
  created_at: string;
}

/** 保存标注文件请求 */
export interface AnnotationFileSaveRequest {
  file_name: string;
  content: string;
}

export interface AnnotationAssistRequest {
  file_name: string;
  pipeline_id?: string;
  shape?: string;
  target_classes?: string[];
  replace_existing?: boolean;
  params?: Record<string, unknown>;
}

export interface AnnotationAssistPipeline {
  id: string;
  name: string;
  description?: string | null;
  supported_annotation_types: number[];
  supported_shapes: string[];
  enabled: boolean;
}

export interface AnnotationAssistItem {
  label: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  confidence?: number | null;
  source?: string | null;
}

export interface AnnotationAssistResponse {
  file_name: string;
  image_width: number;
  image_height: number;
  annotations: AnnotationAssistItem[];
  replace_existing: boolean;
  debug?: Record<string, unknown> | null;
}

/** 标注类型枚举 */
export enum AnnotationType {
  Detection = 0,
  Classification = 1,
  Segmentation = 2,
  MLLM = 3,
  Pose = 4,
}

/** 颜色调色板 - 为不同类别分配颜色 */
export const CLASS_COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
  '#F0B27A', '#82E0AA', '#F1948A', '#85929E', '#73C6B6',
  '#E59866', '#AED6F1', '#D2B4DE', '#A3E4D7', '#FAD7A0',
];

export function getClassColor(classId: number): string {
  if (classId < 0) return '#999999';
  return CLASS_COLORS[classId % CLASS_COLORS.length];
}
