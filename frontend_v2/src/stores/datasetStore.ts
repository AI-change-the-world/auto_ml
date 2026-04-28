import { create } from 'zustand';
import type { AnnotationProject, AnnotationRecord, Dataset, SampleItem } from '../types';
import { getAnnotation, getAnnotationRecords, saveAnnotationRecord } from '../api/annotation';
import { updateAnnotation as updateAnnotationApi } from '../api/annotation';
import { getDataset, getDatasetSamples, previewSample } from '../api/dataset';
import { AnnotationType, createClassificationAnnotation } from '../types';
import { toYoloFormat } from '../utils/yolo';
import { getRecordClassIds, buildYoloRecordContent, buildClassificationRecordContent } from '../utils/annotationRecordContent';
import { parseAnnotationClasses } from '../utils/annotationClasses';
import { getSampleItemName, isImageSampleItem } from '../utils/sampleItem';
import { useAnnotationStore } from './annotationStore';
import { message } from 'antd';

interface DatasetStoreState {
  // 当前标注项目
  annotationProject: AnnotationProject | null;
  // 当前关联数据集
  dataset: Dataset | null;
  // 当前图像样本列表
  sampleItems: SampleItem[];
  // 当前标注记录列表
  annotationRecords: AnnotationRecord[];
  // 当前样本索引
  currentSampleIndex: number;
  // 当前图像 URL
  currentImageUrl: string;
  // 加载状态
  loading: boolean;

  // Actions
  loadAnnotationProject: (annotationId: number) => Promise<void>;
  loadSampleAtIndex: (index: number) => Promise<void>;
  loadSampleByName: (sampleName: string) => Promise<void>;
  nextSample: () => Promise<void>;
  prevSample: () => Promise<void>;
  saveCurrentAnnotation: () => Promise<void>;
}

export const useDatasetStore = create<DatasetStoreState>((set, get) => ({
  annotationProject: null,
  dataset: null,
  sampleItems: [],
  annotationRecords: [],
  currentSampleIndex: -1,
  currentImageUrl: '',
  loading: false,

  loadAnnotationProject: async (annotationId: number) => {
    set({ loading: true });
    try {
      // 1. 获取标注项目
      const project = await getAnnotation(annotationId);
      set({
        annotationProject: project,
        dataset: null,
        sampleItems: [],
        annotationRecords: [],
        currentSampleIndex: -1,
        currentImageUrl: '',
      });

      // 2. 设置 classes
      const annotationStore = useAnnotationStore.getState();
      annotationStore.setClasses(parseAnnotationClasses(project.classes));

      // 3. 获取数据集样本和标注记录
      if (project.dataset_id) {
        const [dataset, sampleResult, recordResult] = await Promise.all([
          getDataset(project.dataset_id),
          getDatasetSamples(project.dataset_id),
          getAnnotationRecords(annotationId, 1, 500),
        ]);
        const samples = (sampleResult.items || []).filter(isImageSampleItem);
        set({ dataset, sampleItems: samples, annotationRecords: recordResult.items || [] });

        // 4. 加载第一个样本
        if (samples.length > 0) {
          await get().loadSampleAtIndex(0);
        }
      } else {
        set({
          dataset: null,
          sampleItems: [],
          annotationRecords: [],
          currentSampleIndex: -1,
          currentImageUrl: '',
        });
      }
    } catch (err) {
      console.error('Failed to load annotation project:', err);
      message.error('加载标注项目失败');
    } finally {
      set({ loading: false });
    }
  },

  loadSampleAtIndex: async (index: number) => {
    const { sampleItems, annotationRecords, annotationProject } = get();
    if (index < 0 || index >= sampleItems.length || !annotationProject?.dataset_id) return;

    set({ loading: true, currentSampleIndex: index });
    const annotationStore = useAnnotationStore.getState();

    try {
      const sample = sampleItems[index];

      // 获取图像预览 URL
      const preview = await previewSample(annotationProject.dataset_id, sample.id);
      set({ currentImageUrl: preview.presigned_url });

      const annotationRecord = annotationRecords.find((record) => record.sample_item_id === sample.id);

      if (annotationRecord?.content) {
        if (annotationProject.annotation_type === AnnotationType.Classification) {
          const classIds = getRecordClassIds(annotationRecord.content);
          annotationStore.setAnnotations(classIds.length > 0 ? [createClassificationAnnotation(classIds[0])] : []);
        } else {
          // 需要等待图像加载完成才能获取尺寸，先设置空标注
          // 实际解析在 ImageCanvas 图像加载后进行
          annotationStore.setAnnotations([]);
        }
        set({ loading: false });
      } else {
        annotationStore.setAnnotations([]);
        set({ loading: false });
      }
    } catch (err) {
      console.error('Failed to load file:', err);
      set({ loading: false });
    }
  },

  loadSampleByName: async (sampleName: string) => {
    const { sampleItems } = get();
    const index = sampleItems.findIndex((sample) => getSampleItemName(sample) === sampleName);
    if (index >= 0) {
      await get().loadSampleAtIndex(index);
    }
  },

  nextSample: async () => {
    const { currentSampleIndex, sampleItems, annotationProject } = get();
    const annotationStore = useAnnotationStore.getState();

    // 自动保存
    if (annotationStore.modified && annotationProject) {
      await get().saveCurrentAnnotation();
    }

    if (currentSampleIndex < sampleItems.length - 1) {
      await get().loadSampleAtIndex(currentSampleIndex + 1);
    }
  },

  prevSample: async () => {
    const { currentSampleIndex, annotationProject } = get();
    const annotationStore = useAnnotationStore.getState();

    // 自动保存
    if (annotationStore.modified && annotationProject) {
      await get().saveCurrentAnnotation();
    }

    if (currentSampleIndex > 0) {
      await get().loadSampleAtIndex(currentSampleIndex - 1);
    }
  },

  saveCurrentAnnotation: async () => {
    const { annotationProject, sampleItems, currentSampleIndex } = get();
    if (!annotationProject || currentSampleIndex < 0) return;

    const annotationStore = useAnnotationStore.getState();
    const sample = sampleItems[currentSampleIndex];
    const recordContent = annotationProject.annotation_type === AnnotationType.Classification
      ? buildClassificationRecordContent(
        annotationStore.annotations[0]?.classId !== undefined && annotationStore.annotations[0]?.classId >= 0
          ? [annotationStore.annotations[0].classId]
          : [],
      )
      : buildYoloRecordContent(
        toYoloFormat(
          annotationStore.annotations,
          annotationStore.imageWidth,
          annotationStore.imageHeight,
        ),
        annotationStore.imageWidth,
        annotationStore.imageHeight,
      );

    try {
      const record = await saveAnnotationRecord(annotationProject.id, {
        sample_item_id: sample.id,
        content: recordContent,
        status: 'saved',
      });
      set((state) => ({
        annotationRecords: [
          record,
          ...state.annotationRecords.filter((item) => item.sample_item_id !== sample.id),
        ],
      }));

      // 同步 classes 到数据库
      const classesJson = JSON.stringify(annotationStore.classes);
      if (classesJson !== (annotationProject.classes ?? '[]')) {
        try {
          await updateAnnotationApi(annotationProject.id, { classes: classesJson });
          set((state) => ({
            annotationProject: state.annotationProject
              ? { ...state.annotationProject, classes: classesJson }
              : null,
          }));
        } catch (err) {
          console.error('Failed to sync classes:', err);
        }
      }

      annotationStore.setModified(false);
      message.success('保存成功');
    } catch (err) {
      console.error('Failed to save annotation:', err);
      message.error('保存失败');
    }
  },
}));
