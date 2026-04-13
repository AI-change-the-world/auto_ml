import apiClient from './client';
import type { Result, PageResult, Dataset, DatasetFile, FilePreviewResponse, DatasetCreate, DatasetUpdate } from '../types';

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

/** 获取数据集文件列表 */
export async function getDatasetFiles(datasetId: number, page = 1, pageSize = 500) {
  const res = await apiClient.get<Result<PageResult<DatasetFile>>>(`/dataset/${datasetId}/files`, {
    params: { page, page_size: pageSize },
  });
  return res.data.data;
}

/** 预览文件 */
export async function previewFile(datasetId: number, fileName: string) {
  const res = await apiClient.get<Result<FilePreviewResponse>>(`/dataset/${datasetId}/preview`, {
    params: { file_name: fileName },
  });
  return res.data.data;
}

/** 删除单个文件 */
export async function deleteDatasetFile(datasetId: number, fileId: number) {
  const res = await apiClient.delete<Result<unknown>>(`/dataset/${datasetId}/files/${fileId}`);
  return res.data;
}

/** 批量删除文件 */
export async function batchDeleteDatasetFiles(datasetId: number, fileIds: number[]) {
  const res = await apiClient.post<Result<number>>(`/dataset/${datasetId}/files/batch-delete`, { file_ids: fileIds });
  return res.data.data;
}
