export const DATASETS_CHANGED_EVENT = 'automl:datasets-changed';
export const ANNOTATIONS_CHANGED_EVENT = 'automl:annotations-changed';
export const TASKS_CHANGED_EVENT = 'automl:tasks-changed';

export function emitDatasetsChanged() {
  window.dispatchEvent(new CustomEvent(DATASETS_CHANGED_EVENT));
}

export function emitAnnotationsChanged() {
  window.dispatchEvent(new CustomEvent(ANNOTATIONS_CHANGED_EVENT));
}

export function emitTasksChanged() {
  window.dispatchEvent(new CustomEvent(TASKS_CHANGED_EVENT));
}
