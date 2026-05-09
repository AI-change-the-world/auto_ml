import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { message, Spin } from 'antd';
import { ArrowLeftOutlined, ReloadOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { getTask, getTaskLogs } from '../../api/task';
import { subscribeTaskStream } from '../../api/taskStream';
import type { TaskResponse, TaskLogResponse } from '../../types/task';
import { TaskStatusLabels, TaskStatusColors } from '../../types/task';
import { useTranslation } from 'react-i18next';

const statusStyles: Record<string, { bg: string; fg: string }> = {
  default: { bg: '#f5f5f5', fg: '#888' },
  processing: { bg: '#eef2ff', fg: '#4f6ef7' },
  error: { bg: '#fef2f2', fg: '#dc2626' },
  success: { bg: '#f0fdf4', fg: '#16a34a' },
};

const getStaleMinutes = (seconds?: number | null) => Math.max(1, Math.floor((seconds || 0) / 60));

const TaskDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation('task');
  const tc = useTranslation('common').t;
  const taskId = Number(id);
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [logs, setLogs] = useState<TaskLogResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [streamVersion, setStreamVersion] = useState(0);
  const logRef = useRef<HTMLDivElement>(null);

  const fetchTask = useCallback(async () => {
    try { const r = await getTask(taskId); if (r) setTask(r); } catch { message.error(tc('msg.fetchFailed')); }
  }, [taskId]);

  const fetchLogs = useCallback(async () => {
    try {
      const r = await getTaskLogs(taskId, 1, 500);
      if (r) { setLogs(r.items); setTimeout(() => { logRef.current && (logRef.current.scrollTop = logRef.current.scrollHeight); }, 50); }
    } catch { }
  }, [taskId]);

  const handleManualRefresh = useCallback(() => {
    setStreamVersion((prev) => prev + 1);
    fetchTask();
    fetchLogs();
  }, [fetchTask, fetchLogs]);

  useEffect(() => {
    (async () => { setLoading(true); await Promise.all([fetchTask(), fetchLogs()]); setLoading(false); })();
  }, [fetchTask, fetchLogs]);

  useEffect(() => {
    if (!Number.isFinite(taskId)) return;

    const stop = subscribeTaskStream({
      onEvent: (payload) => {
        if (payload.event === 'task_upsert' && payload.data.task) {
          setTask(payload.data.task);
        }
        if (payload.event === 'task_log' && payload.data.log) {
          const nextLog = payload.data.log;
          setLogs((prev) => {
            if (prev.some((item) => item.id === nextLog.id)) {
              return prev;
            }
            const next = [...prev, nextLog];
            next.sort((a, b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf());
            setTimeout(() => {
              if (logRef.current) {
                logRef.current.scrollTop = logRef.current.scrollHeight;
              }
            }, 50);
            return next;
          });
        }
      },
      onError: () => {
        fetchTask();
        fetchLogs();
      },
    }, taskId);

    return () => {
      stop();
    };
  }, [taskId, fetchTask, fetchLogs, streamVersion]);

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}><Spin size="large" /></div>;
  if (!task) return (
    <div style={{ padding: 24 }}>
      <button className="button-text" onClick={() => navigate('/tasks')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: '#666', cursor: 'pointer' }}><ArrowLeftOutlined /> {tc('action.back')}</button>
      <div style={{ textAlign: 'center', marginTop: 80, color: '#ccc' }}>{t('notExist')}</div>
    </div>
  );

  const typeLabels: Record<number, string> = { 0: t('detection'), 1: t('classification') };
  const ck = TaskStatusColors[task.status] || 'default';
  const s = statusStyles[ck] || statusStyles.default;
  const getSourceDisplayName = (source: NonNullable<TaskResponse['sources']>[number]) => (
    source.source_name?.trim()
    || t('sourceFallbackName', {
      datasetId: source.dataset_id,
      annotationId: source.annotation_id,
    })
  );
  const primarySource = task.sources?.[0];
  const primarySourceName = primarySource
    ? getSourceDisplayName(primarySource)
    : task.dataset_id != null && task.annotation_id != null
      ? t('sourceFallbackName', {
        datasetId: task.dataset_id,
        annotationId: task.annotation_id,
      })
      : '-';
  const primarySourceIds = primarySource
    ? t('sourceIdsInline', {
      datasetId: primarySource.dataset_id,
      annotationId: primarySource.annotation_id,
    })
    : task.dataset_id != null && task.annotation_id != null
      ? t('sourceIdsInline', {
        datasetId: task.dataset_id,
        annotationId: task.annotation_id,
      })
      : '-';

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }} className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={() => navigate('/tasks')} style={{ width: 32, height: 32, borderRadius: 8, border: '1px solid #eee', background: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}><ArrowLeftOutlined /></button>
          <h1 className="section-title" style={{ margin: 0 }}>{t('taskId', { id: task.id })}</h1>
          <span className="tag-text" style={{ padding: '2px 10px', borderRadius: 999, background: s.bg, color: s.fg }}>{TaskStatusLabels[task.status]}</span>
          {task.is_stale && (
            <span className="tag-text" style={{ padding: '2px 10px', borderRadius: 999, background: '#fff7ed', color: '#c2410c' }}>
              {t('staleBadge')}
            </span>
          )}
        </div>
        <button className="button-text" onClick={handleManualRefresh} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '6px 14px', border: '1px solid #e5e5e5', borderRadius: 8, background: '#fff', color: '#666', cursor: 'pointer' }}><ReloadOutlined /> {tc('action.refresh')}</button>
      </div>

      {/* Info */}
      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        {task.is_stale && (
          <div style={{ marginBottom: 16, padding: 12, background: '#fff7ed', borderRadius: 8 }}>
            <div className="info-label" style={{ color: '#c2410c', marginBottom: 2 }}>{t('staleBadge')}</div>
            <div className="body-text-sm" style={{ color: '#9a3412' }}>
              {t('staleHint', { minutes: getStaleMinutes(task.stale_seconds) })}
            </div>
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20 }}>
          {[
            { label: t('taskTypeLabel'), value: typeLabels[task.task_type] ?? task.task_type },
            {
              label: t('primarySourceLabel'),
              value: primarySourceName,
            },
            {
              label: t('sourceCountLabel'),
              value: t('sourceCount', { count: task.sources?.length ?? 0 }),
            },
            {
              label: t('primarySourceIdsLabel'),
              value: primarySourceIds,
            },
            { label: tc('label.status'), value: TaskStatusLabels[task.status] },
            { label: tc('label.createdAt'), value: dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss') },
            { label: tc('label.updatedAt'), value: dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss') },
          ].map((item, i) => (
            <div key={i}>
              <div className="info-label" style={{ marginBottom: 2 }}>{item.label}</div>
              <div className="info-value">{item.value}</div>
            </div>
          ))}
        </div>
        {(task.sources?.length ?? 0) > 0 && (
          <div style={{ marginTop: 16, padding: 12, background: '#f8fafc', borderRadius: 8 }}>
            <div className="info-label" style={{ marginBottom: 8 }}>{t('sources')}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {(task.sources || []).map((source, index) => (
                <div
                  key={source.id}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 8,
                    background: '#fff',
                    border: '1px solid #e2e8f0',
                  }}
                >
                  <div className="body-text-sm" style={{ fontWeight: 600, color: '#0f172a' }}>
                    {index + 1}. {getSourceDisplayName(source)}
                  </div>
                  <div className="caption-text" style={{ marginTop: 4, color: '#64748b' }}>
                    {t('sourceIdsInline', {
                      datasetId: source.dataset_id,
                      annotationId: source.annotation_id,
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        {task.error_message && (
          <div style={{ marginTop: 16, padding: 12, background: '#fef2f2', borderRadius: 8 }}>
            <div className="info-label" style={{ color: '#dc2626', marginBottom: 2 }}>{t('errorMessage')}</div>
            <div className="body-text-sm" style={{ color: '#991b1b' }}>{task.error_message}</div>
          </div>
        )}
        {task.result && (
          <div style={{ marginTop: 16, padding: 12, background: '#f0fdf4', borderRadius: 8 }}>
            <div className="info-label" style={{ color: '#16a34a', marginBottom: 2 }}>{t('result')}</div>
            <div className="body-text-sm" style={{ color: '#166534', fontFamily: 'monospace' }}>{task.result}</div>
          </div>
        )}
      </div>

      {/* Logs */}
      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 18px', borderBottom: '1px solid #f5f5f5' }}>
          <span className="card-title" style={{ color: '#111' }}>{t('trainLog')}</span>
          <span className="caption-text" style={{ color: '#bbb', display: 'flex', alignItems: 'center', gap: 4 }}>
            <ClockCircleOutlined /> {task.status <= 2 ? t('autoRefresh') : t('totalLogs', { count: logs.length })}
          </span>
        </div>
        <div ref={logRef} style={{
          background: '#1e1e1e', color: '#d4d4d4', padding: 16, height: 380, overflow: 'auto',
          fontFamily: "'Cascadia Code', 'Fira Code', Consolas, monospace", lineHeight: 1.7,
        }}>
          {logs.length === 0 ? <span className="code-text" style={{ color: '#555' }}>{t('noLogs')}</span>
            : logs.map((log) => (
              <div key={log.id} className="code-text">
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
