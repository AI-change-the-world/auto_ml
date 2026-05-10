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
  preference?: {
    mode?: 'dpo';
    result_format?: 'json';
    task_types?: Array<'pairwise' | 'best_of_n'>;
    default_task_type?: 'pairwise' | 'best_of_n';
    export_strategy?: 'winner_vs_all';
    min_candidates?: number;
    max_candidates?: number;
    primary_input?: 'text';
    allow_tie?: boolean;
    allow_skip?: boolean;
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

export interface DataTypeOption {
  value: number;
  label: string;
  description: string;
}

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
  DPOPreference: 4,
  DpoPairwise: 5,
  DpoBestOfN: 6,
  DpoReferenceChoice: 7,
  DpoMultiTurn: 8,
} as const;

export type DatasetScenarioTypeValue =
  (typeof DatasetScenarioType)[keyof typeof DatasetScenarioType];

export const DatasetScenarioLabels: Record<number, string> = {
  [DatasetScenarioType.Normal]: '普通',
  [DatasetScenarioType.AerialStitch]: '无人机航拍/拼接',
  [DatasetScenarioType.LLMConversation]: 'LLM 对话标注',
  [DatasetScenarioType.MLLMConversation]: 'MLLM 对话标注',
  [DatasetScenarioType.DPOPreference]: 'DPO 偏好标注',
  [DatasetScenarioType.DpoPairwise]: 'DPO 二选一',
  [DatasetScenarioType.DpoBestOfN]: 'DPO 多选一',
  [DatasetScenarioType.DpoReferenceChoice]: 'DPO 参考增强',
  [DatasetScenarioType.DpoMultiTurn]: 'DPO 多轮对话',
};

export interface DatasetScenarioDefinition {
  value: number;
  dataType: number;
  label: string;
  shortLabel: string;
  description: string;
  uploadHint: string;
}

export const DataTypeOptions: DataTypeOption[] = [
  {
    value: 0,
    label: '图像',
    description: '检测、分类、分割、图文对话等图像相关场景',
  },
  {
    value: 1,
    label: '文本',
    description: '普通文本、LLM 对话、DPO 多子类型偏好数据',
  },
  {
    value: 2,
    label: '视频',
    description: '视频文件与后续视频任务数据',
  },
  {
    value: 3,
    label: '音频',
    description: '音频文件与后续语音任务数据',
  },
];

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

export const createDefaultDpoScenarioConfig = (): DatasetScenarioConfig => ({
  preference: {
    mode: 'dpo',
    result_format: 'json',
    task_types: ['pairwise', 'best_of_n'],
    default_task_type: 'pairwise',
    export_strategy: 'winner_vs_all',
    min_candidates: 2,
    max_candidates: 6,
    primary_input: 'text',
    allow_tie: true,
    allow_skip: true,
  },
});

export const createDefaultDpoPairwiseScenarioConfig = (): DatasetScenarioConfig => ({
  preference: {
    mode: 'dpo',
    task_types: ['pairwise'],
    default_task_type: 'pairwise',
    min_candidates: 2,
    max_candidates: 2,
    primary_input: 'text',
    allow_tie: true,
    allow_skip: true,
  },
});

export const createDefaultDpoBestOfNScenarioConfig = (): DatasetScenarioConfig => ({
  preference: {
    mode: 'dpo',
    task_types: ['best_of_n'],
    default_task_type: 'best_of_n',
    export_strategy: 'winner_vs_all',
    min_candidates: 3,
    max_candidates: 6,
    primary_input: 'text',
    allow_tie: true,
    allow_skip: true,
  },
});

export const createDefaultDpoReferenceChoiceScenarioConfig = (): DatasetScenarioConfig => ({
  preference: {
    mode: 'dpo',
    task_types: ['pairwise'],
    default_task_type: 'pairwise',
    min_candidates: 2,
    max_candidates: 4,
    primary_input: 'text',
    allow_tie: true,
    allow_skip: true,
  },
});

export const createDefaultDpoMultiTurnScenarioConfig = (): DatasetScenarioConfig => ({
  preference: {
    mode: 'dpo',
    task_types: ['pairwise'],
    default_task_type: 'pairwise',
    min_candidates: 2,
    max_candidates: 4,
    primary_input: 'text',
    allow_tie: true,
    allow_skip: true,
  },
});

