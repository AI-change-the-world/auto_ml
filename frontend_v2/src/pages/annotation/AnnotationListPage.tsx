import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Input, Select } from 'antd';
import {
  PlusOutlined, TagsOutlined, SearchOutlined, ClockCircleOutlined,
  DeleteOutlined, EditOutlined,
} from '@ant-design/icons';
import { listAnnotations, createAnnotation, deleteAnnotation } from '../../api/annotation';
import { listDatasets } from '../../api/dataset';
import type { AnnotationProject, AnnotationCreate } from '../../types/annotation';
import type { Dataset } from '../../types/dataset';
import { AnnotationTypeLabels, AnnotationTypeColors } from '../../types/annotation';
import { useTranslation } from 'react-i18next';

const colorMap: Record<string, { bg: string; fg: string }> = {
  blue: { bg: '#eef2ff', fg: '#4f6ef7' },
  green: { bg: '#f0fdf4', fg: '#16a34a' },
  orange: { bg: '#fff7ed', fg: '#ea580c' },
  purple: { bg: '#faf5ff', fg: '#9333ea' },
};

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

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listAnnotations(1, 50, keyword || undefined);
      if (res) { setAnnotations(res.items); setTotal(res.total); }
    } catch { message.error(tc('msg.loadFailed')); }
    finally { setLoading(false); }
  }, [keyword]);

  useEffect(() => { fetch(); }, [fetch]);

  const openCreate = async () => {
    setCreateOpen(true);
    try { const r = await listDatasets(1, 100); if (r) setDatasets(r.items); } catch {}
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) { message.warning(tc('msg.pleaseInputName')); return; }
    setCreating(true);
    try {
      await createAnnotation(formData);
      message.success(tc('msg.createSuccess'));
      setCreateOpen(false);
      setFormData({ name: '', annotation_type: 0 });
      fetch();
    } catch { message.error(tc('msg.createFailed')); }
    finally { setCreating(false); }
  };

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    Modal.confirm({
      title: t('deleteTitle'), content: tc('msg.confirmDelete'), okButtonProps: { danger: true },
      onOk: async () => { await deleteAnnotation(id); message.success(tc('msg.deleted')); fetch(); },
    });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
            <TagsOutlined /> {t('title')}
          </h1>
          <p style={{ color: '#888', fontSize: 13, marginTop: 4 }}>{t('subtitle')}</p>
        </div>
        <button onClick={openCreate} style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500,
          background: '#4f6ef7', color: '#fff', border: 'none', cursor: 'pointer',
        }}>
          <PlusOutlined /> {t('newAnnotation')}
        </button>
      </div>

      <div style={{ marginBottom: 20, position: 'relative', maxWidth: 360 }}>
        <SearchOutlined style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#bbb', fontSize: 13 }} />
        <input
          style={{ width: '100%', padding: '8px 12px 8px 34px', border: '1px solid #e5e5e5', borderRadius: 8, fontSize: 13, outline: 'none' }}
          placeholder={t('searchPlaceholder')}
          value={keyword} onChange={(e) => setKeyword(e.target.value)}
        />
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
      ) : annotations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}>
          <TagsOutlined style={{ fontSize: 48, marginBottom: 12 }} />
          <p style={{ fontSize: 14 }}>{t('empty')}</p>
        </div>
      ) : (
        <div className="card-grid">
          {annotations.map((ann) => {
            const ck = AnnotationTypeColors[ann.annotation_type] || 'blue';
            const c = colorMap[ck] || colorMap.blue;
            const classes = ann.classes ? ann.classes.split(',').filter(Boolean) : [];
            return (
              <div key={ann.id}
                onClick={() => navigate(`/annotations/${ann.id}/label`)}
                style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, overflow: 'hidden', cursor: 'pointer', transition: 'box-shadow 0.2s' }}
                onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.06)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
              >
                <div style={{ height: 90, background: 'linear-gradient(135deg, #eef2ff, #e8dff5)', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                  <EditOutlined style={{ fontSize: 28, color: '#a5b4fc' }} />
                  <button onClick={(e) => handleDelete(e, ann.id)} style={{
                    position: 'absolute', top: 8, right: 8, width: 28, height: 28, borderRadius: 6,
                    background: 'rgba(255,255,255,0.8)', border: 'none', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999', fontSize: 13,
                  }}><DeleteOutlined /></button>
                </div>
                <div style={{ padding: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <span style={{ fontSize: 14, fontWeight: 600, color: '#111', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ann.name}</span>
                    <span style={{ fontSize: 11, padding: '1px 8px', background: c.bg, color: c.fg, borderRadius: 999, flexShrink: 0 }}>
                      {AnnotationTypeLabels[ann.annotation_type] ?? tc('status.unknown')}
                    </span>
                  </div>
                  {classes.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
                      {classes.slice(0, 5).map((cl, i) => (
                        <span key={i} style={{ padding: '1px 6px', background: '#f5f5f5', color: '#666', fontSize: 11, borderRadius: 4 }}>{cl.trim()}</span>
                      ))}
                      {classes.length > 5 && <span style={{ fontSize: 11, color: '#bbb' }}>+{classes.length - 5}</span>}
                    </div>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, color: '#999' }}>
                    <span>{t('classCount', { count: classes.length })}</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><ClockCircleOutlined /> {new Date(ann.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ marginTop: 16, fontSize: 13, color: '#bbb' }}>{t('totalAnnotations', { count: total })}</div>

      <Modal title={t('newAnnotation')} open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); setFormData({ name: '', annotation_type: 0 }); }} confirmLoading={creating} okText={tc('action.create')} cancelText={tc('action.cancel')}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{tc('label.name')}</label>
            <Input placeholder={t('inputName')} value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{t('annotationType')}</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {Object.entries(AnnotationTypeLabels).map(([k, v]) => (
                <button key={k} onClick={() => setFormData({ ...formData, annotation_type: Number(k) })} style={{
                  padding: '5px 14px', fontSize: 13, borderRadius: 8, cursor: 'pointer',
                  border: formData.annotation_type === Number(k) ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                  background: formData.annotation_type === Number(k) ? '#eef2ff' : '#fff',
                  color: formData.annotation_type === Number(k) ? '#4f6ef7' : '#666',
                }}>{v}</button>
              ))}
            </div>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{t('linkedDataset')}</label>
            <Select placeholder={t('selectDataset')} allowClear style={{ width: '100%' }} value={formData.dataset_id}
              onChange={(v) => setFormData({ ...formData, dataset_id: v })} options={datasets.map((ds) => ({ label: ds.name, value: ds.id }))} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{t('initialClasses')}</label>
            <Input.TextArea rows={2} placeholder={t('classesPlaceholder')} value={formData.classes}
              onChange={(e) => setFormData({ ...formData, classes: e.target.value })} />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default AnnotationListPage;
