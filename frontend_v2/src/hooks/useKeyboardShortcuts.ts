import { useEffect } from 'react';
import { useAnnotationStore } from '../stores/annotationStore';
import { useDatasetStore } from '../stores/datasetStore';

export function useKeyboardShortcuts() {
  const toggleMode = useAnnotationStore((s) => s.toggleMode);
  const deleteSelected = useAnnotationStore((s) => s.deleteSelected);
  const toggleSelectedVisibility = useAnnotationStore((s) => s.toggleSelectedVisibility);
  const clearSelection = useAnnotationStore((s) => s.clearSelection);

  const nextFile = useDatasetStore((s) => s.nextFile);
  const prevFile = useDatasetStore((s) => s.prevFile);
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
          toggleMode();
          break;
        case 'q':
          e.preventDefault();
          prevFile();
          break;
        case 'e':
          e.preventDefault();
          nextFile();
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
  }, [toggleMode, deleteSelected, toggleSelectedVisibility, clearSelection, nextFile, prevFile, saveCurrentAnnotation]);
}
