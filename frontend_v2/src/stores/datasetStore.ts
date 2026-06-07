import { create } from 'zustand';
import type { AnnotationProject, AnnotationRecord, Dataset, SampleItem } from '../types';
import { getAnnotation, getAnnotationRecords, getAnnotationRecordsBySamples, saveAnnotationRecord } from '../api/annotation';
import { updateAnnotation as updateAnnotationApi } from '../api/annotation';
import { getDataset, getDatasetSamples, previewSample } from '../api/dataset';
import { AnnotationType, DatasetScenarioType, createClassificationAnnotation } from '../types';
import { toYoloFormat } from '../utils/yolo';
import { getRecordClassIds, buildYoloRecordContent, buildClassificationRecordContent } from '../utils/annotationRecordContent';
import { parseAnnotationClasses } from '../utils/annotationClasses';
import { getSampleItemName, isImageSampleItem } from '../utils/sampleItem';
import { useAnnotationStore } from './annotationStore';
import { readSampleCursorCache, writeSampleCursorCache, type SampleCursorCache } from './annotationSampleCursorCache';
import { message } from 'antd';

const DEFAULT_SAMPLE_PAGE_SIZE = 100;

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
  // 当前样本页码（1-based）
  samplePage: number;
  // 当前页大小
  samplePageSize: number;
  // 样本总数
  totalSamples: number;
  // 当前样本是否按页加载
  pagedSamplesEnabled: boolean;
  // 最近访问样本位置缓存
  sampleCursorCache: SampleCursorCache;
  // 当前协作标注 token。普通标注页为空。
  collaboratorToken: string | null;
  // 当前协作文档快照。普通标注页为空。
  collaborationState: string | null;
  // 当前图像 URL
  currentImageUrl: string;
  // 加载状态
  loading: boolean;

  // Actions
  loadAnnotationProject: (annotationId: number) => Promise<SampleRestoreInfo | null>;
  loadSampleAtIndex: (index: number) => Promise<void>;
  loadSamplePage: (page: number, focusIndexInPage?: number) => Promise<void>;
  loadSampleById: (sampleId: number) => Promise<boolean>;
  loadSampleByName: (sampleName: string) => Promise<void>;
  nextSample: () => Promise<void>;
  prevSample: () => Promise<void>;
  rememberCurrentSample: () => void;
  saveCurrentAnnotation: () => Promise<void>;
}

export interface SampleRestoreInfo {
  annotationId: number;
  sampleId: number;
  sampleName: string;
}

