import { create } from 'zustand';
import type { AnnotationProject, AnnotationFile, DatasetFile, Dataset } from '../types';
import { getAnnotation, getAnnotationFiles, saveAnnotationFile } from '../api/annotation';
import { updateAnnotation as updateAnnotationApi } from '../api/annotation';
import { getDataset, getDatasetFiles, previewFile } from '../api/dataset';
import { AnnotationType, createClassificationAnnotation } from '../types';
import { toYoloFormat } from '../utils/yolo';
import { isImageFileName } from '../utils/file';
import { useAnnotationStore } from './annotationStore';
import { message } from 'antd';

interface DatasetStoreState {
  // 当前标注项目
  annotationProject: AnnotationProject | null;
  // 当前关联数据集
  dataset: Dataset | null;
  // 数据集文件列表 (图像文件)
  datasetFiles: DatasetFile[];
  // 标注文件列表
  annotationFiles: AnnotationFile[];
  // 当前文件索引
  currentFileIndex: number;
  // 当前图像 URL
  currentImageUrl: string;
  // 加载状态
  loading: boolean;

  // Actions
  loadAnnotationProject: (annotationId: number) => Promise<void>;
  loadFileAtIndex: (index: number) => Promise<void>;
  loadFileByName: (fileName: string) => Promise<void>;
  nextFile: () => Promise<void>;
  prevFile: () => Promise<void>;
  saveCurrentAnnotation: () => Promise<void>;
}

export const useDatasetStore = create<DatasetStoreState>((set, get) => ({
  annotationProject: null,
  dataset: null,
  datasetFiles: [],
  annotationFiles: [],
  currentFileIndex: -1,
  currentImageUrl: '',
  loading: false,

  loadAnnotationProject: async (annotationId: number) => {
    set({ loading: true });
    try {
      // 1. 获取标注项目
      const project = await getAnnotation(annotationId);
      set({ annotationProject: project, dataset: null });

      // 2. 设置 classes
      const annotationStore = useAnnotationStore.getState();
      if (project.classes) {
        try {
          const classes = JSON.parse(project.classes);
          annotationStore.setClasses(Array.isArray(classes) ? classes : []);
        } catch {
          // classes 可能是逗号分隔的字符串
          annotationStore.setClasses(project.classes.split(',').map((c: string) => c.trim()).filter(Boolean));
        }
      }

      // 3. 获取数据集文件列表
      if (project.dataset_id) {
        const [dataset, datasetResult] = await Promise.all([
          getDataset(project.dataset_id),
          getDatasetFiles(project.dataset_id),
        ]);
        const files = (datasetResult.items || []).filter((file) => isImageFileName(file.file_name));
        set({ dataset, datasetFiles: files });

        // 4. 获取标注文件列表
        const annotationResult = await getAnnotationFiles(annotationId, 1, 500);
        set({ annotationFiles: annotationResult.items || [] });

        // 5. 加载第一个文件
        if (files.length > 0) {
          await get().loadFileAtIndex(0);
        }
      }
    } catch (err) {
      console.error('Failed to load annotation project:', err);
      message.error('加载标注项目失败');
    } finally {
      set({ loading: false });
    }
  },

  loadFileAtIndex: async (index: number) => {
    const { datasetFiles, annotationFiles, annotationProject } = get();
    if (index < 0 || index >= datasetFiles.length || !annotationProject?.dataset_id) return;

    set({ loading: true, currentFileIndex: index });
    const annotationStore = useAnnotationStore.getState();

    try {
      const file = datasetFiles[index];

      // 获取图像预览 URL
      const preview = await previewFile(annotationProject.dataset_id, file.file_name);
      set({ currentImageUrl: preview.presigned_url });

      // 查找对应的标注文件
      const labelFileName = file.file_name.replace(/\.[^.]+$/, '.txt');
      const annotationFile = annotationFiles.find((f) => f.file_name === labelFileName);

      if (annotationFile?.content) {
        if (annotationProject.annotation_type === AnnotationType.Classification) {
          const classId = parseInt(annotationFile.content.trim(), 10);
          annotationStore.setAnnotations(Number.isNaN(classId) ? [] : [createClassificationAnnotation(classId)]);
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

  loadFileByName: async (fileName: string) => {
    const { datasetFiles } = get();
    const index = datasetFiles.findIndex((file) => file.file_name === fileName);
    if (index >= 0) {
      await get().loadFileAtIndex(index);
    }
  },

  nextFile: async () => {
    const { currentFileIndex, datasetFiles, annotationProject } = get();
    const annotationStore = useAnnotationStore.getState();

    // 自动保存
    if (annotationStore.modified && annotationProject) {
      await get().saveCurrentAnnotation();
    }

    if (currentFileIndex < datasetFiles.length - 1) {
      await get().loadFileAtIndex(currentFileIndex + 1);
    }
  },

  prevFile: async () => {
    const { currentFileIndex, annotationProject } = get();
    const annotationStore = useAnnotationStore.getState();

    // 自动保存
    if (annotationStore.modified && annotationProject) {
      await get().saveCurrentAnnotation();
    }

    if (currentFileIndex > 0) {
      await get().loadFileAtIndex(currentFileIndex - 1);
    }
  },

  saveCurrentAnnotation: async () => {
    const { annotationProject, datasetFiles, currentFileIndex } = get();
    if (!annotationProject || currentFileIndex < 0) return;

    const annotationStore = useAnnotationStore.getState();
    const file = datasetFiles[currentFileIndex];
    const labelFileName = file.file_name.replace(/\.[^.]+$/, '.txt');
    const content = annotationProject.annotation_type === AnnotationType.Classification
      ? String(annotationStore.annotations[0]?.classId ?? '').trim()
      : toYoloFormat(
        annotationStore.annotations,
        annotationStore.imageWidth,
        annotationStore.imageHeight,
      );

    try {
      await saveAnnotationFile(annotationProject.id, {
        file_name: labelFileName,
        content,
      });

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
