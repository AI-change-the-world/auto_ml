import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Button, Card, Empty, Spin, Tabs, Tag, Typography, message } from 'antd';
import { DatabaseOutlined, ReloadOutlined, UploadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

import { getBaseModels } from '../../api/task';
import {
  importTrainingRuntimeModelPackage,
  listTrainingRuntimeModelPackages,
} from '../../api/trainingRuntime';
import type { BaseModelResponse, TrainingRuntimeModelPackage } from '../../types';

const { Text } = Typography;

type SourceTab = 'builtin' | 'external';
type ModelCategory = 'all' | 'detection' | 'classification' | 'segmentation' | 'pose' | 'other';

const modelCategories: ModelCategory[] = [
  'all',
  'detection',
  'classification',
  'segmentation',
  'pose',
  'other',
];

function getModelCategory(modelType: string | null | undefined): ModelCategory {
  const normalized = (modelType || '').trim().toLowerCase();
  if (normalized.includes('classification')) return 'classification';
  if (normalized.includes('segmentation')) return 'segmentation';
  if (normalized.includes('pose')) return 'pose';
  if (normalized.includes('detection') || normalized.includes('detect')) return 'detection';
  return 'other';
}

function formatByteSize(sizeBytes: number) {
  if (sizeBytes < 1024) return `${sizeBytes} B`;
  const units = ['KB', 'MB', 'GB'];
  let value = sizeBytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[unitIndex]}`;
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

const ModelManagementPage: React.FC = () => {
  const { t } = useTranslation('trainingRuntime');
  const { t: common } = useTranslation('common');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeSource, setActiveSource] = useState<SourceTab>('builtin');
  const [category, setCategory] = useState<ModelCategory>('all');
  const [builtinModels, setBuiltinModels] = useState<BaseModelResponse[]>([]);
  const [externalModels, setExternalModels] = useState<TrainingRuntimeModelPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const loadModels = useCallback(async () => {
    setLoading(true);
    try {
      const [nextBuiltinModels, nextExternalModels] = await Promise.all([
        getBaseModels(),
        listTrainingRuntimeModelPackages(),
      ]);
      setBuiltinModels(nextBuiltinModels);
      setExternalModels(nextExternalModels);
    } catch (error) {
      message.error(getErrorMessage(error, t('loadFailed')));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void loadModels();
  }, [loadModels]);

  const visibleBuiltinModels = useMemo(
    () => builtinModels.filter((model) => category === 'all' || getModelCategory(model.model_type) === category),
    [builtinModels, category],
  );
  const visibleExternalModels = useMemo(
    () => externalModels.filter((model) => category === 'all' || getModelCategory(model.task_kind) === category),
    [externalModels, category],
  );

  const handleImport = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.zip')) {
      message.warning(t('zipRequired'));
      return;
    }
    setUploading(true);
    try {
      const result = await importTrainingRuntimeModelPackage(file);
      message.success(
        result.catalog_created
          ? t('modelImportSuccess', { name: result.package.name })
          : t('alreadyRegistered', { name: result.package.name }),
      );
      await loadModels();
    } catch (error) {
      message.error(getErrorMessage(error, t('importFailed')));
    } finally {
      setUploading(false);
    }
  };

  const categoryBar = (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
      {modelCategories.map((nextCategory) => (
        <Button
          key={nextCategory}
          size="small"
          type={category === nextCategory ? 'primary' : 'default'}
          onClick={() => setCategory(nextCategory)}
        >
          {t(`category.${nextCategory}`)}
        </Button>
      ))}
    </div>
  );

  const builtinContent = loading ? <div className="settings-section-panel" style={{ padding: 80, textAlign: 'center' }}><Spin size="large" /></div> : (
    <div className="settings-section-panel">
      <Card size="small" style={{ marginBottom: 16, borderColor: '#bfdbfe', background: '#eff6ff' }}>
        <Text type="secondary">{t('builtinHint')}</Text>
      </Card>
      {categoryBar}
      {visibleBuiltinModels.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={t('noBuiltinModels')} /> : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
          {visibleBuiltinModels.map((model) => (
            <Card key={model.id} size="small">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600, color: '#1f2937' }}>{model.name}</div>
                  <Text type="secondary" ellipsis style={{ display: 'block' }}>
                    {model.description || t('noDescription')}
                  </Text>
                </div>
                <Tag color="blue">{t(`category.${getModelCategory(model.model_type)}`)}</Tag>
              </div>
              <Text type="secondary" style={{ display: 'block', marginTop: 10, fontSize: 12 }}>
                {t('builtinModelId', { id: model.id })}
              </Text>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  const externalContent = loading ? <div className="settings-section-panel" style={{ padding: 80, textAlign: 'center' }}><Spin size="large" /></div> : (
    <div className="settings-section-panel">
      <Card size="small" style={{ marginBottom: 16, borderColor: '#c7d2fe', background: '#eef2ff' }}>
        <Text type="secondary">{t('externalHint')}</Text>
      </Card>
      {categoryBar}
      {visibleExternalModels.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={t('noExternalModels')} /> : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
          {visibleExternalModels.map((model) => (
            <Card key={model.id} size="small">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600, color: '#1f2937' }}>{model.name}</div>
                  <Text type="secondary" ellipsis style={{ display: 'block' }}>
                    {model.framework_id} {model.framework_version} · .{model.artifact_format}
                  </Text>
                </div>
                <Tag color="purple">{t(`category.${getModelCategory(model.task_kind)}`)}</Tag>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 10 }}>
                <Tag>{t('classCount', { count: model.class_names.length })}</Tag>
                {model.has_resume_checkpoint ? <Tag color="green">{t('resumeAvailable')}</Tag> : null}
              </div>
              <Text type="secondary" style={{ display: 'block', marginTop: 10, fontSize: 12 }}>
                {t('packageMeta', {
                  fileName: model.package_file_name,
                  size: formatByteSize(model.package_size_bytes),
                  createdAt: dayjs(model.created_at).format('YYYY-MM-DD HH:mm'),
                })}
              </Text>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon"><DatabaseOutlined /></div>
          <div>
            <h1 className="page-title">{t('modelManagementTitle')}</h1>
            <p className="page-subtitle">{t('modelManagementSubtitle')}</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button icon={<ReloadOutlined />} onClick={() => void loadModels()} loading={loading}>
            {common('action.refresh')}
          </Button>
          {activeSource === 'external' ? (
            <Button type="primary" icon={<UploadOutlined />} loading={uploading} onClick={() => fileInputRef.current?.click()}>
              {t('importModelPackage')}
            </Button>
          ) : null}
        </div>
      </div>

      <input
        ref={fileInputRef}
        hidden
        type="file"
        accept=".zip,application/zip"
        onChange={(event) => {
          const file = event.currentTarget.files?.[0];
          event.currentTarget.value = '';
          if (file) void handleImport(file);
        }}
      />

      <Tabs
        className="settings-section-tabs"
        activeKey={activeSource}
        onChange={(key) => setActiveSource(key as SourceTab)}
        animated={false}
        items={[
          {
            key: 'builtin',
            label: <span className="flex items-center gap-2"><DatabaseOutlined />{t('builtinTab')}</span>,
            children: builtinContent,
          },
          {
            key: 'external',
            label: <span className="flex items-center gap-2"><UploadOutlined />{t('externalTab')}</span>,
            children: externalContent,
          },
        ]}
      />
    </div>
  );
};

export default ModelManagementPage;
