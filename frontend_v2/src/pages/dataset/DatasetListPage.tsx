import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Input } from 'antd';
import {
  PlusOutlined,
  DatabaseOutlined,
  SearchOutlined,
  PictureOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  ApartmentOutlined,
} from '@ant-design/icons';
import { listDatasets, createDataset, deleteDataset } from '../../api/dataset';
import type { Dataset, DatasetCreate } from '../../types';
import {
  DataTypeOptions,
  DataTypeLabels,
  DatasetScenarioType,
  getDatasetScenarioDefinition,
  getDatasetScenarioDefinitions,
  getDatasetScenarioLabel,
  createDefaultScenarioConfig,
  isAnyDpoDataset,
  isLlmConversationDataset,
  isMllmConversationDataset,
} from '../../types';
import { useTranslation } from 'react-i18next';

const createInitialFormData = (): DatasetCreate => ({
  name: '',
  data_type: 0,
  scenario_type: DatasetScenarioType.Normal,
  scenario_config: null,
});

const IMAGE_DATA_TYPE = 0;

const DatasetListPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation('dataset');
  const tc = useTranslation('common').t;
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState<DatasetCreate>(createInitialFormData());
  const currentDataType = formData.data_type ?? IMAGE_DATA_TYPE;
  const currentScenarioType = formData.scenario_type ?? DatasetScenarioType.Normal;
  const scenarioDefinitions = getDatasetScenarioDefinitions(currentDataType);
  const currentScenarioDefinition = getDatasetScenarioDefinition(currentDataType, currentScenarioType);
  const isAerialScenario = currentScenarioType === DatasetScenarioType.AerialStitch;
  const isLlmScenario = isLlmConversationDataset(currentDataType, currentScenarioType);
  const isMllmScenario = isMllmConversationDataset(currentDataType, currentScenarioType);
  const isDpoScenario = isAnyDpoDataset(currentDataType, currentScenarioType);

  const fetchDatasets = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listDatasets(1, 50, keyword || undefined);
      if (res) { setDatasets(res.items); setTotal(res.total); }
    } catch { message.error(tc('msg.loadFailed')); }
    finally { setLoading(false); }
  }, [keyword]);

  useEffect(() => { fetchDatasets(); }, [fetchDatasets]);

  const handleCreate = async () => {
    if (!formData.name.trim()) { message.warning(tc('msg.pleaseInputName')); return; }
    setCreating(true);
    try {
      const res = await createDataset(formData);
      message.success(tc('msg.createSuccess'));
      setCreateOpen(false);
      setFormData(createInitialFormData());
      fetchDatasets();
      if (res) navigate(`/datasets/${res.id}`);
    } catch { message.error(tc('msg.createFailed')); }
    finally { setCreating(false); }
  };

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    Modal.confirm({
      title: t('deleteTitle'), content: tc('msg.confirmDelete'),
      okButtonProps: { danger: true },
      onOk: async () => { await deleteDataset(id); message.success(tc('msg.deleted')); fetchDatasets(); },
    });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon">
            <DatabaseOutlined />
          </div>
          <div>
            <h1 className="page-title">{t('title')}</h1>
            <p className="page-subtitle">{t('subtitle')}</p>
          </div>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500,
            background: '#4f6ef7', color: '#fff', border: 'none', cursor: 'pointer',
          }}
        >
          <PlusOutlined /> {t('newDataset')}
        </button>
      </div>

      {/* Search */}
      <div style={{ marginBottom: 20, position: 'relative', maxWidth: 360 }}>
        <SearchOutlined style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#bbb', fontSize: 13 }} />
        <input
          style={{
            width: '100%', padding: '8px 12px 8px 34px', border: '1px solid #e5e5e5',
            borderRadius: 8, fontSize: 13, outline: 'none', background: '#fff',
          }}
          placeholder={t('searchPlaceholder')}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
      ) : datasets.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}>
          <DatabaseOutlined style={{ fontSize: 48, marginBottom: 12 }} />
          <p style={{ fontSize: 14 }}>{t('empty')}</p>
        </div>
      ) : (
        <div className="card-grid">
          {datasets.map((ds) => (
            <div
              key={ds.id}
              onClick={() => navigate(`/datasets/${ds.id}`)}
              style={{
                background: '#fff', border: '1px solid #eee', borderRadius: 12,
                overflow: 'hidden', cursor: 'pointer', transition: 'box-shadow 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.06)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
            >
              <div style={{
                height: 120, background: 'linear-gradient(135deg, #e0e7ff, #c7d2fe)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative',
              }}>
                <PictureOutlined style={{ fontSize: 36, color: '#a5b4fc' }} />
                <button
                  onClick={(e) => handleDelete(e, ds.id)}
                  style={{
                    position: 'absolute', top: 8, right: 8, width: 28, height: 28,
                    borderRadius: 6, background: 'rgba(255,255,255,0.8)', border: 'none',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#999', fontSize: 13, opacity: 0, transition: 'opacity 0.2s',
                  }}
                  className="card-delete-btn"
                >
                  <DeleteOutlined />
                </button>
              </div>
              <div style={{ padding: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color: '#111', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ds.name}</span>
                  <span style={{ fontSize: 11, padding: '1px 8px', background: '#eef2ff', color: '#4f6ef7', borderRadius: 999, flexShrink: 0 }}>
                    {DataTypeLabels[ds.data_type] ?? tc('status.unknown')}
                  </span>
                  <span style={{ fontSize: 11, padding: '1px 8px', background: '#f8fafc', color: '#475569', borderRadius: 999, flexShrink: 0 }}>
                    {getDatasetScenarioLabel(ds.data_type, ds.scenario_type)}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: '#999' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><PictureOutlined /> {ds.count} {tc('label.files')}</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><ClockCircleOutlined /> {new Date(ds.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 16, fontSize: 13, color: '#bbb', textAlign: 'center' }}>{t('totalDatasets', { count: total })}</div>

      <Modal title={t('newDataset')} open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); setFormData(createInitialFormData()); }} confirmLoading={creating} okText={tc('action.create')} cancelText={tc('action.cancel')}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{tc('label.name')}</label>
            <Input placeholder={t('inputName')} value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 8 }}>{t('dataType')}</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 8 }}>
              {DataTypeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => {
                    const nextDataType = option.value;
                    const nextScenarioDefinitions = getDatasetScenarioDefinitions(nextDataType);
                    const currentAllowed = nextScenarioDefinitions.find((item) => item.value === (formData.scenario_type ?? DatasetScenarioType.Normal));
                    const nextScenarioType = currentAllowed?.value ?? nextScenarioDefinitions[0]?.value ?? DatasetScenarioType.Normal;
                    setFormData({
                      ...formData,
                      data_type: nextDataType,
                      scenario_type: nextScenarioType,
                      scenario_config: createDefaultScenarioConfig(nextDataType, nextScenarioType),
                    });
                  }}
                  style={{
                    padding: '10px 12px', fontSize: 13, borderRadius: 8, cursor: 'pointer',
                    border: formData.data_type === option.value ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                    background: formData.data_type === option.value ? '#eef2ff' : '#fff',
                    color: formData.data_type === option.value ? '#4f6ef7' : '#334155',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: 2 }}>{option.label}</div>
                  <div style={{ fontSize: 12, color: formData.data_type === option.value ? '#4f6ef7' : '#94a3b8', lineHeight: 1.5 }}>
                    {option.description}
                  </div>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 8 }}>{t('scenarioType')}</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {scenarioDefinitions.map((scenario) => (
                <button
                  key={scenario.value}
                  onClick={() => setFormData({
                    ...formData,
                    scenario_type: scenario.value,
                    scenario_config: createDefaultScenarioConfig(currentDataType, scenario.value),
                  })}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    border: currentScenarioType === scenario.value ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                    background: currentScenarioType === scenario.value ? '#eef2ff' : '#fff',
                    color: '#334155',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: currentScenarioType === scenario.value ? '#4f6ef7' : '#0f172a' }}>
                      {scenario.label}
                    </span>
                    <span style={{ fontSize: 12, color: currentScenarioType === scenario.value ? '#4f6ef7' : '#94a3b8' }}>
                      {scenario.shortLabel}
                    </span>
                  </div>
                  <div style={{ marginTop: 4, fontSize: 12, color: '#64748b', lineHeight: 1.6 }}>
                    {scenario.description}
                  </div>
                </button>
              ))}
            </div>
            {currentScenarioDefinition && (
              <div style={{ marginTop: 8, padding: 10, borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0', color: '#475569', fontSize: 12, lineHeight: 1.7 }}>
                <div style={{ fontWeight: 600, marginBottom: 2 }}>
                  上传建议
                </div>
                <div>{currentScenarioDefinition.uploadHint}</div>
              </div>
            )}
            {isAerialScenario && (
              <div style={{ marginTop: 8, padding: 10, borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0', color: '#64748b', fontSize: 12, lineHeight: 1.7 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#0f766e', fontWeight: 600, marginBottom: 2 }}>
                  <ApartmentOutlined /> {t('aerialScenarioTitle')}
                </div>
                <div>{t('aerialScenarioDesc')}</div>
                <div style={{ marginTop: 4, color: '#94a3b8' }}>{t('aerialNamingExample')}</div>
              </div>
            )}
            {(isLlmScenario || isMllmScenario) && (
              <div style={{ marginTop: 8, padding: 10, borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0', color: '#475569', fontSize: 12, lineHeight: 1.7 }}>
                <div style={{ fontWeight: 600, marginBottom: 2 }}>
                  {isLlmScenario ? 'LLM 对话数据集' : 'MLLM 对话数据集'}
                </div>
                <div>标注结果按 JSON 保存，适合多轮对话式标注。</div>
                <div style={{ marginTop: 4, color: '#94a3b8' }}>
                  {isLlmScenario ? '建议上传 txt、md、json 等文本文件。' : '建议上传图像文件，标注时逐张补充对话。'}
                </div>
              </div>
            )}
            {isDpoScenario && (
              <div style={{ marginTop: 8, padding: 10, borderRadius: 8, background: '#fffdf4', border: '1px solid #fde68a', color: '#713f12', fontSize: 12, lineHeight: 1.7 }}>
                <div style={{ fontWeight: 600, marginBottom: 2 }}>
                  DPO 偏好数据集
                </div>
                <div>用于同一 prompt 下两条候选回复的偏好标注。首期只支持文本 JSONL 导入。</div>
                <div style={{ marginTop: 4, color: '#a16207' }}>
                  建议上传 `.jsonl` 文件，结构需与当前 DPO 子场景匹配。
                </div>
              </div>
            )}
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{tc('label.description')}</label>
            <Input.TextArea rows={3} placeholder={t('optionalDesc')} value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DatasetListPage;
