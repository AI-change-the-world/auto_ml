import apiClient from './client';
import type {
  Result,
  TrainingRuntimeCodePackage,
  TrainingRuntimeCodePackageImportResponse,
} from '../types';

export async function listTrainingRuntimeCodePackages(includeDisabled = true) {
  const response = await apiClient.get<Result<TrainingRuntimeCodePackage[]>>(
    '/training-runtime/code-packages',
    { params: { include_disabled: includeDisabled } },
  );
  return response.data.data ?? [];
}

export async function importTrainingRuntimeCodePackage(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<Result<TrainingRuntimeCodePackageImportResponse>>(
    '/training-runtime/code-packages/import',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 },
  );
  return response.data.data;
}

export async function getTrainingRuntimeCodePackage(packageId: number) {
  const response = await apiClient.get<Result<TrainingRuntimeCodePackage>>(
    `/training-runtime/code-packages/${packageId}`,
  );
  return response.data.data;
}

export async function updateTrainingRuntimeCodePackage(packageId: number, data: { enabled: boolean }) {
  const response = await apiClient.patch<Result<TrainingRuntimeCodePackage>>(
    `/training-runtime/code-packages/${packageId}`,
    data,
  );
  return response.data.data;
}

export async function deleteTrainingRuntimeCodePackage(packageId: number) {
  const response = await apiClient.delete<Result<unknown>>(
    `/training-runtime/code-packages/${packageId}`,
  );
  return response.data;
}
