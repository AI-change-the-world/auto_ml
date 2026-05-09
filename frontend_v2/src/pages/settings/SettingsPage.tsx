import React, { useEffect, useState } from 'react';
import { SettingOutlined, CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import apiClient from '../../api/client';

type ModuleState = 'enabled' | 'unavailable' | 'disabled';

type HealthResponse = {
  status: string;
  service: string;
  version?: string;
  modules?: Partial<Record<'dataset_mgmt' | 'annotation_mgmt' | 'train_task' | 'model_deploy' | 'predict_service' | 'user_mgmt', ModuleState>>;
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
  const [platformName, setPlatformName] = useState<string>('AutoML Platform');
  const [moduleStatusMap, setModuleStatusMap] = useState<Record<string, ModuleState>>({
    dataset_mgmt: 'enabled',
    annotation_mgmt: 'enabled',
    train_task: 'enabled',
    model_deploy: 'enabled',
    predict_service: 'enabled',
    user_mgmt: 'disabled',
  });

  const modules = [
    { key: 'dataset_mgmt', name: t('datasetMgmt') },
    { key: 'annotation_mgmt', name: t('annotationMgmt') },
    { key: 'train_task', name: t('trainTask') },
    { key: 'model_deploy', name: t('modelDeploy') },
    { key: 'user_mgmt', name: t('userMgmt') },
    { key: 'predict_service', name: t('predictService') },
  ];
  const apiBaseUrl = getConfiguredApiBaseUrl();

  useEffect(() => {
    let active = true;

    const loadHealth = async () => {
      try {
        const response = await apiClient.get<HealthResponse>('/health');
        if (!active) return;
        setBackendVersion(response.data.version || '-');
        setPlatformName(response.data.service || 'AutoML Platform');
        if (response.data.modules) {
          setModuleStatusMap((prev) => ({
            ...prev,
            ...response.data.modules,
          }));
        }
      } catch {
        if (!active) return;
        setBackendVersion('-');
        setPlatformName('AutoML Platform');
      }
    };

    void loadHealth();
    return () => {
      active = false;
    };
  }, []);

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
