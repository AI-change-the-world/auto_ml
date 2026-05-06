import type { Dataset } from '../types';
import {
  DatasetScenarioType,
  isDpoPreferenceDataset,
  isLlmConversationDataset,
  isMllmConversationDataset,
} from '../types';
import { getFileExtension } from './file';

const ARCHIVE_EXTENSIONS = ['zip', 'tar', 'gz', 'tgz', 'bz2', 'xz', 'tbz2', 'txz'];
const IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'svg', 'ico'];
const TEXT_EXTENSIONS = ['txt', 'md', 'json', 'jsonl', 'csv', 'tsv', 'xml', 'yaml', 'yml', 'log'];
const VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv', 'webm', 'wmv', 'flv'];
const AUDIO_EXTENSIONS = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma'];

export interface DatasetUploadRule {
  accept: string;
  extensions: string[];
  description: string;
}

function withDot(extensions: string[]) {
  return extensions.map((extension) => `.${extension}`);
}

export function getDatasetUploadRule(dataset: Dataset): DatasetUploadRule {
  if (isDpoPreferenceDataset(dataset.data_type, dataset.scenario_type)) {
    return {
      accept: '.jsonl',
      extensions: ['jsonl'],
      description: '.jsonl',
    };
  }

  if (isLlmConversationDataset(dataset.data_type, dataset.scenario_type)) {
    return {
      accept: withDot(TEXT_EXTENSIONS).join(','),
      extensions: TEXT_EXTENSIONS,
      description: withDot(TEXT_EXTENSIONS).join(', '),
    };
  }

  if (isMllmConversationDataset(dataset.data_type, dataset.scenario_type)) {
    return {
      accept: withDot(IMAGE_EXTENSIONS).join(','),
      extensions: IMAGE_EXTENSIONS,
      description: withDot(IMAGE_EXTENSIONS).join(', '),
    };
  }

  if (dataset.scenario_type === DatasetScenarioType.AerialStitch || dataset.data_type === 0) {
    const extensions = [...IMAGE_EXTENSIONS, ...ARCHIVE_EXTENSIONS];
    return {
      accept: withDot(extensions).join(','),
      extensions,
      description: withDot(extensions).join(', '),
    };
  }

  if (dataset.data_type === 1) {
    return {
      accept: withDot(TEXT_EXTENSIONS).join(','),
      extensions: TEXT_EXTENSIONS,
      description: withDot(TEXT_EXTENSIONS).join(', '),
    };
  }

  if (dataset.data_type === 2) {
    return {
      accept: withDot(VIDEO_EXTENSIONS).join(','),
      extensions: VIDEO_EXTENSIONS,
      description: withDot(VIDEO_EXTENSIONS).join(', '),
    };
  }

  if (dataset.data_type === 3) {
    return {
      accept: withDot(AUDIO_EXTENSIONS).join(','),
      extensions: AUDIO_EXTENSIONS,
      description: withDot(AUDIO_EXTENSIONS).join(', '),
    };
  }

  return {
    accept: '',
    extensions: [],
    description: '',
  };
}

export function splitAcceptedFiles(dataset: Dataset, files: File[]) {
  const rule = getDatasetUploadRule(dataset);
  if (rule.extensions.length === 0) {
    return {
      accepted: files,
      rejected: [] as File[],
      rule,
    };
  }

  const extensionSet = new Set(rule.extensions);
  const accepted: File[] = [];
  const rejected: File[] = [];
  files.forEach((file) => {
    const extension = getFileExtension(file.name);
    if (extensionSet.has(extension)) {
      accepted.push(file);
    } else {
      rejected.push(file);
    }
  });
  return { accepted, rejected, rule };
}
