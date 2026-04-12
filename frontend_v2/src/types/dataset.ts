/** 数据集创建请求 */
export interface DatasetCreate {
  name: string;
  storage_type?: number;
  data_type?: number;
  description?: string;
}

/** 数据集更新请求 */
export interface DatasetUpdate {
  name?: string;
  description?: string;
}

/** 数据集响应 */
export interface Dataset {
  id: number;
  name: string;
  storage_type: number;
  data_type: number;
  save_path: string | null;
  count: number;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export const DataTypeLabels: Record<number, string> = {
  0: '图像',
  1: '文本',
  2: '视频',
  3: '音频',
};

export const DataTypeIcons: Record<number, string> = {
  0: 'picture',
  1: 'file-text',
  2: 'video-camera',
  3: 'audio',
};

/** 数据集文件响应 */
export interface DatasetFile {
  id: number;
  dataset_id: number;
  file_name: string;
  save_path: string | null;
  created_at: string;
}

/** 文件预览响应 */
export interface FilePreviewResponse {
  file_name: string;
  presigned_url: string;
}
