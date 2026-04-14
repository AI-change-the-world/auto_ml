import apiClient from './client';
import type { Result, PageResult, TaskCreate, TaskResponse, TaskLogResponse, BaseModelResponse, TrainerStatusResponse } from '../types';

/** 创建训练任务 */
export async function createTrainTask(data: TaskCreate) {
  const res = await apiClient.post<Result<TaskResponse>>('/task/train', data);
  return res.data.data;
}

/** 获取任务列表 */
export async function listTasks(page = 1, pageSize = 10, status?: number) {
  const params: Record<string, unknown> = { page, page_size: pageSize };
  if (status !== undefined && status !== null) params.status = status;
  const res = await apiClient.get<Result<PageResult<TaskResponse>>>('/task/list', { params });
  return res.data.data;
}

/** 获取任务详情 */
export async function getTask(taskId: number) {
  const res = await apiClient.get<Result<TaskResponse>>(`/task/${taskId}`);
  return res.data.data;
}

/** 获取任务日志 */
export async function getTaskLogs(taskId: number, page = 1, pageSize = 100) {
  const res = await apiClient.get<Result<PageResult<TaskLogResponse>>>(`/task/${taskId}/logs`, {
    params: { page, page_size: pageSize },
  });
  return res.data.data;
}

/** 获取基础模型列表 */
export async function getBaseModels() {
  const res = await apiClient.get<Result<BaseModelResponse[]>>('/task/base-models');
  return res.data.data;
}

/** 获取训练服务状态 */
export async function getTrainerStatus() {
  const res = await apiClient.get<Result<TrainerStatusResponse>>('/task/trainer/status');
  return res.data.data;
}
