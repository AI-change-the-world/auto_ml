import apiClient from './client';
import type {
  Result,
  PageResult,
  AvailableModelResponse,
  DeployStatusResponse,
  InferenceParams,
  InferencePredictResponse,
  InferenceHealthResponse,
  RenameModelRequest,
} from '../types';

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

/** 获取推理健康状态 */
export async function getInferenceHealth(modelId: number) {
  const res = await apiClient.get<Result<InferenceHealthResponse>>(`/inference/models/${modelId}/health`);
  return res.data.data;
}

/** 上传图片执行推理 */
export async function predictModel(modelId: number, file: File, inferenceParams?: InferenceParams | null) {
  const formData = new FormData();
  formData.append('file', file);
  if (inferenceParams && Object.keys(inferenceParams).length > 0) {
    formData.append('inference_params', JSON.stringify(inferenceParams));
  }
  const res = await apiClient.post<Result<InferencePredictResponse>>(
    `/inference/models/${modelId}/predict`,
    formData,
    {
      timeout: 120000,
    },
  );
  return res.data.data;
}

/** 重命名模型 */
export async function renameModel(modelId: number, data: RenameModelRequest) {
  const res = await apiClient.patch<Result<AvailableModelResponse>>(`/deploy/${modelId}/rename`, data);
  return res.data.data;
}
