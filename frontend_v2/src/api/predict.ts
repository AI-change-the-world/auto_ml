import apiClient from './client';
import type { Result, PageResult, PredictRequest, PredictTaskResponse } from '../types';

/** 图像预测 */
export async function predictImage(data: PredictRequest) {
  const res = await apiClient.post<Result<{ task_id: number }>>('/predict/image', data);
  return res.data.data;
}

/** 预测任务列表 */
export async function listPredictTasks(page = 1, pageSize = 10) {
  const res = await apiClient.get<Result<PageResult<PredictTaskResponse>>>('/predict/list', {
    params: { page, page_size: pageSize },
  });
  return res.data.data;
}

/** 获取预测结果 */
export async function getPredictResult(taskId: number) {
  const res = await apiClient.get<Result<{ task_id: number; status: number; result: string | null }>>(`/predict/${taskId}/result`);
  return res.data.data;
}
