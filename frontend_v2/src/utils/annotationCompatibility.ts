import type { Dataset } from '../types';
import {
  AnnotationType,
  DatasetScenarioType,
  isAnyDpoDataset,
  isDpoBestOfNDataset,
  isDpoMultiTurnDataset,
  isDpoPairwiseDataset,
  isDpoReferenceChoiceDataset,
  isLlmConversationDataset,
  isMllmConversationDataset,
} from '../types';

export interface AnnotationCategoryDefinition {
  key: 'image' | 'conversation' | 'preference';
  label: string;
  description: string;
  annotationTypes: number[];
}

export interface AnnotationTypePreset {
  value: number;
  label: string;
  description: string;
  categoryKey: AnnotationCategoryDefinition['key'];
  datasetHint: string;
}

export const AnnotationCategoryDefinitions: AnnotationCategoryDefinition[] = [
  {
    key: 'image',
    label: '图像标注',
    description: '面向图像检测、分类、分割等视觉任务。',
    annotationTypes: [
      AnnotationType.Detection,
      AnnotationType.Classification,
      AnnotationType.Segmentation,
      AnnotationType.Pose,
    ],
  },
  {
    key: 'conversation',
    label: '对话标注',
    description: '面向文本对话或图文对话的结构化标注。',
    annotationTypes: [
      AnnotationType.LLM,
      AnnotationType.MLLM,
    ],
  },
  {
    key: 'preference',
    label: '偏好标注',
    description: '面向候选回复优劣判断的偏好数据生产。',
    annotationTypes: [
      AnnotationType.DpoPairwise,
      AnnotationType.DpoBestOfN,
      AnnotationType.DpoReferenceChoice,
      AnnotationType.DpoMultiTurn,
    ],
  },
];

export const AnnotationTypePresets: AnnotationTypePreset[] = [
  {
    value: AnnotationType.Detection,
    label: '目标检测',
    description: '通过框选目标位置完成检测类标注。',
    categoryKey: 'image',
    datasetHint: '仅可绑定普通图像或航拍拼接图像数据集。',
  },
  {
    value: AnnotationType.Classification,
    label: '图像分类',
    description: '为整张图像打类别标签。',
    categoryKey: 'image',
    datasetHint: '仅可绑定普通图像或航拍拼接图像数据集。',
  },
  {
    value: AnnotationType.Segmentation,
    label: '图像分割',
    description: '通过多边形区域完成像素级标注。',
    categoryKey: 'image',
    datasetHint: '仅可绑定普通图像或航拍拼接图像数据集。',
  },
  {
    value: AnnotationType.Pose,
    label: '姿态标注',
    description: '关键点姿态标注能力，当前仍为占位。',
    categoryKey: 'image',
    datasetHint: '仅可绑定普通图像或航拍拼接图像数据集。',
  },
  {
    value: AnnotationType.LLM,
    label: 'LLM 对话',
    description: '面向纯文本对话数据的消息标注。',
    categoryKey: 'conversation',
    datasetHint: '仅可绑定 LLM 对话数据集。',
  },
  {
    value: AnnotationType.MLLM,
    label: 'MLLM 对话',
    description: '面向图文混合场景的多模态对话标注。',
    categoryKey: 'conversation',
    datasetHint: '仅可绑定 MLLM 图文对话数据集。',
  },
  {
    value: AnnotationType.DpoPairwise,
    label: 'DPO 二选一',
    description: '在两条候选回复之间直接做 A/B 偏好判断。',
    categoryKey: 'preference',
    datasetHint: '仅可绑定 DPO 二选一数据集。',
  },
  {
    value: AnnotationType.DpoBestOfN,
    label: 'DPO 多选一',
    description: '在多条候选回复中选出最佳回复。',
    categoryKey: 'preference',
    datasetHint: '仅可绑定 DPO 多选一数据集。',
  },
  {
    value: AnnotationType.DpoReferenceChoice,
    label: 'DPO 参考增强',
    description: '结合参考答案或规则说明判断最佳回复。',
    categoryKey: 'preference',
    datasetHint: '仅可绑定 DPO 参考增强数据集。',
  },
  {
    value: AnnotationType.DpoMultiTurn,
    label: 'DPO 多轮对话',
    description: '基于完整对话上下文判断最终回复优劣。',
    categoryKey: 'preference',
    datasetHint: '仅可绑定 DPO 多轮对话数据集。',
  },
];

export function getAnnotationCategoryDefinition(key: AnnotationCategoryDefinition['key']) {
  return AnnotationCategoryDefinitions.find((item) => item.key === key);
}

export function getAnnotationTypePreset(annotationType: number) {
  return AnnotationTypePresets.find((item) => item.value === annotationType);
}

export function isImageAnnotationType(annotationType: number) {
  const imageAnnotationTypes: number[] = [
    AnnotationType.Detection,
    AnnotationType.Classification,
    AnnotationType.Segmentation,
    AnnotationType.Pose,
  ];

  return imageAnnotationTypes.includes(annotationType);
}

export function isDatasetCompatibleWithAnnotationType(dataset: Dataset, annotationType: number) {
  if (annotationType === AnnotationType.LLM) {
    return isLlmConversationDataset(dataset.data_type, dataset.scenario_type);
  }

  if (annotationType === AnnotationType.MLLM) {
    return isMllmConversationDataset(dataset.data_type, dataset.scenario_type);
  }

  if (annotationType === AnnotationType.DPO) {
    return isAnyDpoDataset(dataset.data_type, dataset.scenario_type);
  }

  if (annotationType === AnnotationType.DpoPairwise) {
    return isDpoPairwiseDataset(dataset.data_type, dataset.scenario_type);
  }

  if (annotationType === AnnotationType.DpoBestOfN) {
    return isDpoBestOfNDataset(dataset.data_type, dataset.scenario_type);
  }

  if (annotationType === AnnotationType.DpoReferenceChoice) {
    return isDpoReferenceChoiceDataset(dataset.data_type, dataset.scenario_type);
  }

  if (annotationType === AnnotationType.DpoMultiTurn) {
    return isDpoMultiTurnDataset(dataset.data_type, dataset.scenario_type);
  }

  if (isImageAnnotationType(annotationType)) {
    const imageDatasetScenarios: number[] = [
      DatasetScenarioType.Normal,
      DatasetScenarioType.AerialStitch,
    ];

    return dataset.data_type === 0 && imageDatasetScenarios.includes(dataset.scenario_type);
  }

  return false;
}

export function getAllowedAnnotationTypesForDataset(dataset?: Dataset): number[] {
  if (!dataset) {
    return AnnotationTypePresets.map((item) => item.value);
  }

  const allowed = AnnotationTypePresets
    .map((item) => item.value)
    .filter((annotationType) => isDatasetCompatibleWithAnnotationType(dataset, annotationType));

  return allowed.filter((annotationType) => annotationType !== AnnotationType.DPO);
}

export function getCompatibleDatasetsForAnnotationType(datasets: Dataset[], annotationType?: number) {
  if (annotationType === undefined) {
    return datasets;
  }

  return datasets.filter((dataset) => isDatasetCompatibleWithAnnotationType(dataset, annotationType));
}
