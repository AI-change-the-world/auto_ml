import { useEffect, useRef } from 'react';
import { clearNavigationGuard, setNavigationGuard } from '../router/appHistory';

const DEFAULT_MESSAGE = '当前有未保存内容，离开后将丢失，确定继续离开吗？';

export function useUnsavedChangesGuard(
  hasUnsavedChanges: boolean,
  message: string = DEFAULT_MESSAGE,
) {
  const guardIdRef = useRef(Symbol('unsaved-changes-guard'));

  useEffect(() => {
    if (hasUnsavedChanges) {
      setNavigationGuard(guardIdRef.current, message);
      return () => clearNavigationGuard(guardIdRef.current);
    }
    clearNavigationGuard(guardIdRef.current);
    return undefined;
  }, [hasUnsavedChanges, message]);

  useEffect(() => {
    if (!hasUnsavedChanges) return;

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);
}
