import type { SampleItem } from '../types';
import { isImageFileName } from './file';

export function getSampleItemName(sample: SampleItem): string {
  return sample.asset?.file_name || sample.item_key;
}

export function isImageSampleItem(sample: SampleItem): boolean {
  return isImageFileName(getSampleItemName(sample));
}
