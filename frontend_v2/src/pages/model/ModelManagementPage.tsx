import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Button, Card, Descriptions, Drawer, Empty, Popconfirm, Spin, Tabs, Tag, Tooltip, Typography, message } from 'antd';
import { DatabaseOutlined, DeleteOutlined, InfoCircleOutlined, PauseCircleOutlined, PlayCircleOutlined, ReloadOutlined, UploadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

import { getBaseModels } from '../../api/task';
import {
  deleteTrainingRuntimeCodePackage,
  getTrainingRuntimeCodePackage,
  importTrainingRuntimeCodePackage,
  listTrainingRuntimeCodePackages,
  updateTrainingRuntimeCodePackage,
} from '../../api/trainingRuntime';
import type {
  BaseModelResponse,
  TrainingRuntimeCodePackage,
} from '../../types';

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
  const codeFileInputRef = useRef<HTMLInputElement>(null);
  const [activeSource, setActiveSource] = useState<SourceTab>('builtin');
  const [category, setCategory] = useState<ModelCategory>('all');
  const [builtinModels, setBuiltinModels] = useState<BaseModelResponse[]>([]);
  const [externalCodePackages, setExternalCodePackages] = useState<TrainingRuntimeCodePackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [updatingPackageId, setUpdatingPackageId] = useState<number | null>(null);
  const [deletingPackageId, setDeletingPackageId] = useState<number | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailPackage, setDetailPackage] = useState<TrainingRuntimeCodePackage | null>(null);

  const loadModels = useCallback(async () => {
    setLoading(true);
    try {
      const [nextBuiltinModels, nextCodePackages] = await Promise.all([
        getBaseModels(),
        listTrainingRuntimeCodePackages(),
      ]);
      setBuiltinModels(nextBuiltinModels);
      setExternalCodePackages(nextCodePackages);
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
  const visibleCustomModels = useMemo(
    () => externalCodePackages.filter((model) => (
      category === 'all'
      || model.supported_tasks.some((task) => getModelCategory(task.task_kind) === category)
    )),
    [externalCodePackages, category],
  );

  const handleImportCodePackage = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.zip')) {
      message.warning(t('zipRequired'));
      return;
    }
    setUploading(true);
    try {
      const result = await importTrainingRuntimeCodePackage(file);
      message.success(
        result.catalog_created
          ? t('customModelImportSuccess', { name: result.package.name })
          : t('alreadyRegistered', { name: result.package.name }),
      );
      await loadModels();
    } catch (error) {
      message.error(getErrorMessage(error, t('importFailed')));
    } finally {
      setUploading(false);
    }
  };

  const handleOpenPackageDetail = async (packageId: number) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailPackage(null);
    try {
      const item = await getTrainingRuntimeCodePackage(packageId);
      if (!item) throw new Error(t('packageNotFound'));
      setDetailPackage(item);
    } catch (error) {
      message.error(getErrorMessage(error, t('loadPackageDetailFailed')));
      setDetailOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  const handlePackageEnabledChange = async (item: TrainingRuntimeCodePackage) => {
    setUpdatingPackageId(item.id);
    try {
      const updated = await updateTrainingRuntimeCodePackage(item.id, { enabled: !item.enabled });
      if (!updated) throw new Error(t('updatePackageFailed'));
      setExternalCodePackages((packages) => packages.map((current) => (
        current.id === updated.id ? updated : current
      )));
      setDetailPackage((current) => current?.id === updated.id ? updated : current);
      message.success(item.enabled ? t('packageDisabled') : t('packageEnabled'));
    } catch (error) {
      message.error(getErrorMessage(error, t('updatePackageFailed')));
    } finally {
      setUpdatingPackageId(null);
    }
  };

  const handleDeletePackage = async (item: TrainingRuntimeCodePackage) => {
    setDeletingPackageId(item.id);
    try {
      await deleteTrainingRuntimeCodePackage(item.id);
      setExternalCodePackages((packages) => packages.filter((current) => current.id !== item.id));
      if (detailPackage?.id === item.id) {
        setDetailOpen(false);
        setDetailPackage(null);
      }
      message.success(t('packageDeleted'));
    } catch (error) {
      message.error(getErrorMessage(error, t('deletePackageFailed')));
    } finally {
      setDeletingPackageId(null);
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
      <Card size="small" title={t('customModelsTitle')}>
        {visibleCustomModels.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={t('noCustomModels')} /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
            {visibleCustomModels.map((item) => (
              <Card
                key={item.id}
                size="small"
                styles={{ body: { minHeight: 226, display: 'flex', flexDirection: 'column', padding: 16 } }}
                style={{ height: '100%', borderRadius: 6, boxShadow: 'none', borderColor: '#e5e7eb', opacity: item.enabled ? 1 : 0.66 }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 600, color: '#1f2937' }}>{item.name}</div>
                    <Text type="secondary" ellipsis style={{ display: 'block' }}>
                      {item.package_key} · v{item.version} · {item.runtime_id}
                    </Text>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 5, flexShrink: 0 }}>
                    <div style={{ display: 'flex', gap: 4, whiteSpace: 'nowrap' }}>
                      <Tag color={item.enabled ? 'green' : 'default'}>{item.enabled ? t('enabled') : t('disabled')}</Tag>
                      <Tag color="geekblue">{item.supported_tasks.map((task) => task.task_kind).filter(Boolean).join(', ') || t('unknownTask')}</Tag>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 2, height: 24 }}>
                      <Tooltip title={t('viewPackageDetail')}>
                        <Button
                          aria-label={t('viewPackageDetail')}
                          type="text"
                          size="small"
                          icon={<InfoCircleOutlined />}
                          onClick={() => { void handleOpenPackageDetail(item.id); }}
                        />
                      </Tooltip>
                      <Tooltip title={item.enabled ? t('disablePackage') : t('enablePackage')}>
                        <Button
                          aria-label={item.enabled ? t('disablePackage') : t('enablePackage')}
                          type="text"
                          size="small"
                          icon={item.enabled ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                          loading={updatingPackageId === item.id}
                          onClick={() => { void handlePackageEnabledChange(item); }}
                        />
                      </Tooltip>
                      <Popconfirm
                        title={t('deletePackageTitle')}
                        description={t('deletePackageDescription')}
                        okText={common('action.delete')}
                        cancelText={common('action.cancel')}
                        okButtonProps={{ danger: true }}
                        onConfirm={() => { void handleDeletePackage(item); }}
                      >
                        <Tooltip title={t('deletePackage')}>
                          <Button
                            aria-label={t('deletePackage')}
                            type="text"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                            loading={deletingPackageId === item.id}
                          />
                        </Tooltip>
                      </Popconfirm>
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 10 }}>
                  {item.input_modes.map((mode) => <Tag key={mode} color={mode === 'script_managed' ? 'gold' : 'blue'}>{t(`inputMode.${mode}`)}</Tag>)}
                  {item.class_names.length > 0 ? <Tag color="cyan">{t('fixedClassCount', { count: item.class_names.length })}</Tag> : null}
                </div>
                <Text type="secondary" style={{ display: 'block', marginTop: 10, fontSize: 12 }}>
                  {t('packageMeta', {
                    fileName: item.package_file_name,
                    size: formatByteSize(item.package_size_bytes),
                    createdAt: dayjs(item.created_at).format('YYYY-MM-DD HH:mm'),
                  })}
                </Text>
              </Card>
            ))}
          </div>
        )}
      </Card>
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
            <Button type="primary" icon={<UploadOutlined />} loading={uploading} onClick={() => codeFileInputRef.current?.click()}>
              {t('importCustomModel')}
            </Button>
          ) : null}
        </div>
      </div>

      <input
        ref={codeFileInputRef}
        hidden
        type="file"
        accept=".zip,application/zip"
        onChange={(event) => {
          const file = event.currentTarget.files?.[0];
          event.currentTarget.value = '';
          if (file) void handleImportCodePackage(file);
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
      <Drawer
        title={detailPackage?.name || t('packageDetail')}
        open={detailOpen}
        width={720}
        onClose={() => setDetailOpen(false)}
        styles={{ body: { padding: 20 } }}
      >
        {detailLoading ? <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 100 }}><Spin /></div> : detailPackage ? (
          <>
            <Text type="secondary">{detailPackage.package_key} · v{detailPackage.version}</Text>
            <Descriptions size="small" column={1} style={{ margin: '16px 0 20px' }}>
              <Descriptions.Item label={t('detail.packageId')}>#{detailPackage.id}</Descriptions.Item>
              <Descriptions.Item label={t('detail.runtime')}>{detailPackage.runtime_id}</Descriptions.Item>
              <Descriptions.Item label={t('detail.entrypoint')}>{detailPackage.entrypoint}</Descriptions.Item>
              <Descriptions.Item label={t('detail.status')}>
                <Tag color={detailPackage.enabled ? 'green' : 'default'}>{detailPackage.enabled ? t('enabled') : t('disabled')}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('detail.tasks')}>
                {detailPackage.supported_tasks.map((task, index) => (
                  <Tag key={`${task.task_kind}-${index}`} color="geekblue">{task.task_kind || t('unknownTask')}</Tag>
                ))}
              </Descriptions.Item>
              <Descriptions.Item label={t('detail.inputModes')}>
                {detailPackage.input_modes.map((mode) => <Tag key={mode}>{t(`inputMode.${mode}`)}</Tag>)}
              </Descriptions.Item>
              <Descriptions.Item label={t('detail.classNames')}>
                {detailPackage.class_names.length > 0
                  ? detailPackage.class_names.map((className) => <Tag key={className} color="cyan">{className}</Tag>)
                  : t('dynamicClassNames')}
              </Descriptions.Item>
              <Descriptions.Item label={t('detail.packageFile')}>{detailPackage.package_file_name}</Descriptions.Item>
              <Descriptions.Item label={t('detail.packageSize')}>{formatByteSize(detailPackage.package_size_bytes)}</Descriptions.Item>
              <Descriptions.Item label={t('detail.createdAt')}>{dayjs(detailPackage.created_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
            </Descriptions>
            {detailPackage.description ? <Text type="secondary" style={{ display: 'block', whiteSpace: 'pre-wrap', marginBottom: 20 }}>{detailPackage.description}</Text> : null}
            <section style={{ borderTop: '1px solid #e5e7eb', paddingTop: 16 }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>{t('detail.parametersSchema')}</div>
              <pre style={{ margin: 0, padding: 12, borderRadius: 8, background: '#f8fafc', border: '1px solid #e5e7eb', overflow: 'auto', maxHeight: 260 }}>{JSON.stringify(detailPackage.parameters_schema, null, 2)}</pre>
            </section>
            <section style={{ borderTop: '1px solid #e5e7eb', paddingTop: 16, marginTop: 20 }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>{t('detail.outputContract')}</div>
              <pre style={{ margin: 0, padding: 12, borderRadius: 8, background: '#f8fafc', border: '1px solid #e5e7eb', overflow: 'auto', maxHeight: 260 }}>{JSON.stringify(detailPackage.output_contract, null, 2)}</pre>
            </section>
          </>
        ) : null}
      </Drawer>
    </div>
  );
};

export default ModelManagementPage;
