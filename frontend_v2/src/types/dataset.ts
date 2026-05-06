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
  conversation?: {
    mode?: 'llm' | 'mllm';
    result_format?: 'json';
    roles?: string[];
    primary_input?: 'text' | 'image';
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

export interface Asset {
  id: number;
  dataset_id: number;
  asset_type: string;
  file_name: string;
  save_path: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  meta_json: string | null;
  created_at: string;
}

export interface SampleItem {
  id: number;
  dataset_id: number;
  asset_id: number | null;
  item_type: string;
  item_key: string;
  locator: Record<string, unknown> | null;
  payload: Record<string, unknown> | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
  asset?: Asset | null;
}

export interface SampleItemCreate {
  item_type: string;
  item_key: string;
  locator?: Record<string, unknown> | null;
  payload?: Record<string, unknown> | null;
}

export interface SampleItemUpdate {
  item_key?: string;
  locator?: Record<string, unknown> | null;
  payload?: Record<string, unknown> | null;
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
  LLMConversation: 2,
  MLLMConversation: 3,
} as const;

export type DatasetScenarioTypeValue =
  (typeof DatasetScenarioType)[keyof typeof DatasetScenarioType];

export const DatasetScenarioLabels: Record<number, string> = {
  [DatasetScenarioType.Normal]: '普通',
  [DatasetScenarioType.AerialStitch]: '无人机航拍/拼接',
  [DatasetScenarioType.LLMConversation]: 'LLM 对话标注',
  [DatasetScenarioType.MLLMConversation]: 'MLLM 对话标注',
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

export const createDefaultLlmScenarioConfig = (): DatasetScenarioConfig => ({
  conversation: {
    mode: 'llm',
    result_format: 'json',
    roles: ['system', 'user', 'assistant'],
    primary_input: 'text',
  },
});

export const createDefaultMllmScenarioConfig = (): DatasetScenarioConfig => ({
  conversation: {
    mode: 'mllm',
    result_format: 'json',
    roles: ['system', 'user', 'assistant'],
    primary_input: 'image',
  },
});

export function getDatasetScenarioOptions(dataType: number): Array<{ value: number; label: string }> {
  if (dataType === 0) {
    return [
      { value: DatasetScenarioType.Normal, label: '普通图像' },
      { value: DatasetScenarioType.AerialStitch, label: DatasetScenarioLabels[DatasetScenarioType.AerialStitch] },
      { value: DatasetScenarioType.MLLMConversation, label: DatasetScenarioLabels[DatasetScenarioType.MLLMConversation] },
    ];
  }

  if (dataType === 1) {
    return [
      { value: DatasetScenarioType.Normal, label: '普通文本' },
      { value: DatasetScenarioType.LLMConversation, label: DatasetScenarioLabels[DatasetScenarioType.LLMConversation] },
    ];
  }

  if (dataType === 2) {
    return [{ value: DatasetScenarioType.Normal, label: '普通视频' }];
  }

  if (dataType === 3) {
    return [{ value: DatasetScenarioType.Normal, label: '普通音频' }];
  }

  return [{ value: DatasetScenarioType.Normal, label: DatasetScenarioLabels[DatasetScenarioType.Normal] }];
}

export function getDatasetScenarioLabel(dataType: number, scenarioType: number): string {
  const matched = getDatasetScenarioOptions(dataType).find((item) => item.value === scenarioType);
  return matched?.label ?? DatasetScenarioLabels[scenarioType] ?? DatasetScenarioLabels[DatasetScenarioType.Normal];
}

export function createDefaultScenarioConfig(
  dataType: number,
  scenarioType: number,
): DatasetScenarioConfig | null {
  if (scenarioType === DatasetScenarioType.AerialStitch && dataType === 0) {
    return createDefaultAerialScenarioConfig();
  }
  if (scenarioType === DatasetScenarioType.LLMConversation && dataType === 1) {
    return createDefaultLlmScenarioConfig();
  }
  if (scenarioType === DatasetScenarioType.MLLMConversation && dataType === 0) {
    return createDefaultMllmScenarioConfig();
  }
  return null;
}

export function isLlmConversationDataset(dataType: number, scenarioType: number): boolean {
  return dataType === 1 && scenarioType === DatasetScenarioType.LLMConversation;
}

export function isMllmConversationDataset(dataType: number, scenarioType: number): boolean {
  return dataType === 0 && scenarioType === DatasetScenarioType.MLLMConversation;
}

/** 文件预览响应 */
export interface FilePreviewResponse {
  file_name: string;
  presigned_url: string;
}

export interface FileContentResponse {
  file_name: string;
  content: string;
}
