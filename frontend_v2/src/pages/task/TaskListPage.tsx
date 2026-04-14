import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Select } from 'antd';
import { PlusOutlined, ExperimentOutlined, ReloadOutlined, ClockCircleOutlined, RightOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { listTasks, createTrainTask, getBaseModels, getTrainerStatus } from '../../api/task';
import { listDatasets } from '../../api/dataset';
import { listAnnotations } from '../../api/annotation';
import type { TaskResponse, TaskCreate, BaseModelResponse, TrainerStatusResponse } from '../../types/task';
import type { Dataset } from '../../types/dataset';
import type { AnnotationProject } from '../../types/annotation';
import { TaskStatusLabels, TaskStatusColors } from '../../types/task';
import { useTranslation } from 'react-i18next';

const statusStyles: Record<string, { bg: string; fg: string }> = {
  default: { bg: '#f5f5f5', fg: '#888' },
  processing: { bg: '#eef2ff', fg: '#4f6ef7' },
  error: { bg: '#fef2f2', fg: '#dc2626' },
  success: { bg: '#f0fdf4', fg: '#16a34a' },
};

const TaskListPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation('task');
  const tc = useTranslation('common').t;
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [annotations, setAnnotations] = useState<AnnotationProject[]>([]);
  const [_bm, setBm] = useState<BaseModelResponse[]>([]);
  const [trainerStatus, setTrainerStatus] = useState<TrainerStatusResponse | null>(null);
  const [form, setForm] = useState<{ task_type: number; dataset_id?: number; annotation_id?: number }>({ task_type: 0 });

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const st = statusFilter === 'all' ? undefined : Number(statusFilter);
      const r = await listTasks(page, 20, st);
      if (r) { setTasks(r.items); setTotal(r.total); }
    } catch { message.error(tc('msg.loadFailed')); }
    finally { setLoading(false); }
  }, [page, statusFilter]);

  const fetchTrainer = useCallback(async () => {
    try {
      const r = await getTrainerStatus();
      if (r) setTrainerStatus(r);
    } catch { }
  }, []);

  useEffect(() => { fetchTasks(); fetchTrainer(); }, [fetchTasks, fetchTrainer]);

  useEffect(() => {
    const timer = setInterval(() => {
      fetchTasks();
      fetchTrainer();
    }, 5000);
    return () => clearInterval(timer);
  }, [fetchTasks, fetchTrainer]);

  const openCreate = async () => {
    setCreateOpen(true);
    try {
      const [d, a, b] = await Promise.all([listDatasets(1, 100), listAnnotations(1, 100), getBaseModels()]);
      if (d) setDatasets(d.items);
      if (a) setAnnotations(a.items);
      if (b) setBm(Array.isArray(b) ? b : []);
    } catch { }
  };

  const handleCreate = async () => {
    if (!form.dataset_id) { message.warning(t('pleaseSelectDataset')); return; }
    setCreating(true);
    try {
      const data: TaskCreate = { task_type: form.task_type, dataset_id: form.dataset_id, annotation_id: form.annotation_id };
      await createTrainTask(data);
      message.success(tc('msg.createSuccess'));
      setCreateOpen(false);
      setForm({ task_type: 0 });
      fetchTasks();
    } catch { message.error(tc('msg.createFailed')); }
    finally { setCreating(false); }
  };

  const tabs = [
    { key: 'all', label: tc('label.all') }, { key: '0', label: tc('status.queued') },
    { key: '1', label: tc('status.running') }, { key: '2', label: '后处理' }, { key: '3', label: tc('status.completed') }, { key: '4', label: tc('status.failed') },
  ];
  const typeLabels: Record<number, string> = { 0: t('detection'), 1: t('classification'), 2: t('segmentation') };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}><ExperimentOutlined /> {t('title')}</h1>
          <p style={{ color: '#888', fontSize: 13, marginTop: 4 }}>{t('subtitle')}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => { fetchTasks(); fetchTrainer(); }} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 14px', border: '1px solid #e5e5e5', borderRadius: 8, fontSize: 13, background: '#fff', color: '#666', cursor: 'pointer' }}><ReloadOutlined /> {tc('action.refresh')}</button>
          <button onClick={openCreate} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 16px', background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer' }}><PlusOutlined /> {t('createTask')}</button>
        </div>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: '14px 18px', marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#111' }}>{t('trainerStatusTitle')}</div>
          <span style={{
            padding: '2px 10px',
            borderRadius: 999,
            fontSize: 12,
            background: trainerStatus?.reachable ? '#f0fdf4' : '#fef2f2',
            color: trainerStatus?.reachable ? '#16a34a' : '#dc2626',
          }}>
            {trainerStatus?.reachable ? t('trainerReachable') : t('trainerUnreachable')}
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {[
            { label: t('trainerMq'), value: trainerStatus?.mq_connected ? t('connected') : t('disconnected') },
            { label: t('trainerMaxConcurrent'), value: trainerStatus?.max_concurrent ?? '-' },
            { label: t('trainerActiveTasks'), value: trainerStatus?.active_tasks ?? '-' },
            { label: t('trainerQueuedTasks'), value: trainerStatus?.queued_tasks ?? '-' },
          ].map((item, i) => (
            <div key={i}>
              <div style={{ fontSize: 12, color: '#999', marginBottom: 2 }}>{item.label}</div>
              <div style={{ fontSize: 14, fontWeight: 500, color: '#111' }}>{item.value}</div>
            </div>
          ))}
        </div>
        {trainerStatus?.message && (
          <div style={{ marginTop: 10, fontSize: 12, color: '#999' }}>{trainerStatus.message}</div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #eee', marginBottom: 20 }}>
        {tabs.map((t) => (
          <button key={t.key} onClick={() => { setStatusFilter(t.key); setPage(1); }} style={{
            padding: '10px 16px', fontSize: 13, fontWeight: 500, cursor: 'pointer', border: 'none', background: 'none',
            borderBottom: statusFilter === t.key ? '2px solid #4f6ef7' : '2px solid transparent',
            color: statusFilter === t.key ? '#4f6ef7' : '#888', marginBottom: -1,
          }}>{t.label}</button>
        ))}
      </div>

      {loading ? <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
        : tasks.length === 0 ? <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}><ExperimentOutlined style={{ fontSize: 48, marginBottom: 12 }} /><p>{t('empty')}</p></div>
          : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {tasks.map((task) => {
                const ck = TaskStatusColors[task.status] || 'default';
                const s = statusStyles[ck] || statusStyles.default;
                return (
                  <div key={task.id} onClick={() => navigate(`/tasks/${task.id}`)} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: '14px 18px', cursor: 'pointer', transition: 'box-shadow 0.2s',
                  }} onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)'} onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                      <div style={{ width: 36, height: 36, borderRadius: 8, background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4f6ef7', fontWeight: 600, fontSize: 13 }}>#{task.id}</div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 14, fontWeight: 500, color: '#111' }}>{typeLabels[task.task_type] ?? `${t('taskType')}${task.task_type}`} {t('training')}</span>
                          <span style={{ padding: '1px 8px', fontSize: 11, borderRadius: 999, background: s.bg, color: s.fg }}>{TaskStatusLabels[task.status] || tc('status.unknown')}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, color: '#999', marginTop: 2 }}>
                          <span>{t('datasetId', { id: task.dataset_id ?? '-' })}</span>
                          {task.annotation_id && <span>{t('annotationId', { id: task.annotation_id })}</span>}
                          <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><ClockCircleOutlined /> {dayjs(task.created_at).format('MM-DD HH:mm')}</span>
                        </div>
                      </div>
                    </div>
                    <RightOutlined style={{ color: '#ddd' }} />
                  </div>
                );
              })}
            </div>
          )}

      <div style={{ marginTop: 16, fontSize: 13, color: '#bbb' }}>{t('totalTasks', { count: total })}</div>

      <Modal title={t('createTitle')} open={createOpen} onOk={handleCreate} onCancel={() => setCreateOpen(false)} confirmLoading={creating} okText={tc('action.create')} cancelText={tc('action.cancel')}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{t('taskType')}</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {Object.entries(typeLabels).map(([k, v]) => (
                <button key={k} onClick={() => setForm({ ...form, task_type: Number(k) })} style={{
                  padding: '5px 14px', fontSize: 13, borderRadius: 8, cursor: 'pointer',
                  border: form.task_type === Number(k) ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                  background: form.task_type === Number(k) ? '#eef2ff' : '#fff',
                  color: form.task_type === Number(k) ? '#4f6ef7' : '#666',
                }}>{v}</button>
              ))}
            </div>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{t('dataset')}</label>
            <Select style={{ width: '100%' }} placeholder={t('selectDataset')} value={form.dataset_id} onChange={(v) => setForm({ ...form, dataset_id: v })} options={datasets.map((d) => ({ label: d.name, value: d.id }))} showSearch optionFilterProp="label" />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>{t('annotationOptional')}</label>
            <Select style={{ width: '100%' }} placeholder={t('selectAnnotation')} allowClear value={form.annotation_id} onChange={(v) => setForm({ ...form, annotation_id: v })} options={annotations.map((a) => ({ label: a.name, value: a.id }))} showSearch optionFilterProp="label" />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default TaskListPage;
