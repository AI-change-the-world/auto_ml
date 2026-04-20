/** 数据集创建请求 */
export interface DatasetCreate {
  name: string;
  storage_type?: number;
  data_type?: number;
  scenario_type?: number;
  scenario_config?: DatasetScenarioConfig | null;
  description?: string;
}

/** 数据集更新请求 */
export interface DatasetUpdate {
  name?: string;
  scenario_type?: number;
  scenario_config?: DatasetScenarioConfig | null;
  description?: string;
}

export interface DatasetScenarioConfig {
  grouping?: {
    strategy?: string;
    pattern_hint?: string;
    sequence_order?: string;
  };
  stitching?: {
    enabled?: boolean;
    allow_missing_tiles?: boolean;
    skip_invalid_files?: boolean;
    default_overlap_ratio?: number;
    manual_alignment_required?: boolean;
  };
  annotation?: {
    coordinate_source?: string;
    support_tile_annotation?: boolean;
    support_mosaic_annotation?: boolean;
  };
  training?: {
    default_views?: string[];
    allow_view_specific_models?: boolean;
  };
  [key: string]: unknown;
}

/** 数据集响应 */
export interface Dataset {
  id: number;
  name: string;
  storage_type: number;
  data_type: number;
  scenario_type: number;
  scenario_config: DatasetScenarioConfig | null;
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

export const DatasetScenarioType = {
  Normal: 0,
  AerialStitch: 1,
} as const;

export type DatasetScenarioTypeValue =
  (typeof DatasetScenarioType)[keyof typeof DatasetScenarioType];

export const DatasetScenarioLabels: Record<number, string> = {
  [DatasetScenarioType.Normal]: '普通图像',
  [DatasetScenarioType.AerialStitch]: '无人机航拍/拼接',
};

export const createDefaultAerialScenarioConfig = (): DatasetScenarioConfig => ({
  grouping: {
    strategy: 'filename_prefix',
    pattern_hint: '{scene}_{rows}x{cols}_r{row}_c{col}.jpg',
    sequence_order: 'row_major',
  },
  stitching: {
    enabled: true,
    allow_missing_tiles: true,
    skip_invalid_files: true,
    default_overlap_ratio: 0.2,
    manual_alignment_required: false,
  },
  annotation: {
    coordinate_source: 'global',
    support_tile_annotation: true,
    support_mosaic_annotation: true,
  },
  training: {
    default_views: ['tile', 'mosaic'],
    allow_view_specific_models: true,
  },
});

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