const DATASET_SCENARIO_DEFINITIONS: Record<number, DatasetScenarioDefinition[]> = {
  0: [
    {
      value: DatasetScenarioType.Normal,
      dataType: 0,
      label: '普通图像',
      shortLabel: '普通图像',
      description: '适合检测、分类、分割等通用图像标注任务。',
      uploadHint: '支持常见图像文件，航拍拼接场景除外。',
    },
    {
      value: DatasetScenarioType.AerialStitch,
      dataType: 0,
      label: '无人机航拍/拼接',
      shortLabel: '航拍拼接',
      description: '用于切片、拼接和全景视角联合标注的航拍影像数据。',
      uploadHint: '建议上传命名规范明确的图像或压缩包。',
    },
    {
      value: DatasetScenarioType.MLLMConversation,
      dataType: 0,
      label: 'MLLM 图文对话',
      shortLabel: 'MLLM 对话',
      description: '以图像为输入，标注多模态对话内容。',
      uploadHint: '建议上传图像文件，标注阶段补充对话内容。',
    },
  ],
  1: [
    {
      value: DatasetScenarioType.Normal,
      dataType: 1,
      label: '普通文本',
      shortLabel: '普通文本',
      description: '适合纯文本样本管理和常规文本任务。',
      uploadHint: '建议上传 txt、md、json、jsonl、csv 等文本文件。',
    },
    {
      value: DatasetScenarioType.LLMConversation,
      dataType: 1,
      label: 'LLM 对话',
      shortLabel: 'LLM 对话',
      description: '以文本形式组织多轮对话，标注结果按结构化消息保存。',
      uploadHint: '建议上传文本文件，标注时逐条补充对话内容。',
    },
    {
      value: DatasetScenarioType.DpoPairwise,
      dataType: 1,
      label: 'DPO 二选一',
      shortLabel: '二选一',
      description: '同一提示词下两条候选回复做 A/B 偏好判断。',
      uploadHint: '上传 .jsonl，每条样本固定两条 responses。',
    },
    {
      value: DatasetScenarioType.DpoBestOfN,
      dataType: 1,
      label: 'DPO 多选一',
      shortLabel: '多选一',
      description: '同一提示词下 3 到 6 条候选回复中选出最佳。',
      uploadHint: '上传 .jsonl，每条样本包含 3 到 6 条 responses。',
    },
    {
      value: DatasetScenarioType.DpoReferenceChoice,
      dataType: 1,
      label: 'DPO 参考增强',
      shortLabel: '参考增强',
      description: '基于参考答案或规则说明，对候选回复做偏好判断。',
      uploadHint: '上传 .jsonl，每条样本需包含 reference。',
    },
    {
      value: DatasetScenarioType.DpoMultiTurn,
      dataType: 1,
      label: 'DPO 多轮对话',
      shortLabel: '多轮对话',
      description: '基于完整对话历史，对最终候选回复做偏好判断。',
      uploadHint: '上传 .jsonl，prompt.messages 需包含多轮上下文。',
    },
  ],
  2: [
    {
      value: DatasetScenarioType.Normal,
      dataType: 2,
      label: '普通视频',
      shortLabel: '普通视频',
      description: '适合视频文件管理和后续视频类任务扩展。',
      uploadHint: '支持常见视频文件格式。',
    },
  ],
  3: [
    {
      value: DatasetScenarioType.Normal,
      dataType: 3,
      label: '普通音频',
      shortLabel: '普通音频',
      description: '适合音频文件管理和后续语音类任务扩展。',
      uploadHint: '支持常见音频文件格式。',
    },
  ],
};

export function getDatasetScenarioOptions(dataType: number): Array<{ value: number; label: string }> {
  return getDatasetScenarioDefinitions(dataType).map((item) => ({
    value: item.value,
    label: item.label,
  }));
}

export function getDatasetScenarioDefinitions(dataType: number): DatasetScenarioDefinition[] {
  return DATASET_SCENARIO_DEFINITIONS[dataType] ?? [
    {
      value: DatasetScenarioType.Normal,
      dataType,
      label: DatasetScenarioLabels[DatasetScenarioType.Normal],
      shortLabel: DatasetScenarioLabels[DatasetScenarioType.Normal],
      description: '默认数据集类型。',
      uploadHint: '',
    },
  ];
}

export function getDatasetScenarioDefinition(
  dataType: number,
  scenarioType: number,
): DatasetScenarioDefinition | undefined {
  return getDatasetScenarioDefinitions(dataType).find((item) => item.value === scenarioType);
}

export function getDatasetScenarioLabel(dataType: number, scenarioType: number): string {
  return getDatasetScenarioDefinition(dataType, scenarioType)?.label
    ?? DatasetScenarioLabels[scenarioType]
    ?? DatasetScenarioLabels[DatasetScenarioType.Normal];
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
  if (scenarioType === DatasetScenarioType.DPOPreference && dataType === 1) {
    return createDefaultDpoScenarioConfig();
  }
  if (scenarioType === DatasetScenarioType.DpoPairwise && dataType === 1) {
    return createDefaultDpoPairwiseScenarioConfig();
  }
  if (scenarioType === DatasetScenarioType.DpoBestOfN && dataType === 1) {
    return createDefaultDpoBestOfNScenarioConfig();
  }
  if (scenarioType === DatasetScenarioType.DpoReferenceChoice && dataType === 1) {
    return createDefaultDpoReferenceChoiceScenarioConfig();
  }
  if (scenarioType === DatasetScenarioType.DpoMultiTurn && dataType === 1) {
    return createDefaultDpoMultiTurnScenarioConfig();
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

export function isDpoPreferenceDataset(dataType: number, scenarioType: number): boolean {
  return dataType === 1 && scenarioType === DatasetScenarioType.DPOPreference;
}

export function isDpoPairwiseDataset(dataType: number, scenarioType: number): boolean {
  return dataType === 1 && scenarioType === DatasetScenarioType.DpoPairwise;
}

export function isDpoBestOfNDataset(dataType: number, scenarioType: number): boolean {
  return dataType === 1 && scenarioType === DatasetScenarioType.DpoBestOfN;
}

export function isDpoReferenceChoiceDataset(dataType: number, scenarioType: number): boolean {
  return dataType === 1 && scenarioType === DatasetScenarioType.DpoReferenceChoice;
}

export function isDpoMultiTurnDataset(dataType: number, scenarioType: number): boolean {
  return dataType === 1 && scenarioType === DatasetScenarioType.DpoMultiTurn;
}

export function isAnyDpoDataset(dataType: number, scenarioType: number): boolean {
  const dpoScenarioTypes: number[] = [
    DatasetScenarioType.DPOPreference,
    DatasetScenarioType.DpoPairwise,
    DatasetScenarioType.DpoBestOfN,
    DatasetScenarioType.DpoReferenceChoice,
    DatasetScenarioType.DpoMultiTurn,
  ];

  return dataType === 1 && dpoScenarioTypes.includes(scenarioType);
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
