import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import { LabelMode, AnnotationShape } from '../types';
import type { Annotation } from '../types';

interface AnnotationStoreState {
  // 标注数据
  annotations: Annotation[];
  selectedUuid: string;
  mode: LabelMode;
  modified: boolean;
  classes: string[];

  // 默认类别 ID（下次创建标注时使用）
  defaultClassId: number;

  // 当前标注形状工具
  annotationShape: AnnotationShape;

  // 图像尺寸
  imageWidth: number;
  imageHeight: number;

  // Undo / Redo 历史栈
  _history: Annotation[][];
  _future: Annotation[][];
  /** 是否处于拖拽/缩放/旋转等连续操作中，连续操作期间 updateAnnotation 不入栈 */
  _batch: boolean;

  // Actions
  setAnnotations: (annotations: Annotation[]) => void;
  addAnnotation: (annotation: Annotation) => void;
  deleteAnnotation: (uuid: string) => void;
  updateAnnotation: (uuid: string, updates: Partial<Annotation>) => void;
  selectAnnotation: (uuid: string) => void;
  clearSelection: () => void;
  toggleVisibility: (uuid: string) => void;
  toggleSelectedVisibility: () => void;
  deleteSelected: () => void;
  changeMode: (mode: LabelMode) => void;
  toggleMode: () => void;
  setModified: (modified: boolean) => void;
  setClasses: (classes: string[]) => void;
  addOrGetClassId: (className: string) => number;
  removeClassByIndex: (index: number) => void;
  setDefaultClassId: (classId: number) => void;
  setSelectedClassId: (classId: number) => void;
  setImageSize: (width: number, height: number) => void;
  setAnnotationShape: (shape: AnnotationShape) => void;
  /** 开始一次连续操作（拖拽/缩放/旋转），先保存快照 */
  beginBatch: () => void;
  /** 结束连续操作 */
  endBatch: () => void;
  undo: () => void;
  redo: () => void;
  reset: () => void;
}

const MAX_HISTORY = 50;

/** 保存当前 annotations 快照到历史栈，并清空 future */
function pushHistory(state: AnnotationStoreState) {
  const history = [...state._history, state.annotations.map((a) => ({ ...a }))];
  if (history.length > MAX_HISTORY) history.shift();
  return { _history: history, _future: [] as Annotation[][] };
}

export const useAnnotationStore = create<AnnotationStoreState>((set, get) => ({
  annotations: [],
  selectedUuid: '',
  mode: LabelMode.Edit,
  modified: false,
  classes: [],
  defaultClassId: 0,
  annotationShape: AnnotationShape.BBox,
  imageWidth: 0,
  imageHeight: 0,
  _history: [],
  _future: [],
  _batch: false,

  setAnnotations: (annotations) => set({ annotations, selectedUuid: '', modified: false, _history: [], _future: [] }),

  addAnnotation: (annotation) => {
    const newAnnotation = { ...annotation, uuid: annotation.uuid || uuidv4() };
    set((state) => ({
      ...pushHistory(state),
      annotations: [...state.annotations, newAnnotation],
      selectedUuid: newAnnotation.uuid,
      modified: true,
    }));
  },

  deleteAnnotation: (uuid) =>
    set((state) => ({
      ...pushHistory(state),
      annotations: state.annotations.filter((a) => a.uuid !== uuid),
      selectedUuid: state.selectedUuid === uuid ? '' : state.selectedUuid,
      modified: true,
    })),

  updateAnnotation: (uuid, updates) =>
    set((state) => ({
      ...(state._batch ? {} : pushHistory(state)),
      annotations: state.annotations.map((a) => (a.uuid === uuid ? { ...a, ...updates } as Annotation : a)),
      modified: true,
    })),

  selectAnnotation: (uuid) =>
    set((state) => ({
      selectedUuid: uuid,
      annotations: state.annotations.map((a) => ({ ...a, selected: a.uuid === uuid }) as Annotation),
    })),

  clearSelection: () =>
    set((state) => ({
      selectedUuid: '',
      annotations: state.annotations.map((a) => ({ ...a, selected: false }) as Annotation),
    })),

  toggleVisibility: (uuid) =>
    set((state) => ({
      annotations: state.annotations.map((a) =>
        a.uuid === uuid ? { ...a, visible: !a.visible } as Annotation : a,
      ),
    })),

  toggleSelectedVisibility: () => {
    const { selectedUuid } = get();
    if (!selectedUuid) return;
    set((state) => ({
      annotations: state.annotations.map((a) =>
        a.uuid === selectedUuid ? { ...a, visible: !a.visible } as Annotation : a,
      ),
    }));
  },

  deleteSelected: () => {
    const { selectedUuid } = get();
    if (!selectedUuid) return;
    set((state) => ({
      ...pushHistory(state),
      annotations: state.annotations.filter((a) => a.uuid !== selectedUuid),
      selectedUuid: '',
      modified: true,
    }));
  },

  changeMode: (mode) => set({ mode }),

  toggleMode: () =>
    set((state) => ({
      mode: state.mode === LabelMode.Edit ? LabelMode.Add : LabelMode.Edit,
    })),

  setModified: (modified) => set({ modified }),

  setClasses: (classes) => set({ classes }),

  addOrGetClassId: (className: string) => {
    const { classes } = get();
    const idx = classes.indexOf(className);
    if (idx >= 0) return idx;
    const newClasses = [...classes, className];
    set({ classes: newClasses, modified: true });
    return newClasses.length - 1;
  },

  removeClassByIndex: (index: number) => {
    const { classes } = get();
    if (index < 0 || index >= classes.length) return;
    set({ classes: classes.filter((_, i) => i !== index) });
  },

  setDefaultClassId: (classId: number) => set({ defaultClassId: classId }),

  setSelectedClassId: (classId: number) =>
    set((state) => {
      const existing = state.annotations[0];
      const nextAnnotation = existing
        ? { ...existing, classId, selected: true } as Annotation
        : {
          uuid: uuidv4(),
          shape: AnnotationShape.Classification,
          classId,
          visible: true,
          selected: true,
        } as Annotation;
      return {
        ...pushHistory(state),
        annotations: [nextAnnotation],
        selectedUuid: nextAnnotation.uuid,
        defaultClassId: classId,
        modified: true,
      };
    }),

  setImageSize: (width, height) => set({ imageWidth: width, imageHeight: height }),

  setAnnotationShape: (shape) => set({ annotationShape: shape }),

  beginBatch: () => {
    set((state) => ({
      ...pushHistory(state),
      _batch: true,
    }));
  },

  endBatch: () => set({ _batch: false }),

  undo: () => {
    const { _history } = get();
    if (_history.length === 0) return;
    const prev = _history[_history.length - 1];
    set((state) => ({
      _history: state._history.slice(0, -1),
      _future: [state.annotations.map((a) => ({ ...a })), ...state._future],
      annotations: prev,
      selectedUuid: '',
      modified: true,
    }));
  },

  redo: () => {
    const { _future } = get();
    if (_future.length === 0) return;
    const next = _future[0];
    set((state) => ({
      _future: state._future.slice(1),
      _history: [...state._history, state.annotations.map((a) => ({ ...a }))],
      annotations: next,
      selectedUuid: '',
      modified: true,
    }));
  },

  reset: () =>
    set({
      annotations: [],
      selectedUuid: '',
      mode: LabelMode.Edit,
      modified: false,
      annotationShape: AnnotationShape.BBox,
      imageWidth: 0,
      imageHeight: 0,
      _history: [],
      _future: [],
      _batch: false,
    }),
}));
