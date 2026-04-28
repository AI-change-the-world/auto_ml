import apiClient from './client';
import type {
  Result,
  PageResult,
  Dataset,
  FilePreviewResponse,
  FileContentResponse,
  DatasetCreate,
  DatasetUpdate,
  SampleItem,
  SampleItemCreate,
  SampleItemUpdate,
} from '../types';

/** 创建数据集 */
export async function createDataset(data: DatasetCreate) {
  const res = await apiClient.post<Result<Dataset>>('/dataset/new', data);
  return res.data.data;
}

/** 获取数据集列表 */
export async function listDatasets(page = 1, pageSize = 10, keyword?: string) {
  const params: Record<string, unknown> = { page, page_size: pageSize };
  if (keyword) params.keyword = keyword;
  const res = await apiClient.get<Result<PageResult<Dataset>>>('/dataset/list', { params });
  return res.data.data;
}

/** 获取数据集详情 */
export async function getDataset(datasetId: number) {
  const res = await apiClient.get<Result<Dataset>>(`/dataset/${datasetId}`);
  return res.data.data;
}

/** 更新数据集 */
export async function updateDataset(datasetId: number, data: DatasetUpdate) {
  const res = await apiClient.put<Result<Dataset>>(`/dataset/${datasetId}`, data);
  return res.data.data;
}

/** 删除数据集 */
export async function deleteDataset(datasetId: number) {
  const res = await apiClient.delete<Result<unknown>>(`/dataset/${datasetId}`);
  return res.data;
}

/** 上传文件到数据集 */
export async function uploadDatasetFiles(datasetId: number, files: File[]) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const res = await apiClient.post<Result<number>>(`/dataset/${datasetId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  });
  return res.data.data;
}

/** 获取数据集样本列表 */
export async function getDatasetSamples(datasetId: number, page = 1, pageSize = 500, itemType?: string) {
  const res = await apiClient.get<Result<PageResult<SampleItem>>>(`/dataset/${datasetId}/samples`, {
    params: { page, page_size: pageSize, item_type: itemType },
  });
  return res.data.data;
}

/** 创建数据集样本 */
export async function createDatasetSample(datasetId: number, data: SampleItemCreate) {
  const res = await apiClient.post<Result<SampleItem>>(`/dataset/${datasetId}/samples`, data);
  return res.data.data;
}

/** 更新数据集样本 */
export async function updateDatasetSample(datasetId: number, sampleItemId: number, data: SampleItemUpdate) {
  const res = await apiClient.put<Result<SampleItem>>(`/dataset/${datasetId}/samples/${sampleItemId}`, data);
  return res.data.data;
}

/** 删除数据集样本 */
export async function deleteDatasetSample(datasetId: number, sampleItemId: number) {
  const res = await apiClient.delete<Result<unknown>>(`/dataset/${datasetId}/samples/${sampleItemId}`);
  return res.data;
}

/** 预览样本资源 */
export async function previewSample(datasetId: number, sampleItemId: number) {
  const res = await apiClient.get<Result<FilePreviewResponse>>(`/dataset/${datasetId}/samples/${sampleItemId}/preview`);
  return res.data.data;
}

/** 读取样本文本内容 */
export async function getDatasetSampleContent(datasetId: number, sampleItemId: number) {
  const res = await apiClient.get<Result<FileContentResponse>>(`/dataset/${datasetId}/samples/${sampleItemId}/content`);
  return res.data.data;
}
