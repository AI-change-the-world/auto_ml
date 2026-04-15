import React from 'react';
import { SettingOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const SettingsPage: React.FC = () => {
  const { t } = useTranslation('settings');
  const tc = useTranslation('common').t;

  const modules = [
    { name: t('datasetMgmt'), enabled: true },
    { name: t('annotationMgmt'), enabled: true },
    { name: t('trainTask'), enabled: true },
    { name: t('modelDeploy'), enabled: true },
    { name: t('userMgmt'), enabled: false },
    { name: t('predictService'), enabled: false },
  ];
  return (
    <div className="page-container" style={{ maxWidth: 700 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 24 }}>
        <SettingOutlined /> {t('title')}
      </h1>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: '#111', marginBottom: 16 }}>{t('systemInfo')}</h3>
        {[
          { label: t('platformName'), value: 'AutoML Platform' },
          { label: t('version'), value: 'v2.0.0-dev' },
          { label: t('apiAddress'), value: `${window.location.origin}/api`, mono: true },
          { label: t('backendProxy'), value: 'http://localhost:8000', mono: true },
        ].map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: i < 3 ? '1px solid #f8f8f8' : 'none' }}>
            <span style={{ fontSize: 13, color: '#888' }}>{item.label}</span>
            <span style={{ fontSize: 13, color: '#111', fontFamily: item.mono ? 'monospace' : 'inherit', background: item.mono ? '#f7f7f8' : 'none', padding: item.mono ? '2px 8px' : 0, borderRadius: 4 }}>{item.value}</span>
          </div>
        ))}
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: '#111', marginBottom: 16 }}>{t('modules')}</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {modules.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#fafafa', borderRadius: 8 }}>
              <span style={{ fontSize: 13, color: '#555' }}>{m.name}</span>
              {m.enabled
                ? <span style={{ fontSize: 12, color: '#16a34a', display: 'flex', alignItems: 'center', gap: 4 }}><CheckCircleOutlined /> {tc('status.enabled')}</span>
                : <span style={{ fontSize: 12, color: '#bbb', display: 'flex', alignItems: 'center', gap: 4 }}><ClockCircleOutlined /> {tc('status.pending')}</span>
              }
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
