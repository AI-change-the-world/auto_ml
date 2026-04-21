import apiClient from './client';
import type {
  Result,
  PageResult,
  AnnotationProject,
  AnnotationFile,
  AnnotationFileSaveRequest,
  AnnotationAssistRequest,
  AnnotationAssistResponse,
  AnnotationAssistPipeline,
  AnnotationCreate,
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

/** 获取标注项目详情 */
export async function getAnnotation(annotationId: number) {
  const res = await apiClient.get<Result<AnnotationProject>>(`/annotation/${annotationId}`);
  return res.data.data;
}

/** 更新标注项目 */
export async function updateAnnotation(annotationId: number, data: { name?: string; classes?: string; prompt?: string; assist_pipeline?: string | null }) {
  const res = await apiClient.put<Result<AnnotationProject>>(`/annotation/${annotationId}`, data);
  return res.data.data;
}

/** 删除标注项目 */
export async function deleteAnnotation(annotationId: number) {
  const res = await apiClient.delete<Result<unknown>>(`/annotation/${annotationId}`);
  return res.data;
}

/** 获取标注文件列表 */
export async function getAnnotationFiles(annotationId: number, page = 1, pageSize = 100) {
  const res = await apiClient.get<Result<PageResult<AnnotationFile>>>(`/annotation/${annotationId}/files`, {
    params: { page, page_size: pageSize },
  });
  return res.data.data;
}

/** 保存标注文件 */
export async function saveAnnotationFile(annotationId: number, data: AnnotationFileSaveRequest) {
  const res = await apiClient.post<Result<number>>(`/annotation/${annotationId}/file`, data);
  return res.data.data;
}

/** 辅助标注当前图片 */
export async function assistCurrentAnnotation(annotationId: number, data: AnnotationAssistRequest) {
  const res = await apiClient.post<Result<AnnotationAssistResponse>>(`/annotation/${annotationId}/assist/current`, data);
  return res.data.data;
}

/** 获取当前标注项目可用的辅助标注 Pipeline */
export async function listAnnotationAssistPipelines(annotationId: number, shape?: string) {
  const res = await apiClient.get<Result<AnnotationAssistPipeline[]>>(`/annotation/${annotationId}/assist/pipelines`, {
    params: shape ? { shape } : undefined,
  });
  return res.data.data;
}
