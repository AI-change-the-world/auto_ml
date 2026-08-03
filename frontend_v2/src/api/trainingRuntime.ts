import apiClient from './client';
import type {
  Result,
  TrainingRuntimeCodePackage,
  TrainingRuntimeCodePackageImportResponse,
  TrainingRuntimeModelPackage,
  TrainingRuntimeModelPackageImportResponse,
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

export async function listTrainingRuntimeModelPackages(includeDisabled = true) {
  const response = await apiClient.get<Result<TrainingRuntimeModelPackage[]>>(
    '/training-runtime/model-packages',
    { params: { include_disabled: includeDisabled } },
  );
  return response.data.data ?? [];
}

export async function importTrainingRuntimeModelPackage(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<Result<TrainingRuntimeModelPackageImportResponse>>(
    '/training-runtime/model-packages/import',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 },
  );
  return response.data.data;
}