export const useDatasetStore = create<DatasetStoreState>((set, get) => ({
  annotationProject: null,
  dataset: null,
  sampleItems: [],
  annotationRecords: [],
  currentSampleIndex: -1,
  samplePage: 1,
  samplePageSize: DEFAULT_SAMPLE_PAGE_SIZE,
  totalSamples: 0,
  pagedSamplesEnabled: true,
  sampleCursorCache: readSampleCursorCache(),
  collaboratorToken: null,
  collaborationState: null,
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
        samplePage: 1,
        samplePageSize: DEFAULT_SAMPLE_PAGE_SIZE,
        totalSamples: 0,
        pagedSamplesEnabled: true,
        collaboratorToken: null,
        collaborationState: null,
        currentImageUrl: '',
      });

      // 2. 设置 classes
      const annotationStore = useAnnotationStore.getState();
      annotationStore.setClasses(parseAnnotationClasses(project.classes));

      // 3. 获取数据集样本和标注记录
      if (project.dataset_id) {
        const dataset = await getDataset(project.dataset_id);
        const isAerialScenario = dataset.scenario_type === DatasetScenarioType.AerialStitch;
        set({
          dataset,
          pagedSamplesEnabled: !isAerialScenario,
          totalSamples: dataset.count || 0,
        });

        if (isAerialScenario) {
          const [sampleResult, recordResult] = await Promise.all([
            getDatasetSamples(project.dataset_id),
            getAnnotationRecords(annotationId, 1, DEFAULT_SAMPLE_PAGE_SIZE),
          ]);
          const samples = (sampleResult.items || []).filter(isImageSampleItem);
          set({
            sampleItems: samples,
            annotationRecords: recordResult.items || [],
            samplePage: 1,
            samplePageSize: sampleResult.page_size || DEFAULT_SAMPLE_PAGE_SIZE,
            totalSamples: sampleResult.total || samples.length,
          });

          if (samples.length > 0) {
            await get().loadSampleAtIndex(0);
          }
          return null;
        } else {
          const cached = get().sampleCursorCache[annotationId];
          if (cached?.sampleId) {
            const restored = await get().loadSampleById(cached.sampleId);
            if (restored) {
              return {
                annotationId,
                sampleId: cached.sampleId,
                sampleName: cached.sampleName,
              };
            }
          } else {
            await get().loadSamplePage(1, 0);
          }
          return null;
        }
      } else {
        set({
          dataset: null,
          sampleItems: [],
          annotationRecords: [],
          currentSampleIndex: -1,
          samplePage: 1,
          samplePageSize: DEFAULT_SAMPLE_PAGE_SIZE,
          totalSamples: 0,
          pagedSamplesEnabled: true,
          currentImageUrl: '',
        });
      }
      return null;
    } catch (err) {
      console.error('Failed to load annotation project:', err);
      message.error('加载标注项目失败');
      return null;
    } finally {
      set({ loading: false });
    }
  },

  loadSamplePage: async (page: number, focusIndexInPage = 0) => {
    const { annotationProject, dataset, samplePageSize, pagedSamplesEnabled } = get();
    if (!annotationProject?.dataset_id || !annotationProject.id || !dataset || !pagedSamplesEnabled) return;

    const annotationStore = useAnnotationStore.getState();
    if (annotationStore.modified) {
      await get().saveCurrentAnnotation();
    }

    const nextPage = Math.max(1, page);
    set({ loading: true });

    try {
      const sampleResult = await getDatasetSamples(annotationProject.dataset_id, nextPage, samplePageSize);
      const samples = (sampleResult.items || []).filter(isImageSampleItem);
      const sampleIds = samples.map((sample) => sample.id);
      const pageRecords = sampleIds.length > 0
        ? await getAnnotationRecordsBySamples(annotationProject.id, sampleIds)
        : [];
      const nextIndex = samples.length > 0
        ? Math.min(Math.max(focusIndexInPage, 0), samples.length - 1)
        : -1;

      set({
        sampleItems: samples,
        annotationRecords: pageRecords,
        samplePage: sampleResult.page || nextPage,
        samplePageSize: sampleResult.page_size || samplePageSize,
        totalSamples: sampleResult.total || 0,
        currentSampleIndex: nextIndex,
        currentImageUrl: '',
      });

      if (nextIndex >= 0) {
        await get().loadSampleAtIndex(nextIndex);
      } else {
        useAnnotationStore.getState().setAnnotations([]);
        set({ loading: false });
      }
    } catch (err) {
      console.error('Failed to load sample page:', err);
      message.error('加载样本分页失败');
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
      const annotationProjectId = annotationProject.id;
      const sampleName = getSampleItemName(sample);

      set((state) => ({
        sampleCursorCache: {
          ...state.sampleCursorCache,
          [annotationProjectId]: {
            sampleId: sample.id,
            sampleName,
            updatedAt: Date.now(),
          },
        },
      }));
      writeSampleCursorCache({
        ...get().sampleCursorCache,
        [annotationProjectId]: {
          sampleId: sample.id,
          sampleName,
          updatedAt: Date.now(),
        },
      });

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
    const { sampleItems, annotationProject, dataset, pagedSamplesEnabled, totalSamples, samplePageSize } = get();
    const index = sampleItems.findIndex((sample) => getSampleItemName(sample) === sampleName);
    if (index >= 0) {
      await get().loadSampleAtIndex(index);
      return;
    }

    if (!pagedSamplesEnabled || !annotationProject?.dataset_id || !dataset) {
      return;
    }

    const totalPages = Math.max(1, Math.ceil(totalSamples / samplePageSize));
    for (let page = 1; page <= totalPages; page += 1) {
      try {
        const sampleResult = await getDatasetSamples(annotationProject.dataset_id, page, samplePageSize);
        const samples = (sampleResult.items || []).filter(isImageSampleItem);
        const pageIndex = samples.findIndex((sample) => getSampleItemName(sample) === sampleName);
        if (pageIndex >= 0) {
          const sampleIds = samples.map((sample) => sample.id);
          const pageRecords = sampleIds.length > 0
            ? await getAnnotationRecordsBySamples(annotationProject.id, sampleIds)
            : [];
          set({
            sampleItems: samples,
            annotationRecords: pageRecords,
            samplePage: sampleResult.page || page,
            samplePageSize: sampleResult.page_size || samplePageSize,
            totalSamples: sampleResult.total || 0,
            currentSampleIndex: pageIndex,
            currentImageUrl: '',
          });
          await get().loadSampleAtIndex(pageIndex);
          return;
        }
      } catch (err) {
        console.error('Failed to locate sample by name:', err);
        break;
      }
    }
  },

  loadSampleById: async (sampleId: number) => {
    const { sampleItems, annotationProject, dataset, pagedSamplesEnabled, totalSamples, samplePageSize } = get();
    const index = sampleItems.findIndex((sample) => sample.id === sampleId);
    if (index >= 0) {
      await get().loadSampleAtIndex(index);
      return true;
    }

    if (!pagedSamplesEnabled || !annotationProject?.dataset_id || !dataset) {
      return false;
    }

    const totalPages = Math.max(1, Math.ceil(totalSamples / samplePageSize));
    for (let page = 1; page <= totalPages; page += 1) {
      try {
        const sampleResult = await getDatasetSamples(annotationProject.dataset_id, page, samplePageSize);
        const samples = (sampleResult.items || []).filter(isImageSampleItem);
        const pageIndex = samples.findIndex((sample) => sample.id === sampleId);
        if (pageIndex >= 0) {
          const sampleIds = samples.map((sample) => sample.id);
          const pageRecords = sampleIds.length > 0
            ? await getAnnotationRecordsBySamples(annotationProject.id, sampleIds)
            : [];
          set({
            sampleItems: samples,
            annotationRecords: pageRecords,
            samplePage: sampleResult.page || page,
            samplePageSize: sampleResult.page_size || samplePageSize,
            totalSamples: sampleResult.total || 0,
            currentSampleIndex: pageIndex,
            currentImageUrl: '',
          });
          await get().loadSampleAtIndex(pageIndex);
          return true;
        }
      } catch (err) {
        console.error('Failed to locate sample by id:', err);
        break;
      }
    }
    return false;
  },

  nextSample: async () => {
    const { currentSampleIndex, sampleItems, annotationProject, pagedSamplesEnabled, samplePage, samplePageSize, totalSamples } = get();
    const annotationStore = useAnnotationStore.getState();

    // 自动保存
    if (annotationStore.modified && annotationProject) {
      await get().saveCurrentAnnotation();
    }

    if (currentSampleIndex < sampleItems.length - 1) {
      await get().loadSampleAtIndex(currentSampleIndex + 1);
      return;
    }

    if (pagedSamplesEnabled && samplePage * samplePageSize < totalSamples) {
      await get().loadSamplePage(samplePage + 1, 0);
    }
  },

  prevSample: async () => {
    const { currentSampleIndex, annotationProject, pagedSamplesEnabled, samplePage, samplePageSize } = get();
    const annotationStore = useAnnotationStore.getState();

    // 自动保存
    if (annotationStore.modified && annotationProject) {
      await get().saveCurrentAnnotation();
    }

    if (currentSampleIndex > 0) {
      await get().loadSampleAtIndex(currentSampleIndex - 1);
      return;
    }

    if (pagedSamplesEnabled && samplePage > 1) {
      await get().loadSamplePage(samplePage - 1, samplePageSize - 1);
    }
  },

  rememberCurrentSample: () => {
    const { annotationProject, sampleItems, currentSampleIndex } = get();
    if (!annotationProject?.id || currentSampleIndex < 0 || currentSampleIndex >= sampleItems.length) return;
    const sample = sampleItems[currentSampleIndex];
    set((state) => ({
      sampleCursorCache: {
        ...state.sampleCursorCache,
        [annotationProject.id]: {
          sampleId: sample.id,
          sampleName: getSampleItemName(sample),
          updatedAt: Date.now(),
        },
      },
    }));
    writeSampleCursorCache({
      ...get().sampleCursorCache,
      [annotationProject.id]: {
        sampleId: sample.id,
        sampleName: getSampleItemName(sample),
        updatedAt: Date.now(),
      },
    });
  },

  saveCurrentAnnotation: async () => {
    const {
      annotationProject,
      collaborationState,
      collaboratorToken,
      sampleItems,
      currentSampleIndex,
    } = get();
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
        collaborator_token: collaboratorToken || undefined,
        collab_state: collaborationState || undefined,
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
