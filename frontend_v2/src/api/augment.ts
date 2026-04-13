import apiClient from './client';
import type { Result, AugmentCapability, AugmentRequest } from '../types';

/** 获取增强能力列表 */
export async function getAugmentCapabilities() {
  const res = await apiClient.get<Result<AugmentCapability[]>>('/augment/capabilities');
  return res.data.data;
}

/** 执行数据增强 */
export async function processAugment(data: AugmentRequest) {
  const res = await apiClient.post<Result<{ status: string; dataset_id: number; augment_type: string }>>('/augment/process', data);
  return res.data.data;
}
