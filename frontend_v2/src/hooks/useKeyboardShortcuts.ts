import { useEffect } from 'react';
import { message } from 'antd';
import { useAnnotationStore } from '../stores/annotationStore';
import { useDatasetStore } from '../stores/datasetStore';

export function useKeyboardShortcuts() {
  const toggleMode = useAnnotationStore((s) => s.toggleMode);
  const mode = useAnnotationStore((s) => s.mode);
  const deleteSelected = useAnnotationStore((s) => s.deleteSelected);
  const toggleSelectedVisibility = useAnnotationStore((s) => s.toggleSelectedVisibility);
  const clearSelection = useAnnotationStore((s) => s.clearSelection);

  const nextSample = useDatasetStore((s) => s.nextSample);
  const prevSample = useDatasetStore((s) => s.prevSample);
  const saveCurrentAnnotation = useDatasetStore((s) => s.saveCurrentAnnotation);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 忽略输入框中的按键
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      switch (e.key.toLowerCase()) {
        case 'w':
          e.preventDefault();
          const nextMode = mode === 'edit' ? 'add' : 'edit';
          toggleMode();
          message.success(nextMode === 'add' ? '已切换到标注模式' : '已切换到修改模式');
          break;
        case 'q':
          e.preventDefault();
          prevSample();
          break;
        case 'e':
          e.preventDefault();
          nextSample();
          break;
        case 's':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            saveCurrentAnnotation();
          }
          break;
        case 'd':
        case 'delete':
          e.preventDefault();
          deleteSelected();
          break;
        case 'h':
          e.preventDefault();
          toggleSelectedVisibility();
          break;
        case 'escape':
          e.preventDefault();
          clearSelection();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleMode, mode, deleteSelected, toggleSelectedVisibility, clearSelection, nextSample, prevSample, saveCurrentAnnotation]);
}
