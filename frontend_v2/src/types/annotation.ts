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

/** 标注类型枚举，与后端 app.common.constants.AnnotationType 保持一致 */
export enum AnnotationType {
  Detection = 0,
  Classification = 1,
  Segmentation = 2,
  MLLM = 3,
  Pose = 4,
  LLM = 5,
  DPO = 6,
  DpoPairwise = 7,
  DpoBestOfN = 8,
  DpoReferenceChoice = 9,
  DpoMultiTurn = 10,
}

export interface AnnotationTypeDefinition {
  value: number;
  code: string;
  label: string;
  color: string;
  icon_key: string;
  supports_classes: boolean;
}

export class AnnotationTypeModel {
  readonly value: number;
  readonly code: string;
  readonly label: string;
  readonly color: string;
  readonly iconKey: string;
  readonly supportsClasses: boolean;

  constructor(definition: AnnotationTypeDefinition) {
    this.value = definition.value;
    this.code = definition.code;
    this.label = definition.label;
    this.color = definition.color;
    this.iconKey = definition.icon_key;
    this.supportsClasses = definition.supports_classes;
  }
}

export const DEFAULT_ANNOTATION_TYPE_DEFINITIONS: AnnotationTypeDefinition[] = [
  {
    value: AnnotationType.Detection,
    code: 'detection',
    label: '检测',
    color: 'blue',
    icon_key: 'bbox',
    supports_classes: true,
  },
  {
    value: AnnotationType.Classification,
    code: 'classification',
    label: '分类',
    color: 'green',
    icon_key: 'classification',
    supports_classes: true,
  },
  {
    value: AnnotationType.Segmentation,
    code: 'segmentation',
    label: '分割',
    color: 'orange',
    icon_key: 'polygon',
    supports_classes: true,
  },
  {
    value: AnnotationType.MLLM,
    code: 'mllm',
    label: 'MLLM',
    color: 'purple',
    icon_key: 'mllm',
    supports_classes: false,
  },
  {
    value: AnnotationType.Pose,
    code: 'pose',
    label: '姿态',
    color: 'cyan',
    icon_key: 'pose',
    supports_classes: true,
  },
  {
    value: AnnotationType.LLM,
    code: 'llm',
    label: 'LLM',
    color: 'geekblue',
    icon_key: 'llm',
    supports_classes: false,
  },
  {
    value: AnnotationType.DPO,
    code: 'dpo',
    label: 'DPO 兼容',
    color: 'gold',
    icon_key: 'dpo',
    supports_classes: false,
  },
  {
    value: AnnotationType.DpoPairwise,
    code: 'dpo_pairwise',
    label: 'DPO 二选一',
    color: 'gold',
    icon_key: 'dpo',
    supports_classes: false,
  },
  {
    value: AnnotationType.DpoBestOfN,
    code: 'dpo_best_of_n',
    label: 'DPO 多选一',
    color: 'gold',
    icon_key: 'dpo',
    supports_classes: false,
  },
  {
    value: AnnotationType.DpoReferenceChoice,
    code: 'dpo_reference_choice',
    label: 'DPO 参考增强',
    color: 'gold',
    icon_key: 'dpo',
    supports_classes: false,
  },
  {
    value: AnnotationType.DpoMultiTurn,
    code: 'dpo_multi_turn',
    label: 'DPO 多轮对话',
    color: 'gold',
    icon_key: 'dpo',
    supports_classes: false,
  },
];

export const createAnnotationTypeRegistry = (
  definitions: AnnotationTypeDefinition[] = DEFAULT_ANNOTATION_TYPE_DEFINITIONS,
): Record<number, AnnotationTypeModel> => Object.fromEntries(
  definitions.map((definition) => [definition.value, new AnnotationTypeModel(definition)]),
);

export const DefaultAnnotationTypeRegistry = createAnnotationTypeRegistry();

/** 标注类型标签 */
export const AnnotationTypeLabels: Record<number, string> = Object.fromEntries(
  DEFAULT_ANNOTATION_TYPE_DEFINITIONS.map((definition) => [definition.value, definition.label]),
);

export const AnnotationTypeColors: Record<number, string> = Object.fromEntries(
  DEFAULT_ANNOTATION_TYPE_DEFINITIONS.map((definition) => [definition.value, definition.color]),
);

export const AnnotationTypeIconKeys: Record<number, string> = Object.fromEntries(
  DEFAULT_ANNOTATION_TYPE_DEFINITIONS.map((definition) => [definition.value, definition.icon_key]),
);

export const AnnotationTypeSupportsClasses: Record<number, boolean> = Object.fromEntries(
  DEFAULT_ANNOTATION_TYPE_DEFINITIONS.map((definition) => [definition.value, definition.supports_classes]),
);

export const getAnnotationTypeModel = (annotationType: number): AnnotationTypeModel | undefined => {
  return DefaultAnnotationTypeRegistry[annotationType];
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
  default_ai_pipeline_binding_id: number | null;
  dataset_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface AnnotationRecord {
  id: number;
  annotation_id: number;
  sample_item_id: number;
  annotation_type: number;
  status: string;
  content: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface AnnotationRecordSaveRequest {
  sample_item_id: number;
  content: Record<string, unknown>;
  status?: string;
}

export interface AnnotationAssistRequest {
  sample_item_id: number;
  pipeline_id?: string;
  binding_id?: number;
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

export interface AnnotationAiPipelineBinding {
  id: number;
  binding_type: string;
  binding_target_id: number;
  template_id: number;
  template_version: number;
  template_key?: string | null;
  template_name?: string | null;
  name?: string | null;
  description?: string | null;
  pipeline_type?: string | null;
  supported_annotation_types: number[];
  supported_shapes: string[];
  enabled: boolean;
  is_default: boolean;
  runtime_input_defaults_json?: Record<string, unknown> | unknown[] | string | null;
  resource_bindings_json?: Record<string, unknown> | unknown[] | string | null;
  created_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AnnotationAssistItem {
  label: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  confidence?: number | null;
  source?: string | null;
}

export interface AnnotationAssistResponse {
  sample_item_id: number;
  item_key: string;
  image_width: number;
  image_height: number;
  annotations: AnnotationAssistItem[];
  replace_existing: boolean;
  debug?: Record<string, unknown> | null;
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
