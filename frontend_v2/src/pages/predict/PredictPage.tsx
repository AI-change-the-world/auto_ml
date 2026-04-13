import React, { useEffect, useState, useCallback } from 'react';
import { message, Spin, Modal, Input, Select } from 'antd';
import { AimOutlined, ReloadOutlined, PlusOutlined, PictureOutlined, VideoCameraOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { predictImage, listPredictTasks } from '../../api/predict';
import { listModels } from '../../api/deploy';
import type { PredictTaskResponse } from '../../types/predict';
import type { AvailableModelResponse } from '../../types/deploy';
import { PredictStatusLabels, PredictStatusColors } from '../../types/predict';
import { useTranslation } from 'react-i18next';

const statusStyles: Record<string, { bg: string; fg: string }> = {
    default: { bg: '#f5f5f5', fg: '#888' },
    processing: { bg: '#eef2ff', fg: '#4f6ef7' },
    error: { bg: '#fef2f2', fg: '#dc2626' },
    success: { bg: '#f0fdf4', fg: '#16a34a' },
};

const PredictPage: React.FC = () => {
    const { t } = useTranslation('predict');
    const tc = useTranslation('common').t;
    const [tasks, setTasks] = useState<PredictTaskResponse[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [createOpen, setCreateOpen] = useState(false);
    const [creating, setCreating] = useState(false);
    const [models, setModels] = useState<AvailableModelResponse[]>([]);
    const [form, setForm] = useState<{ source: string; model_id?: number; task_type: string }>({
        source: '',
        task_type: 'image',
    });

    const fetchTasks = useCallback(async () => {
        setLoading(true);
        try {
            const r = await listPredictTasks(1, 20);
            if (r) { setTasks(r.items); setTotal(r.total); }
        } catch { message.error(tc('msg.loadFailed')); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { fetchTasks(); }, [fetchTasks]);

    const openCreate = async () => {
        setCreateOpen(true);
        try {
            const r = await listModels(1, 100, true);
            if (r) setModels(r.items);
        } catch { }
    };

    const handleCreate = async () => {
        if (!form.source) { message.warning(t('pleaseInputSource')); return; }
        if (!form.model_id) { message.warning(t('pleaseSelectModel')); return; }
        setCreating(true);
        try {
            await predictImage({ source: form.source, model_id: form.model_id, task_type: form.task_type });
            message.success(t('predictSubmitted'));
            setCreateOpen(false);
            setForm({ source: '', task_type: 'image' });
            fetchTasks();
        } catch { message.error(tc('msg.submitFailed')); }
        finally { setCreating(false); }
    };

    return (
        <div className="page-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div>
                    <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
                        <AimOutlined /> {t('title')}
                    </h1>
                    <p style={{ color: '#888', fontSize: 13, marginTop: 4 }}>{t('subtitle')}</p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={fetchTasks} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 14px', border: '1px solid #e5e5e5', borderRadius: 8, fontSize: 13, background: '#fff', color: '#666', cursor: 'pointer' }}>
                        <ReloadOutlined /> {tc('action.refresh')}
                    </button>
                    <button onClick={openCreate} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 16px', background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
                        <PlusOutlined /> {t('newPredict')}
                    </button>
                </div>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
            ) : tasks.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}>
                    <AimOutlined style={{ fontSize: 48, marginBottom: 12 }} />
                    <p>{t('empty')}</p>
                    <p style={{ fontSize: 13 }}>{t('emptyHint')}</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {tasks.map((task) => {
                        const ck = PredictStatusColors[task.status] || 'default';
                        const s = statusStyles[ck] || statusStyles.default;
                        return (
                            <div key={task.id} style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: '14px 18px',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                                    <div style={{ width: 36, height: 36, borderRadius: 8, background: '#fff7ed', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
                                        {task.task_type === 'video' ? <VideoCameraOutlined /> : <PictureOutlined />}
                                    </div>
                                    <div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <span style={{ fontSize: 14, fontWeight: 500, color: '#111' }}>
                                                {task.task_type === 'video' ? t('videoPredict') : t('imagePredict')} #{task.id}
                                            </span>
                                            <span style={{ padding: '1px 8px', fontSize: 11, borderRadius: 999, background: s.bg, color: s.fg }}>
                                                {PredictStatusLabels[task.status] || tc('status.unknown')}
                                            </span>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, color: '#999', marginTop: 2 }}>
                                            {task.model_id && <span>{t('modelId', { id: task.model_id })}</span>}
                                            <span>{dayjs(task.created_at).format('MM-DD HH:mm')}</span>
                                        </div>
                                    </div>
                                </div>
                                {task.result && (
                                    <span style={{ fontSize: 12, color: '#16a34a', background: '#f0fdf4', padding: '2px 10px', borderRadius: 6 }}>
                                        {tc('status.hasResult')}
                                    </span>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            <div style={{ marginTop: 16, fontSize: 13, color: '#bbb' }}>{t('totalTasks', { count: total })}</div>

            <Modal title={t('createTitle')} open={createOpen} onOk={handleCreate} onCancel={() => setCreateOpen(false)} confirmLoading={creating} okText={tc('action.submit')} cancelText={tc('action.cancel')}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
                    <div>
                        <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{t('taskType')}</label>
                        <div style={{ display: 'flex', gap: 8 }}>
                            {[{ key: 'image', label: t('image'), icon: <PictureOutlined /> }, { key: 'video', label: t('video'), icon: <VideoCameraOutlined /> }].map((tt) => (
                                <button key={tt.key} onClick={() => setForm({ ...form, task_type: tt.key })} style={{
                                    display: 'inline-flex', alignItems: 'center', gap: 4, padding: '5px 14px', fontSize: 13, borderRadius: 8, cursor: 'pointer',
                                    border: form.task_type === tt.key ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                                    background: form.task_type === tt.key ? '#eef2ff' : '#fff',
                                    color: form.task_type === tt.key ? '#4f6ef7' : '#666',
                                }}>{tt.icon} {tt.label}</button>
                            ))}
                        </div>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{t('dataSource')}</label>
                        <Input placeholder={t('dataSourcePlaceholder')} value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{t('selectModel')}</label>
                        <Select style={{ width: '100%' }} placeholder={t('selectDeployedModel')} value={form.model_id} onChange={(v) => setForm({ ...form, model_id: v })}
                            options={models.map((m) => ({ label: m.name || `Model #${m.id}`, value: m.id }))} showSearch optionFilterProp="label" />
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default PredictPage;
