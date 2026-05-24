import apiClient from './client';
import type {
  Result,
  PageResult,
  AnnotationProject,
  AnnotationRecord,
  AnnotationRecordSaveRequest,
  AnnotationAssistRequest,
  AnnotationAssistResponse,
  AnnotationAssistPipeline,
  AnnotationAiPipelineBinding,
  AnnotationCreate,
  AnnotationTypeDefinition,
} from '../types';

/** 创建标注项目 */
export async function createAnnotation(data: AnnotationCreate) {
  const res = await apiClient.post<Result<AnnotationProject>>('/annotation/new', data);
  return res.data.data;
}

/** 获取标注项目列表 */
export async function listAnnotations(page = 1, pageSize = 10, keyword?: string) {
  const params: Record<string, unknown> = { page, page_size: pageSize };
  if (keyword) params.keyword = keyword;
  const res = await apiClient.get<Result<PageResult<AnnotationProject>>>('/annotation/list', { params });
  return res.data.data;
}

export async function getAnnotationSummary() {
  const res = await apiClient.get<Result<{
    total: number;
    recent_annotations: AnnotationProject[];
  }>>('/annotation/summary');
  return res.data.data;
}

/** 获取当前后端支持的标注类型 */
export async function listAnnotationTypes() {
  const res = await apiClient.get<Result<AnnotationTypeDefinition[]>>('/annotation/types');
  return res.data.data ?? [];
}

/** 获取标注项目详情 */
export async function getAnnotation(annotationId: number) {
  const res = await apiClient.get<Result<AnnotationProject>>(`/annotation/${annotationId}`);
  return res.data.data;
}

/** 更新标注项目 */
export async function updateAnnotation(
  annotationId: number,
  data: {
    name?: string;
    classes?: string;
    prompt?: string;
    assist_pipeline?: string | null;
    default_ai_pipeline_binding_id?: number | null;
  },
) {
  const res = await apiClient.put<Result<AnnotationProject>>(`/annotation/${annotationId}`, data);
  return res.data.data;
}

/** 删除标注项目 */
export async function deleteAnnotation(annotationId: number) {
  const res = await apiClient.delete<Result<unknown>>(`/annotation/${annotationId}`);
  return res.data;
}

/** 获取标注记录列表 */
export async function getAnnotationRecords(annotationId: number, page = 1, pageSize = 500) {
  const res = await apiClient.get<Result<PageResult<AnnotationRecord>>>(`/annotation/${annotationId}/records`, {
    params: { page, page_size: pageSize },
  });
  return res.data.data;
}

/** 按样本批量获取标注记录 */
export async function getAnnotationRecordsBySamples(annotationId: number, sampleItemIds: number[]) {
  const res = await apiClient.post<Result<AnnotationRecord[]>>(`/annotation/${annotationId}/records/by-samples`, {
    sample_item_ids: sampleItemIds,
  });
  return res.data.data ?? [];
}

/** 保存样本标注记录 */
export async function saveAnnotationRecord(annotationId: number, data: AnnotationRecordSaveRequest) {
  const res = await apiClient.post<Result<AnnotationRecord>>(`/annotation/${annotationId}/records`, data);
  return res.data.data;
}

/** 辅助标注当前图片 */
export async function assistCurrentAnnotation(annotationId: number, data: AnnotationAssistRequest) {
  const res = await apiClient.post<Result<AnnotationAssistResponse>>(
    `/annotation/${annotationId}/assist/current`,
    data,
    { timeout: 180000 },
  );
  return res.data.data;
}

/** 获取当前标注项目可用的辅助标注 Pipeline */
export async function listAnnotationAssistPipelines(annotationId: number, shape?: string) {
  const res = await apiClient.get<Result<AnnotationAssistPipeline[]>>(`/annotation/${annotationId}/assist/pipelines`, {
    params: shape ? { shape } : undefined,
  });
  return res.data.data;
}

export async function listPlatformAssistPipelines() {
  const res = await apiClient.get<Result<Array<AnnotationAssistPipeline & {
    steps: {
      name: string;
      capability: string;
      provider?: string | null;
    }[];
  }>>>('/annotation/assist/pipelines/platform');
  return res.data.data ?? [];
}

/** 获取当前标注项目可用的 AI Pipeline 绑定 */
export async function listAnnotationAiPipelineBindings(annotationId: number) {
  const res = await apiClient.get<Result<AnnotationAiPipelineBinding[]>>(`/annotation/${annotationId}/ai-pipeline-bindings`);
  return res.data.data ?? [];
}

/** 导出 DPO 标注结果 */
export async function exportDpoAnnotation(annotationId: number) {
  const res = await apiClient.get(`/annotation/${annotationId}/export/dpo`, {
    responseType: 'blob',
  });
  return res.data as Blob;
}
