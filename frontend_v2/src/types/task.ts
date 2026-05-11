export interface TaskSourceItem {
  dataset_id: number;
  annotation_id: number;
}

export interface TaskSourceResponse {
  id: number;
  task_id: number;
  dataset_id: number;
  annotation_id: number;
  source_order: number;
  source_name: string | null;
}

/** 训练任务创建请求 */
export interface TaskCreate {
  task_type: number;
  dataset_id?: number;
  annotation_id?: number;
  sources?: TaskSourceItem[];
  config?: string;
}

export interface TrainingConfigPayload {
  name?: string;
  epoch: number;
  size: number;
  batch: number;
  device: string;
  label_format?: 'auto' | 'bbox' | 'obb';
  export_onnx?: boolean;
  onnx_dynamic?: boolean;
  onnx_simplify?: boolean;
  dataset_cache_mode?: 'off' | 'reuse' | 'refresh';
  resume_model_id?: number;
  augmentation?: TrainingAugmentationConfig;
  optimizer_config?: TrainingOptimizerConfig;
}

export interface TrainingHistoryQuery {
  task_type: number;
  sources: TaskSourceItem[];
  label_format?: 'auto' | 'bbox' | 'obb';
}

export interface TrainingHistoryCandidateResponse {
  model_id: number;
  task_id: number;
  model_name: string;
  model_path: string | null;
  model_type: string | null;
  base_model_name: string | null;
  dataset_id: number | null;
  annotation_id: number | null;
  source_count: number;
  created_at: string;
}

export interface TrainingAugmentationConfig {
  enabled: boolean;
  degrees?: number;
  translate?: number;
  scale?: number;
  shear?: number;
  perspective?: number;
  fliplr?: number;
  flipud?: number;
  hsv_h?: number;
  hsv_s?: number;
  hsv_v?: number;
  mosaic?: number;
  mixup?: number;
  copy_paste?: number;
  close_mosaic?: number;
  auto_augment?: 'randaugment' | 'autoaugment' | 'augmix' | 'none';
  erasing?: number;
}

export interface TrainingOptimizerConfig {
  optimizer?: 'auto' | 'SGD' | 'Adam' | 'AdamW' | 'Adamax' | 'NAdam' | 'RAdam' | 'RMSProp';
  patience?: number;
  lr0?: number;
  lrf?: number;
  momentum?: number;
  weight_decay?: number;
  warmup_epochs?: number;
  cos_lr?: boolean;
}

/** 训练任务响应 */
export interface TaskResponse {
  id: number;
  task_type: number;
  dataset_id: number | null;
  annotation_id: number | null;
  status: number;
  config: string | null;
  result: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  is_stale?: boolean;
  stale_seconds?: number | null;
  sources?: TaskSourceResponse[];
}

/** 任务状态枚举 */
export enum TaskStatus {
  Pending = 0,
  Running = 1,
  PostProcess = 2,
  Completed = 3,
  Failed = 4,
}

export enum TaskType {
  Detection = 0,
  Classification = 1,
  Segmentation = 2,
  Pose = 3,
}

export const TaskStatusLabels: Record<number, string> = {
  [TaskStatus.Pending]: '排队中',
  [TaskStatus.Running]: '运行中',
  [TaskStatus.PostProcess]: '后处理',
  [TaskStatus.Completed]: '已完成',
  [TaskStatus.Failed]: '失败',
};

export const TaskStatusColors: Record<number, string> = {
  [TaskStatus.Pending]: 'default',
  [TaskStatus.Running]: 'processing',
  [TaskStatus.PostProcess]: 'processing',
  [TaskStatus.Completed]: 'success',
  [TaskStatus.Failed]: 'error',
};

/** 任务日志响应 */
export interface TaskLogResponse {
  id: number;
  task_id: number;
  content: string | null;
  log_level: string;
  created_at: string;
}

/** 基础模型响应 */
export interface BaseModelResponse {
  id: number;
  name: string;
  model_type: string | null;
  description: string | null;
  save_path: string | null;
  created_at: string;
}

export interface TrainerStatusResponse {
  reachable: boolean;
  status: string;
  version: string | null;
  mq_connected: boolean;
  max_concurrent: number;
  active_tasks: number;
  queued_tasks: number;
  message: string | null;
}

export interface TaskStreamEnvelope {
  event: 'task_upsert' | 'task_log' | 'trainer_status';
  data: {
    task?: TaskResponse;
    log?: TaskLogResponse;
    trainer_status?: TrainerStatusResponse;
  };
}
