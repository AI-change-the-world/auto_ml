/** 训练任务创建请求 */
export interface TaskCreate {
  task_type: number;
  dataset_id: number;
  annotation_id?: number;
  config?: string;
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
}

/** 任务状态枚举 */
export enum TaskStatus {
  Pending = 0,
  Running = 1,
  PostProcess = 2,
  Completed = 3,
  Failed = 4,
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
