import { getAnnotationFiles } from '../../../api/annotation';
import { getDatasetFiles } from '../../../api/dataset';
import type { DatasetFile } from '../../../types';

const API_BATCH_SIZE = 500;

export async function loadAllDatasetFiles(datasetId: number): Promise<DatasetFile[]> {
  let page = 1;
  let totalPages = 1;
  const items: DatasetFile[] = [];

  while (page <= totalPages) {
    const response = await getDatasetFiles(datasetId, page, API_BATCH_SIZE);
    items.push(...(response.items || []));
    totalPages = response.pages || 1;
    page += 1;
  }

  return items;
}

export async function loadAllAnnotationFiles(annotationId: number) {
  let page = 1;
  let totalPages = 1;
  const items: Array<{ file_name: string; content: string | null }> = [];

  while (page <= totalPages) {
    const response = await getAnnotationFiles(annotationId, page, API_BATCH_SIZE);
    items.push(...(response.items || []));
    totalPages = response.pages || 1;
    page += 1;
  }

  return items;
}
