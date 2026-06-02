import { create } from 'zustand';
import { message } from 'antd';
import {
  claimAnnotationCollaborationSamples,
  createAnnotationCollaborationSession,
  getAnnotationCollaborationSamples,
  getAnnotationCollaborationStats,
  getAnnotation,
} from '../api/annotation';
import { getDataset } from '../api/dataset';
import {
  AnnotationType,
  type AnnotationCollaborator,
  type AnnotationCollaborationStats,
  type AnnotationSampleAssignment,
} from '../types';
import { parseAnnotationClasses } from '../utils/annotationClasses';
import { useAnnotationStore } from './annotationStore';
import { useDatasetStore } from './datasetStore';

const COLLABORATION_PAGE_SIZE = 100;
const DEFAULT_CLAIM_BATCH_SIZE = 20;
const TOKEN_STORAGE_PREFIX = 'auto_ml.annotation.collaborator_token';

function getTokenStorageKey(annotationId: number) {
  return `${TOKEN_STORAGE_PREFIX}.${annotationId}`;
}

function readStoredToken(annotationId: number): string | undefined {
  if (typeof window === 'undefined') return undefined;
  return window.localStorage.getItem(getTokenStorageKey(annotationId)) || undefined;
}

function writeStoredToken(annotationId: number, token: string) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(getTokenStorageKey(annotationId), token);
}

interface AnnotationCollaborationState {
  collaborator: AnnotationCollaborator | null;
  assignments: AnnotationSampleAssignment[];
  stats: AnnotationCollaborationStats | null;
  loading: boolean;
  initializedAnnotationId: number | null;

  initialize: (annotationId: number) => Promise<void>;
  claimMore: (batchSize?: number) => Promise<void>;
  loadAssignedPage: (page: number, focusIndexInPage?: number) => Promise<void>;
  refreshStats: () => Promise<void>;
  reset: () => void;
}

export const useAnnotationCollaborationStore = create<AnnotationCollaborationState>((set, get) => ({
  collaborator: null,
  assignments: [],
  stats: null,
  loading: false,
  initializedAnnotationId: null,

  initialize: async (annotationId: number) => {
    set({ loading: true });
    try {
      const project = await getAnnotation(annotationId);
      if (project.annotation_type !== AnnotationType.Detection) {
        message.error('协作标注 MVP 仅支持目标检测项目');
        return;
      }
      if (!project.dataset_id) {
        message.error('当前标注项目未绑定数据集');
        return;
      }

      const dataset = await getDataset(project.dataset_id);
      const session = await createAnnotationCollaborationSession(annotationId, readStoredToken(annotationId));
      const collaborator = session.collaborator;
      writeStoredToken(annotationId, collaborator.token);

      useAnnotationStore.getState().setClasses(parseAnnotationClasses(project.classes));
      useDatasetStore.setState({
        annotationProject: project,
        dataset,
        sampleItems: [],
        annotationRecords: [],
        currentSampleIndex: -1,
        samplePage: 1,
        samplePageSize: COLLABORATION_PAGE_SIZE,
        totalSamples: 0,
        pagedSamplesEnabled: false,
        collaboratorToken: collaborator.token,
        collaborationState: null,
        currentImageUrl: '',
        loading: false,
      });
      set({ collaborator, initializedAnnotationId: annotationId, assignments: [] });

      await get().loadAssignedPage(1, 0);
      const currentTotal = useDatasetStore.getState().totalSamples;
      if (currentTotal === 0) {
        await get().claimMore(DEFAULT_CLAIM_BATCH_SIZE);
      } else {
        await get().refreshStats();
      }
    } catch (error) {
      console.error('Failed to initialize collaborative annotation:', error);
      message.error('初始化协作标注失败');
    } finally {
      set({ loading: false });
    }
  },

  claimMore: async (batchSize = DEFAULT_CLAIM_BATCH_SIZE) => {
    const { collaborator, initializedAnnotationId } = get();
    if (!collaborator || !initializedAnnotationId) return;

    set({ loading: true });
    try {
      const result = await claimAnnotationCollaborationSamples(
        initializedAnnotationId,
        collaborator.token,
        batchSize,
      );
      if ((result?.assigned_count || 0) > 0) {
        message.success(`已领取 ${result.assigned_count} 张图片`);
      } else {
        message.info('暂无可领取图片');
      }
      await get().loadAssignedPage(1, 0);
      await get().refreshStats();
    } catch (error) {
      console.error('Failed to claim collaborative samples:', error);
      message.error('领取协作样本失败');
    } finally {
      set({ loading: false });
    }
  },

  loadAssignedPage: async (page: number, focusIndexInPage = 0) => {
    const { collaborator, initializedAnnotationId } = get();
    if (!collaborator || !initializedAnnotationId) return;

    const datasetStore = useDatasetStore.getState();
    if (useAnnotationStore.getState().modified) {
      await datasetStore.saveCurrentAnnotation();
    }

    useDatasetStore.setState({ loading: true });
    try {
      const result = await getAnnotationCollaborationSamples(
        initializedAnnotationId,
        collaborator.token,
        page,
        COLLABORATION_PAGE_SIZE,
      );
      const nextIndex = result.samples.length > 0
        ? Math.min(Math.max(focusIndexInPage, 0), result.samples.length - 1)
        : -1;

      useDatasetStore.setState({
        sampleItems: result.samples,
        annotationRecords: result.records,
        samplePage: result.page,
        samplePageSize: result.page_size,
        totalSamples: result.total,
        currentSampleIndex: nextIndex,
        currentImageUrl: '',
        loading: false,
      });
      set({ assignments: result.assignments });

      if (nextIndex >= 0) {
        await useDatasetStore.getState().loadSampleAtIndex(nextIndex);
      } else {
        useAnnotationStore.getState().setAnnotations([]);
      }
    } catch (error) {
      console.error('Failed to load collaborative samples:', error);
      message.error('加载协作样本失败');
      useDatasetStore.setState({ loading: false });
    }
  },

  refreshStats: async () => {
    const { collaborator, initializedAnnotationId } = get();
    if (!collaborator || !initializedAnnotationId) return;

    try {
      const stats = await getAnnotationCollaborationStats(initializedAnnotationId, collaborator.token);
      set({ stats });
    } catch (error) {
      console.error('Failed to load collaborative stats:', error);
    }
  },

  reset: () => {
    set({
      collaborator: null,
      assignments: [],
      stats: null,
      loading: false,
      initializedAnnotationId: null,
    });
    useDatasetStore.setState({ collaboratorToken: null, collaborationState: null });
  },
}));
