import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Input, Select, Tag } from 'antd';
import { PlusOutlined, TagsOutlined, SearchOutlined } from '@ant-design/icons';
import { listAnnotations, createAnnotation, deleteAnnotation, updateAnnotation, listAnnotationTypes } from '../../api/annotation';
import { listDatasets } from '../../api/dataset';
import type { AnnotationProject, AnnotationCreate } from '../../types/annotation';
import type { Dataset } from '../../types/dataset';
import {
  AnnotationType,
  DataTypeLabels,
  DefaultAnnotationTypeRegistry,
  createAnnotationTypeRegistry,
  getDatasetScenarioLabel,
} from '../../types';
import { useTranslation } from 'react-i18next';
import AnnotationProjectCard, { renderAnnotationTypeIcon } from './components/AnnotationProjectCard';
import { parseAnnotationClasses, serializeAnnotationClasses } from '../../utils/annotationClasses';
import { emitAnnotationsChanged } from '../../utils/projectEvents';
import {
  AnnotationCategoryDefinitions,
  getAllowedAnnotationTypesForDataset,
  getCompatibleDatasetsForAnnotationType,
  getAnnotationCategoryDefinition,
  getAnnotationTypePreset,
  isDatasetCompatibleWithAnnotationType,
} from '../../utils/annotationCompatibility';

const AnnotationListPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation('annotation');
  const tc = useTranslation('common').t;
  const [annotations, setAnnotations] = useState<AnnotationProject[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [formData, setFormData] = useState<AnnotationCreate>({ name: '', annotation_type: 0 });
  const [selectedCategoryKey, setSelectedCategoryKey] = useState<'image' | 'conversation' | 'preference'>('image');
  const [annotationTypeRegistry, setAnnotationTypeRegistry] = useState(DefaultAnnotationTypeRegistry);

  // ─── Classes 编辑 Modal ───
  const [classesModalOpen, setClassesModalOpen] = useState(false);
  const [classesEditId, setClassesEditId] = useState<number | null>(null);
  const [classesEditList, setClassesEditList] = useState<string[]>([]);
  const [classesImportText, setClassesImportText] = useState('');

  const openClassesModal = (e: React.MouseEvent, ann: AnnotationProject) => {
    e.stopPropagation();
    setClassesEditId(ann.id);
    setClassesEditList(parseAnnotationClasses(ann.classes));
    setClassesImportText('');
    setClassesModalOpen(true);
  };

  const handleClassesImport = () => {
    const items = parseAnnotationClasses(classesImportText);
    if (items.length === 0) return;
    const existing = new Set(classesEditList);
    const merged = [...classesEditList];
    for (const item of items) {
      if (!existing.has(item)) {
        merged.push(item);
        existing.add(item);
      }
    }
    setClassesEditList(merged);
    setClassesImportText('');
  };

  const handleClassesSave = async () => {
    if (classesEditId === null) return;
    try {
      await updateAnnotation(classesEditId, { classes: serializeAnnotationClasses(classesEditList) });
      message.success('类别已保存');
      setClassesModalOpen(false);
      fetch(); // 刷新列表
    } catch {
      message.error('保存类别失败');
    }
  };

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listAnnotations(1, 50, keyword || undefined);
      if (res) { setAnnotations(res.items); setTotal(res.total); }

      const typeDefinitions = await listAnnotationTypes().catch(() => []);
      if (typeDefinitions.length > 0) setAnnotationTypeRegistry(createAnnotationTypeRegistry(typeDefinitions));
    } catch { message.error(tc('msg.loadFailed')); }
    finally { setLoading(false); }
  }, [keyword]);

  useEffect(() => { fetch(); }, [fetch]);

  const openCreate = async () => {
    setCreateOpen(true);
    try { const r = await listDatasets(1, 100); if (r) setDatasets(r.items); } catch { }
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) { message.warning(tc('msg.pleaseInputName')); return; }
    const selectedDataset = datasets.find((item) => item.id === formData.dataset_id);
    const selectedType = annotationTypeRegistry[formData.annotation_type ?? AnnotationType.Detection];
    if (!selectedDataset) {
      message.warning(tc('msg.pleaseSelectDataset'));
      return;
    }
    if (!isDatasetCompatibleWithAnnotationType(selectedDataset, formData.annotation_type ?? AnnotationType.Detection)) {
      message.warning('当前标注类型与所选数据集不兼容，请重新选择');
      return;
    }
    setCreating(true);
    try {
      const payload = selectedType?.supportsClasses
        ? { ...formData, classes: serializeAnnotationClasses(formData.classes) }
        : { ...formData, classes: undefined };
      await createAnnotation(payload);
      message.success(tc('msg.createSuccess'));
      emitAnnotationsChanged();
      setCreateOpen(false);
      setFormData({ name: '', annotation_type: 0 });
      setSelectedCategoryKey('image');
      fetch();
    } catch { message.error(tc('msg.createFailed')); }
    finally { setCreating(false); }
  };

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    Modal.confirm({
      title: t('deleteTitle'), content: tc('msg.confirmDelete'), okButtonProps: { danger: true },
      onOk: async () => {
        await deleteAnnotation(id);
        emitAnnotationsChanged();
        message.success(tc('msg.deleted'));
        fetch();
      },
    });
  };

  const selectedDataset = datasets.find((item) => item.id === formData.dataset_id);
  const selectedCategory = getAnnotationCategoryDefinition(selectedCategoryKey);
  const categoryAnnotationTypes = (selectedCategory?.annotationTypes ?? [])
    .map((value) => annotationTypeRegistry[value])
    .filter((item) => item !== undefined);
  const compatibleDatasets = getCompatibleDatasetsForAnnotationType(
    datasets,
    formData.annotation_type,
  );
  const selectedAnnotationType = annotationTypeRegistry[formData.annotation_type ?? AnnotationType.Detection];
  const selectedTypePreset = getAnnotationTypePreset(formData.annotation_type ?? AnnotationType.Detection);

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon">
            <TagsOutlined />
          </div>
          <div>
            <h1 className="page-title">{t('title')}</h1>
            <p className="page-subtitle">{t('subtitle')}</p>
          </div>
        </div>
        <button onClick={openCreate} style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          padding: '8px 16px', borderRadius: 8,
          background: '#4f6ef7', color: '#fff', border: 'none', cursor: 'pointer',
        }} className="button-text">
          <PlusOutlined /> {t('newAnnotation')}
        </button>
      </div>

      <div style={{ marginBottom: 20, position: 'relative', maxWidth: 360 }}>
        <SearchOutlined style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#bbb', fontSize: 13 }} />
        <input
          style={{ width: '100%', padding: '8px 12px 8px 34px', border: '1px solid #e5e5e5', borderRadius: 8, outline: 'none' }}
          className="body-text-sm"
          placeholder={t('searchPlaceholder')}
          value={keyword} onChange={(e) => setKeyword(e.target.value)}
        />
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
      ) : annotations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}>
          <TagsOutlined style={{ fontSize: 48, marginBottom: 12 }} />
          <p className="empty-text">{t('empty')}</p>
        </div>
      ) : (
        <div className="card-grid">
          {annotations.map((ann) => (
            <AnnotationProjectCard
              key={ann.id}
              annotation={ann}
              typeModel={annotationTypeRegistry[ann.annotation_type]}
              unknownLabel={tc('status.unknown')}
              t={t}
              onOpen={(annotation) => navigate(`/annotations/${annotation.id}/label`)}
              onEditClasses={openClassesModal}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      <div className="body-text-sm" style={{ marginTop: 16, color: '#bbb', textAlign: 'center' }}>{t('totalAnnotations', { count: total })}</div>

      {/* ─── 编辑类别 Modal ─── */}
      <Modal
        title={<span className="modal-title">编辑类别</span>}
        open={classesModalOpen}
        onOk={handleClassesSave}
        onCancel={() => setClassesModalOpen(false)}
        okText="保存"
        cancelText="取消"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12 }}>
          {/* 批量导入 */}
          <div>
            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>批量导入</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <Input.TextArea
                rows={2}
                placeholder="粘贴类别名，用 ; 或 , 或换行分隔&#10;如: person;car;bike"
                value={classesImportText}
                onChange={(e) => setClassesImportText(e.target.value)}
                style={{ flex: 1 }}
              />
              <button
                className="button-text"
                onClick={handleClassesImport}
                style={{
                  padding: '4px 12px', borderRadius: 6, cursor: 'pointer',
                  background: '#4f6ef7', color: '#fff', border: 'none', alignSelf: 'flex-end',
                }}
              >
                导入
              </button>
            </div>
          </div>

          {/* 已有类别列表 */}
          <div>
            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>当前类别 ({classesEditList.length})</label>
            {classesEditList.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, padding: '8px 0' }}>
                {classesEditList.map((cls, idx) => (
                  <Tag
                    key={idx}
                    closable
                    onClose={(e) => {
                      e.preventDefault();
                      setClassesEditList(classesEditList.filter((_, i) => i !== idx));
                    }}
                    className="caption-text"
                  >
                    {cls}
                  </Tag>
                ))}
              </div>
            ) : (
              <div className="caption-text" style={{ padding: '8px 0', color: '#bbb' }}>暂无类别，请导入或在标注时自动生成</div>
            )}
          </div>
        </div>
      </Modal>

      <Modal title={<span className="modal-title">{t('newAnnotation')}</span>} open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); setFormData({ name: '', annotation_type: 0 }); setSelectedCategoryKey('image'); }} confirmLoading={creating} okText={tc('action.create')} cancelText={tc('action.cancel')}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
          <div>
            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{tc('label.name')}</label>
            <Input placeholder={t('inputName')} value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          </div>
          <div>
            <label className="form-label" style={{ display: 'block', marginBottom: 8 }}>标注大类</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8 }}>
              {AnnotationCategoryDefinitions.map((category) => (
                <button
                  key={category.key}
                  onClick={() => {
                    const nextType = category.annotationTypes[0] ?? AnnotationType.Detection;
                    const nextDataset = datasets.find((item) => formData.dataset_id === item.id);
                    const nextCompatible = nextDataset && isDatasetCompatibleWithAnnotationType(nextDataset, nextType)
                      ? formData.dataset_id
                      : undefined;
                    setSelectedCategoryKey(category.key);
                    setFormData({
                      ...formData,
                      annotation_type: nextType,
                      dataset_id: nextCompatible,
                      classes: annotationTypeRegistry[nextType]?.supportsClasses ? formData.classes : undefined,
                    });
                  }}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    border: selectedCategoryKey === category.key ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                    background: selectedCategoryKey === category.key ? '#eef2ff' : '#fff',
                    textAlign: 'left',
                  }} className="button-text"
                >
                  <div className="body-text-sm" style={{ fontWeight: 600, color: selectedCategoryKey === category.key ? '#4f6ef7' : '#0f172a', marginBottom: 2 }}>
                    {category.label}
                  </div>
                  <div className="caption-text" style={{ color: '#64748b', lineHeight: 1.5 }}>
                    {category.description}
                  </div>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="form-label" style={{ display: 'block', marginBottom: 8 }}>{t('annotationType')}</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {categoryAnnotationTypes.map((typeModel) => {
                const preset = getAnnotationTypePreset(typeModel.value);
                const selected = formData.annotation_type === typeModel.value;
                return (
                  <button
                    key={typeModel.value}
                    onClick={() => {
                      const nextCompatibleDatasets = getCompatibleDatasetsForAnnotationType(datasets, typeModel.value);
                      const nextDatasetId = nextCompatibleDatasets.some((item) => item.id === formData.dataset_id)
                        ? formData.dataset_id
                        : nextCompatibleDatasets[0]?.id;
                      setFormData({
                        ...formData,
                        annotation_type: typeModel.value,
                        dataset_id: nextDatasetId,
                        classes: typeModel.supportsClasses ? formData.classes : undefined,
                      });
                    }}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 8,
                      cursor: 'pointer',
                      border: selected ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                      background: selected ? '#eef2ff' : '#fff',
                      color: '#334155',
                      textAlign: 'left',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 10,
                    }} className="button-text"
                    disabled={typeModel.value === AnnotationType.Pose}
                  >
                    <span style={{ marginTop: 2 }}>
                      {renderAnnotationTypeIcon(typeModel.iconKey, selected ? '#4f6ef7' : '#8c8c8c', 14)}
                    </span>
                    <span style={{ flex: 1 }}>
                      <div className="body-text-sm" style={{ fontWeight: 600, color: selected ? '#4f6ef7' : '#0f172a', marginBottom: 2 }}>
                        {typeModel.value === AnnotationType.Pose ? `${typeModel.label} (占位)` : typeModel.label}
                      </div>
                      <div className="caption-text" style={{ color: '#64748b', lineHeight: 1.5 }}>
                        {preset?.description}
                      </div>
                    </span>
                  </button>
                );
              })}
            </div>
            {selectedTypePreset && (
              <div className="caption-text" style={{ marginTop: 8, padding: 10, borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0', color: '#475569', lineHeight: 1.7 }}>
                <div className="body-text-sm" style={{ fontWeight: 600, marginBottom: 2 }}>数据集要求</div>
                <div>{selectedTypePreset.datasetHint}</div>
              </div>
            )}
          </div>
          <div>
            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('linkedDataset')}</label>
            <Select placeholder={t('selectDataset')} allowClear style={{ width: '100%' }} value={formData.dataset_id}
              onChange={(v) => {
                const nextDataset = compatibleDatasets.find((item) => item.id === v);
                const nextAllowedTypes = getAllowedAnnotationTypesForDataset(nextDataset)
                  .filter((value) => selectedCategory?.annotationTypes.includes(value) ?? true);
                let nextAnnotationType = formData.annotation_type ?? AnnotationType.Detection;
                if (!nextAllowedTypes.includes(nextAnnotationType)) {
                  nextAnnotationType = nextAllowedTypes[0] ?? AnnotationType.Detection;
                }
                setFormData({ ...formData, dataset_id: v, annotation_type: nextAnnotationType });
              }}
              options={compatibleDatasets.map((ds) => ({
                label: `${ds.name} · ${DataTypeLabels[ds.data_type] ?? '未知'} · ${getDatasetScenarioLabel(ds.data_type, ds.scenario_type)}`,
                value: ds.id,
              }))}
            />
            {compatibleDatasets.length === 0 && (
              <div className="caption-text" style={{ marginTop: 6, color: '#b45309' }}>
                当前没有与该标注类型兼容的数据集，请先创建对应类型的数据集。
              </div>
            )}
            {selectedDataset && (
              <div className="caption-text" style={{ marginTop: 6, color: '#888' }}>
                当前数据集类型：{DataTypeLabels[selectedDataset.data_type] ?? '未知'} / {getDatasetScenarioLabel(selectedDataset.data_type, selectedDataset.scenario_type)}
              </div>
            )}
          </div>
          {selectedAnnotationType?.supportsClasses && (
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('initialClasses')}</label>
              <Input.TextArea rows={2} placeholder={t('classesPlaceholder')} value={formData.classes}
                onChange={(e) => setFormData({ ...formData, classes: e.target.value })} />
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default AnnotationListPage;
