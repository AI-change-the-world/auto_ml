import apiClient from './client';
import type { Result, PageResult, AvailableModelResponse, DeployStatusResponse } from '../types';

/** 获取可用模型列表 */
export async function listModels(page = 1, pageSize = 10, deployedOnly?: boolean) {
  const params: Record<string, unknown> = { page, page_size: pageSize };
  if (deployedOnly !== undefined) params.deployed_only = deployedOnly;
  const res = await apiClient.get<Result<PageResult<AvailableModelResponse>>>('/deploy/models', { params });
  return res.data.data;
}

/** 部署模型 */
export async function deployModel(modelId: number, device = 'cpu', version = 'v1') {
  const res = await apiClient.post<Result<DeployStatusResponse>>(`/deploy/${modelId}/deploy`, null, {
    params: { device, version },
  });
  return res.data.data;
}

/** 卸载模型 */
export async function undeployModel(modelId: number) {
  const res = await apiClient.post<Result<DeployStatusResponse>>(`/deploy/${modelId}/undeploy`);
  return res.data.data;
}

/** 获取部署状态 */
export async function getDeployStatus(modelId: number) {
  const res = await apiClient.get<Result<DeployStatusResponse>>(`/deploy/${modelId}/status`);
  return res.data.data;
}
