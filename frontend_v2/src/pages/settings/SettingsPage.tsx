import React, { useEffect, useState } from 'react';
import { SettingOutlined, CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { Switch, message } from 'antd';
import { useTranslation } from 'react-i18next';
import apiClient from '../../api/client';
import {
  getAnnotationDeleteConfirmEnabled,
  getDatasetDeleteConfirmEnabled,
  getDeployConfirmEnabled,
  getTaskDeleteConfirmEnabled,
  setAnnotationDeleteConfirmEnabled,
  setDatasetDeleteConfirmEnabled,
  setDeployConfirmEnabled,
  setTaskDeleteConfirmEnabled,
} from '../../utils/localSettings';

type ModuleState = 'enabled' | 'unavailable' | 'disabled';

type HealthResponse = {
  status: string;
  service: string;
  version?: string;
  modules?: Partial<Record<'dataset_mgmt' | 'annotation_mgmt' | 'train_task' | 'model_deploy' | 'predict_service' | 'user_mgmt', ModuleState>>;
  dependencies?: Partial<Record<'model_trainer' | 'model_deploy' | 'ai_pipeline_runtime', {
    status: ModuleState;
    version?: string | null;
  }>>;
};

const getConfiguredApiBaseUrl = () => {
  const base = import.meta.env.VITE_API_BASE_URL || '/api';
  if (/^https?:\/\//i.test(base)) {
    return base.replace(/\/+$/, '');
  }
  return new URL(base, window.location.origin).toString().replace(/\/+$/, '');
};

const SettingsPage: React.FC = () => {
  const { t } = useTranslation('settings');
  const tc = useTranslation('common').t;
  const [backendVersion, setBackendVersion] = useState<string>('-');
  const [platformName, setPlatformName] = useState<string>('AutoML Studio');
  const [datasetDeleteConfirmEnabled, setDatasetDeleteConfirmEnabledState] = useState(true);
  const [annotationDeleteConfirmEnabled, setAnnotationDeleteConfirmEnabledState] = useState(true);
  const [taskDeleteConfirmEnabled, setTaskDeleteConfirmEnabledState] = useState(true);
  const [deployConfirmEnabled, setDeployConfirmEnabledState] = useState(true);
  const [moduleStatusMap, setModuleStatusMap] = useState<Record<string, ModuleState>>({
    dataset_mgmt: 'enabled',
    annotation_mgmt: 'enabled',
    train_task: 'enabled',
    model_deploy: 'enabled',
    predict_service: 'enabled',
    user_mgmt: 'disabled',
  });
  const [dependencyMap, setDependencyMap] = useState<NonNullable<HealthResponse['dependencies']>>({});

  const modules = [
    { key: 'dataset_mgmt', name: t('datasetMgmt') },
    { key: 'annotation_mgmt', name: t('annotationMgmt') },
    { key: 'train_task', name: t('trainTask') },
    { key: 'model_deploy', name: t('modelDeploy') },
    { key: 'user_mgmt', name: t('userMgmt') },
    { key: 'predict_service', name: t('predictService') },
  ];
  const dependencyRows = [
    { key: 'model_trainer', label: t('trainTask') },
    { key: 'model_deploy', label: t('modelDeploy') },
    { key: 'ai_pipeline_runtime', label: t('aiPipelineRuntime') },
  ] as const;
  const apiBaseUrl = getConfiguredApiBaseUrl();

  useEffect(() => {
    let active = true;
    setDatasetDeleteConfirmEnabledState(getDatasetDeleteConfirmEnabled());
    setAnnotationDeleteConfirmEnabledState(getAnnotationDeleteConfirmEnabled());
    setTaskDeleteConfirmEnabledState(getTaskDeleteConfirmEnabled());
    setDeployConfirmEnabledState(getDeployConfirmEnabled());

    const loadHealth = async () => {
      try {
        const response = await apiClient.get<HealthResponse>('/health');
        if (!active) return;
        setBackendVersion(response.data.version || '-');
        setPlatformName(response.data.service || 'AutoML Studio');
        if (response.data.modules) {
          setModuleStatusMap((prev) => ({
            ...prev,
            ...response.data.modules,
          }));
        }
        if (response.data.dependencies) {
          setDependencyMap((prev) => ({
            ...prev,
            ...response.data.dependencies,
          }));
        }
      } catch {
        if (!active) return;
        setBackendVersion('-');
        setPlatformName('AutoML Studio');
      }
    };

    void loadHealth();
    return () => {
      active = false;
    };
  }, []);

  const handleConfirmDeleteChange = (
    checked: boolean,
    setter: React.Dispatch<React.SetStateAction<boolean>>,
    persist: (enabled: boolean) => void,
    label: string,
  ) => {
    setter(checked);
    persist(checked);
    message.success(`${label}${checked ? '已开启确认' : '已关闭确认'}`);
  };

  return (
    <div className="page-container" style={{ maxWidth: 700 }}>
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon">
            <SettingOutlined />
          </div>
          <div>
            <h1 className="page-title">{t('title')}</h1>
          </div>
        </div>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <h3 className="card-title" style={{ marginBottom: 16 }}>{t('systemInfo')}</h3>
        {[
          { label: t('platformName'), value: platformName },
          { label: t('version'), value: backendVersion },
          { label: t('apiAddress'), value: apiBaseUrl, mono: true },
          { label: t('backendProxy'), value: apiBaseUrl, mono: true },
        ].map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: i < 3 ? '1px solid #f8f8f8' : 'none' }}>
            <span className="body-text-sm" style={{ color: '#888' }}>{item.label}</span>
            <span className="body-text-sm" style={{ color: '#111', fontFamily: item.mono ? 'monospace' : 'inherit', background: item.mono ? '#f7f7f8' : 'none', padding: item.mono ? '2px 8px' : 0, borderRadius: 4 }}>{item.value}</span>
          </div>
          ))}
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <h3 className="card-title" style={{ marginBottom: 16 }}>{t('serviceVersions')}</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10 }}>
          {dependencyRows.map((item) => {
            const detail = dependencyMap[item.key];
            const version = detail?.version || '-';
            const status = detail?.status || 'unavailable';
            const versionText = version === '-' ? '-' : `v${version}`;
            return (
              <div key={item.key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#fafafa', borderRadius: 8 }}>
                <span className="body-text-sm" style={{ color: '#555' }}>{item.label}</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className="body-text-sm" style={{ color: '#111', fontFamily: 'monospace' }}>{versionText}</span>
                  {status === 'enabled' ? (
                    <span className="caption-text" style={{ color: '#16a34a', display: 'flex', alignItems: 'center', gap: 4 }}>{tc('status.enabled')}</span>
                  ) : (
                    <span className="caption-text" style={{ color: '#dc2626', display: 'flex', alignItems: 'center', gap: 4 }}>{tc('status.notAvailable')}</span>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <h3 className="card-title" style={{ marginBottom: 16 }}>删除确认</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 12, alignItems: 'center' }}>
          <span className="body-text-sm" style={{ color: '#555' }}>数据集删除需要确认</span>
          <Switch checked={datasetDeleteConfirmEnabled} onChange={(checked) => handleConfirmDeleteChange(checked, setDatasetDeleteConfirmEnabledState, setDatasetDeleteConfirmEnabled, '数据集删除')} />
          <span className="body-text-sm" style={{ color: '#555' }}>标注删除需要确认</span>
          <Switch checked={annotationDeleteConfirmEnabled} onChange={(checked) => handleConfirmDeleteChange(checked, setAnnotationDeleteConfirmEnabledState, setAnnotationDeleteConfirmEnabled, '标注删除')} />
          <span className="body-text-sm" style={{ color: '#555' }}>任务删除需要确认</span>
          <Switch checked={taskDeleteConfirmEnabled} onChange={(checked) => handleConfirmDeleteChange(checked, setTaskDeleteConfirmEnabledState, setTaskDeleteConfirmEnabled, '任务删除')} />
          <span className="body-text-sm" style={{ color: '#555' }}>部署下线需要确认</span>
          <Switch checked={deployConfirmEnabled} onChange={(checked) => handleConfirmDeleteChange(checked, setDeployConfirmEnabledState, setDeployConfirmEnabled, '部署下线')} />
        </div>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24 }}>
        <h3 className="card-title" style={{ marginBottom: 16 }}>{t('modules')}</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {modules.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#fafafa', borderRadius: 8 }}>
              <span className="body-text-sm" style={{ color: '#555' }}>{m.name}</span>
              {moduleStatusMap[m.key] === 'enabled' ? (
                <span className="caption-text" style={{ color: '#16a34a', display: 'flex', alignItems: 'center', gap: 4 }}><CheckCircleOutlined /> {tc('status.enabled')}</span>
              ) : moduleStatusMap[m.key] === 'unavailable' ? (
                <span className="caption-text" style={{ color: '#dc2626', display: 'flex', alignItems: 'center', gap: 4 }}><CloseCircleOutlined /> {tc('status.notAvailable')}</span>
              ) : (
                <span className="caption-text" style={{ color: '#bbb', display: 'flex', alignItems: 'center', gap: 4 }}><ClockCircleOutlined /> {tc('status.pending')}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
