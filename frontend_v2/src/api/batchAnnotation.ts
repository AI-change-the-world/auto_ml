import apiClient from './client';
import type {
  AiPipelineBatchRun,
  AiPipelineBatchRunCreateRequest,
  AiPipelineBatchRunEvent,
  AiPipelineBatchRunItem,
  AiPipelineBatchScript,
  PageResult,
  Result,
} from '../types';

export async function listBatchAnnotationScripts() {
  const res = await apiClient.get<Result<AiPipelineBatchScript[]>>('/ai-pipeline/batch-scripts');
  return res.data.data ?? [];
}

export async function createBatchAnnotationRun(data: AiPipelineBatchRunCreateRequest) {
  const res = await apiClient.post<Result<AiPipelineBatchRun>>('/ai-pipeline/batch-runs', data);
  return res.data.data;
}

export async function listBatchAnnotationRuns(datasetId: number, limit = 50) {
  const res = await apiClient.get<Result<AiPipelineBatchRun[]>>('/ai-pipeline/batch-runs', {
    params: { dataset_id: datasetId, limit },
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

export async function getBatchAnnotationRunItems(runId: string, status?: string) {
  const res = await apiClient.get<Result<PageResult<AiPipelineBatchRunItem>>>(`/ai-pipeline/batch-runs/${runId}/items`, {
    params: { page: 1, page_size: 100, status },
  });
  return res.data.data;
}

export async function cancelBatchAnnotationRun(runId: string) {
  const res = await apiClient.post<Result<AiPipelineBatchRun>>(`/ai-pipeline/batch-runs/${runId}/cancel`);
  return res.data.data;
}
