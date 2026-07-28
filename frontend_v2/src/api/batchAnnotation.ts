import apiClient from './client';
import type {
  AiPipelineBatchRun,
  AiPipelineBatchRunCreateRequest,
  AiPipelineBatchRunEvent,
  AiPipelineBatchRunItem,
  AiPipelineBatchScript,
  AiPipelineBatchScriptUpdateRequest,
  PageResult,
  Result,
} from '../types';

export async function listBatchAnnotationScripts(includeDisabled = false) {
  const res = await apiClient.get<Result<AiPipelineBatchScript[]>>('/ai-pipeline/batch-scripts', {
    params: { include_disabled: includeDisabled },
  });
  return res.data.data ?? [];
}

export async function getBatchAnnotationScript(scriptKey: string) {
  const res = await apiClient.get<Result<AiPipelineBatchScript>>(`/ai-pipeline/batch-scripts/${scriptKey}`);
  return res.data.data;
}

export async function uploadBatchAnnotationScript(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await apiClient.post<Result<AiPipelineBatchScript>>('/ai-pipeline/batch-scripts/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  });
  return res.data.data;
}

export async function updateBatchAnnotationScript(scriptKey: string, data: AiPipelineBatchScriptUpdateRequest) {
  const res = await apiClient.patch<Result<AiPipelineBatchScript>>(`/ai-pipeline/batch-scripts/${scriptKey}`, data);
  return res.data.data;
}

export async function deleteBatchAnnotationScript(scriptKey: string) {
  const res = await apiClient.delete<Result<unknown>>(`/ai-pipeline/batch-scripts/${scriptKey}`);
  return res.data;
}

export async function createBatchAnnotationRun(data: AiPipelineBatchRunCreateRequest) {
  const res = await apiClient.post<Result<AiPipelineBatchRun>>('/ai-pipeline/batch-runs', data);
  return res.data.data;
}

export async function listBatchAnnotationRuns(datasetId?: number, limit = 50, scriptKey?: string) {
  const params: Record<string, number | string> = { limit };
  if (datasetId !== undefined) params.dataset_id = datasetId;
  if (scriptKey) params.script_key = scriptKey;
  const res = await apiClient.get<Result<AiPipelineBatchRun[]>>('/ai-pipeline/batch-runs', {
    params,
  });
  return res.data.data ?? [];
}

export async function getBatchAnnotationRun(runId: string) {
  const res = await apiClient.get<Result<AiPipelineBatchRun>>(`/ai-pipeline/batch-runs/${runId}`);
  return res.data.data;
}

export async function getBatchAnnotationRunEvents(runId: string, afterId = 0) {
  const res = await apiClient.get<Result<AiPipelineBatchRunEvent[]>>(`/ai-pipeline/batch-runs/${runId}/events`, {
    params: { after_id: afterId, limit: 100 },
  });
  return res.data.data ?? [];
}

export async function getBatchAnnotationRunItems(runId: string, page = 1, pageSize = 50, status?: string) {
  const res = await apiClient.get<Result<PageResult<AiPipelineBatchRunItem>>>(`/ai-pipeline/batch-runs/${runId}/items`, {
    params: { page, page_size: pageSize, status },
  });
  return res.data.data;
}

export async function cancelBatchAnnotationRun(runId: string) {
  const res = await apiClient.post<Result<AiPipelineBatchRun>>(`/ai-pipeline/batch-runs/${runId}/cancel`);
  return res.data.data;
}
