import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import { LabelMode } from '../types';
import type { BBoxAnnotation } from '../types';

interface AnnotationStoreState {
  // 标注数据
  annotations: BBoxAnnotation[];
  selectedUuid: string;
  mode: LabelMode;
  modified: boolean;
  classes: string[];

  // 图像尺寸
  imageWidth: number;
  imageHeight: number;

  // Actions
  setAnnotations: (annotations: BBoxAnnotation[]) => void;
  addAnnotation: (annotation: BBoxAnnotation) => void;
  deleteAnnotation: (uuid: string) => void;
  updateAnnotation: (uuid: string, updates: Partial<BBoxAnnotation>) => void;
  selectAnnotation: (uuid: string) => void;
  clearSelection: () => void;
  toggleVisibility: (uuid: string) => void;
  toggleSelectedVisibility: () => void;
  deleteSelected: () => void;
  changeMode: (mode: LabelMode) => void;
  toggleMode: () => void;
  setModified: (modified: boolean) => void;
  setClasses: (classes: string[]) => void;
  setImageSize: (width: number, height: number) => void;
  reset: () => void;
}

export const useAnnotationStore = create<AnnotationStoreState>((set, get) => ({
  annotations: [],
  selectedUuid: '',
  mode: LabelMode.Edit,
  modified: false,
  classes: [],
  imageWidth: 0,
  imageHeight: 0,

  setAnnotations: (annotations) => set({ annotations, selectedUuid: '', modified: false }),

  addAnnotation: (annotation) => {
    const newAnnotation = { ...annotation, uuid: annotation.uuid || uuidv4() };
    set((state) => ({
      annotations: [...state.annotations, newAnnotation],
      modified: true,
    }));
  },

  deleteAnnotation: (uuid) =>
    set((state) => ({
      annotations: state.annotations.filter((a) => a.uuid !== uuid),
      selectedUuid: state.selectedUuid === uuid ? '' : state.selectedUuid,
      modified: true,
    })),

  updateAnnotation: (uuid, updates) =>
    set((state) => ({
      annotations: state.annotations.map((a) => (a.uuid === uuid ? { ...a, ...updates } : a)),
      modified: true,
    })),

  selectAnnotation: (uuid) =>
    set((state) => ({
      selectedUuid: uuid,
      annotations: state.annotations.map((a) => ({ ...a, selected: a.uuid === uuid })),
    })),

  clearSelection: () =>
    set((state) => ({
      selectedUuid: '',
      annotations: state.annotations.map((a) => ({ ...a, selected: false })),
    })),

  toggleVisibility: (uuid) =>
    set((state) => ({
      annotations: state.annotations.map((a) =>
        a.uuid === uuid ? { ...a, visible: !a.visible } : a,
      ),
    })),

  toggleSelectedVisibility: () => {
    const { selectedUuid } = get();
    if (!selectedUuid) return;
    set((state) => ({
      annotations: state.annotations.map((a) =>
        a.uuid === selectedUuid ? { ...a, visible: !a.visible } : a,
      ),
    }));
  },

  deleteSelected: () => {
    const { selectedUuid } = get();
    if (!selectedUuid) return;
    set((state) => ({
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

  setImageSize: (width, height) => set({ imageWidth: width, imageHeight: height }),

  reset: () =>
    set({
      annotations: [],
      selectedUuid: '',
      mode: LabelMode.Edit,
      modified: false,
      imageWidth: 0,
      imageHeight: 0,
    }),
}));
