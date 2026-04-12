import { v4 as uuidv4 } from 'uuid';

/** 标注模式 */
export enum LabelMode {
  Edit = 'edit',
  Add = 'add',
}

/** 边界框标注 */
export interface BBoxAnnotation {
  uuid: string;
  x: number;
  y: number;
  width: number;
  height: number;
  classId: number;
  visible: boolean;
  selected: boolean;
}

/** 创建新的边界框标注 */
export function createBBoxAnnotation(
  x: number,
  y: number,
  width: number,
  height: number,
  classId: number = -1,
): BBoxAnnotation {
  return {
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
  dataset_id?: number;
}

/** 标注类型标签 */
export const AnnotationTypeLabels: Record<number, string> = {
  0: '检测',
  1: '分类',
  2: '分割',
  3: 'MLLM',
};

export const AnnotationTypeColors: Record<number, string> = {
  0: 'blue',
  1: 'green',
  2: 'orange',
  3: 'purple',
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

/** 标注类型枚举 */
export enum AnnotationType {
  Detection = 0,
  Classification = 1,
  Segmentation = 2,
  MLLM = 3,
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
