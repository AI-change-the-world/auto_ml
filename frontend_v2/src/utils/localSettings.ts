const SETTINGS_PREFIX = 'auto_ml.settings.';

const MODULE_KEYS = {
  datasetDeleteConfirm: 'datasetDeleteConfirm',
  annotationDeleteConfirm: 'annotationDeleteConfirm',
  taskDeleteConfirm: 'taskDeleteConfirm',
  deployConfirm: 'deployConfirm',
} as const;

type ModuleSettingKey = keyof typeof MODULE_KEYS;

function getBooleanSetting(key: ModuleSettingKey, defaultValue = true): boolean {
  if (typeof window === 'undefined') return defaultValue;
  try {
    const value = window.localStorage.getItem(`${SETTINGS_PREFIX}${MODULE_KEYS[key]}`);
    if (value === null) return defaultValue;
    return value !== 'false';
  } catch {
    return defaultValue;
  }
}

function setBooleanSetting(key: ModuleSettingKey, enabled: boolean) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(`${SETTINGS_PREFIX}${MODULE_KEYS[key]}`, String(enabled));
  } catch {
    // ignore
  }
}

export function getDatasetDeleteConfirmEnabled() {
  return getBooleanSetting('datasetDeleteConfirm');
}

export function setDatasetDeleteConfirmEnabled(enabled: boolean) {
  setBooleanSetting('datasetDeleteConfirm', enabled);
}

export function getAnnotationDeleteConfirmEnabled() {
  return getBooleanSetting('annotationDeleteConfirm');
}

export function setAnnotationDeleteConfirmEnabled(enabled: boolean) {
  setBooleanSetting('annotationDeleteConfirm', enabled);
}

export function getTaskDeleteConfirmEnabled() {
  return getBooleanSetting('taskDeleteConfirm');
}

export function setTaskDeleteConfirmEnabled(enabled: boolean) {
  setBooleanSetting('taskDeleteConfirm', enabled);
}

export function getDeployConfirmEnabled() {
  return getBooleanSetting('deployConfirm');
}

export function setDeployConfirmEnabled(enabled: boolean) {
  setBooleanSetting('deployConfirm', enabled);
}
