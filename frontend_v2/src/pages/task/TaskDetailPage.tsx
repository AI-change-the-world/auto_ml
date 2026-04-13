import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { message, Spin } from 'antd';
import { ArrowLeftOutlined, ReloadOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { getTask, getTaskLogs } from '../../api/task';
import type { TaskResponse, TaskLogResponse } from '../../types/task';
import { TaskStatusLabels, TaskStatusColors } from '../../types/task';
import { useTranslation } from 'react-i18next';

const statusStyles: Record<string, { bg: string; fg: string }> = {
  default: { bg: '#f5f5f5', fg: '#888' },
  processing: { bg: '#eef2ff', fg: '#4f6ef7' },
  error: { bg: '#fef2f2', fg: '#dc2626' },
  success: { bg: '#f0fdf4', fg: '#16a34a' },
};

const TaskDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation('task');
  const tc = useTranslation('common').t;
  const taskId = Number(id);
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [logs, setLogs] = useState<TaskLogResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const logRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchTask = useCallback(async () => {
    try { const r = await getTask(taskId); if (r) setTask(r); } catch { message.error(tc('msg.fetchFailed')); }
  }, [taskId]);

  const fetchLogs = useCallback(async () => {
    try {
      const r = await getTaskLogs(taskId, 1, 500);
      if (r) { setLogs(r.items); setTimeout(() => { logRef.current && (logRef.current.scrollTop = logRef.current.scrollHeight); }, 50); }
    } catch {}
  }, [taskId]);

  useEffect(() => {
    (async () => { setLoading(true); await Promise.all([fetchTask(), fetchLogs()]); setLoading(false); })();
  }, [fetchTask, fetchLogs]);

  useEffect(() => {
    if (task && (task.status === 0 || task.status === 1)) {
      timerRef.current = setInterval(() => { fetchTask(); fetchLogs(); }, 5000);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [task?.status, fetchTask, fetchLogs]);

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}><Spin size="large" /></div>;
  if (!task) return (
    <div style={{ padding: 24 }}>
      <button onClick={() => navigate('/tasks')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: 14 }}><ArrowLeftOutlined /> {tc('action.back')}</button>
      <div style={{ textAlign: 'center', marginTop: 80, color: '#ccc' }}>{t('notExist')}</div>
    </div>
  );

  const typeLabels: Record<number, string> = { 0: t('detection'), 1: t('classification'), 2: t('segmentation') };
  const ck = TaskStatusColors[task.status] || 'default';
  const s = statusStyles[ck] || statusStyles.default;

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }} className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={() => navigate('/tasks')} style={{ width: 32, height: 32, borderRadius: 8, border: '1px solid #eee', background: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}><ArrowLeftOutlined /></button>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: '#111', margin: 0 }}>{t('taskId', { id: task.id })}</h1>
          <span style={{ padding: '2px 10px', fontSize: 12, borderRadius: 999, background: s.bg, color: s.fg, fontWeight: 500 }}>{TaskStatusLabels[task.status]}</span>
        </div>
        <button onClick={() => { fetchTask(); fetchLogs(); }} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '6px 14px', border: '1px solid #e5e5e5', borderRadius: 8, fontSize: 13, background: '#fff', color: '#666', cursor: 'pointer' }}><ReloadOutlined /> {tc('action.refresh')}</button>
      </div>

      {/* Info */}
      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20 }}>
          {[
            { label: t('taskTypeLabel'), value: typeLabels[task.task_type] ?? task.task_type },
            { label: t('dataset'), value: task.dataset_id ?? '-' },
            { label: tc('nav.annotation', { ns: 'common' }), value: task.annotation_id ?? '-' },
            { label: tc('label.status'), value: TaskStatusLabels[task.status] },
            { label: tc('label.createdAt'), value: dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss') },
            { label: tc('label.updatedAt'), value: dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss') },
          ].map((item, i) => (
            <div key={i}>
              <div style={{ fontSize: 12, color: '#999', marginBottom: 2 }}>{item.label}</div>
              <div style={{ fontSize: 14, fontWeight: 500, color: '#111' }}>{item.value}</div>
            </div>
          ))}
        </div>
        {task.error_message && (
          <div style={{ marginTop: 16, padding: 12, background: '#fef2f2', borderRadius: 8 }}>
            <div style={{ fontSize: 12, color: '#dc2626', marginBottom: 2 }}>{t('errorMessage')}</div>
            <div style={{ fontSize: 13, color: '#991b1b' }}>{task.error_message}</div>
          </div>
        )}
        {task.result && (
          <div style={{ marginTop: 16, padding: 12, background: '#f0fdf4', borderRadius: 8 }}>
            <div style={{ fontSize: 12, color: '#16a34a', marginBottom: 2 }}>{t('result')}</div>
            <div style={{ fontSize: 13, color: '#166534', fontFamily: 'monospace' }}>{task.result}</div>
          </div>
        )}
      </div>

      {/* Logs */}
      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 18px', borderBottom: '1px solid #f5f5f5' }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: '#111' }}>{t('trainLog')}</span>
          <span style={{ fontSize: 12, color: '#bbb', display: 'flex', alignItems: 'center', gap: 4 }}>
            <ClockCircleOutlined /> {task.status <= 1 ? t('autoRefresh') : t('totalLogs', { count: logs.length })}
          </span>
        </div>
        <div ref={logRef} style={{
          background: '#1e1e1e', color: '#d4d4d4', padding: 16, height: 380, overflow: 'auto',
          fontFamily: "'Cascadia Code', 'Fira Code', Consolas, monospace", fontSize: 12, lineHeight: 1.7,
        }}>
          {logs.length === 0 ? <span style={{ color: '#555' }}>{t('noLogs')}</span>
          : logs.map((log) => (
            <div key={log.id}>
              <span style={{ color: '#6a9955' }}>[{dayjs(log.created_at).format('HH:mm:ss')}]</span>{' '}
              <span style={{ color: log.log_level === 'ERROR' ? '#f44747' : log.log_level === 'WARNING' ? '#cca700' : '#d4d4d4' }}>{log.content}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TaskDetailPage;
