/** 预测请求 */
export interface PredictRequest {
  source: string;
  model_id: number;
  task_type?: string;
}

/** 预测任务响应 */
export interface PredictTaskResponse {
  id: number;
  task_type: string | null;
  source: string | null;
  result: string | null;
  status: number;
  model_id: number | null;
  created_at: string;
}

/** 预测状态枚举 */
export enum PredictStatus {
  Pending = 0,
  Processing = 1,
  Failed = 2,
  Completed = 3,
}

export const PredictStatusLabels: Record<number, string> = {
  [PredictStatus.Pending]: '等待中',
  [PredictStatus.Processing]: '处理中',
  [PredictStatus.Failed]: '失败',
  [PredictStatus.Completed]: '已完成',
};

export const PredictStatusColors: Record<number, string> = {
  [PredictStatus.Pending]: 'default',
  [PredictStatus.Processing]: 'processing',
  [PredictStatus.Failed]: 'error',
  [PredictStatus.Completed]: 'success',
};
