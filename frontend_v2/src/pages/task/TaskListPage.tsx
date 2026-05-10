import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Select, InputNumber, Switch, Divider } from 'antd';
import { PlusOutlined, ExperimentOutlined, ReloadOutlined, ClockCircleOutlined, RightOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { listTasks, createTrainTask, getBaseModels, getTrainerStatus, deleteTask } from '../../api/task';
import { subscribeTaskStream } from '../../api/taskStream';
import { listDatasets } from '../../api/dataset';
import { listAnnotations } from '../../api/annotation';
import type {
  TaskResponse,
  TaskCreate,
  BaseModelResponse,
  TrainerStatusResponse,
  TaskStreamEnvelope,
  TrainingConfigPayload,
  TrainingAugmentationConfig,
  TaskSourceItem,
  TaskSourceResponse,
} from '../../types/task';
import type { Dataset } from '../../types/dataset';
import { AnnotationType, type AnnotationProject } from '../../types/annotation';
import { TaskStatus, TaskStatusLabels, TaskStatusColors } from '../../types/task';
import { useTranslation } from 'react-i18next';
import { emitTasksChanged } from '../../utils/projectEvents';
import { getTaskDeleteConfirmEnabled } from '../../utils/localSettings';

const statusStyles: Record<string, { bg: string; fg: string }> = {
  default: { bg: '#f5f5f5', fg: '#888' },
  processing: { bg: '#eef2ff', fg: '#4f6ef7' },
  error: { bg: '#fef2f2', fg: '#dc2626' },
  success: { bg: '#f0fdf4', fg: '#16a34a' },
};

type DetectionMode = 'bbox' | 'obb';

const DEFAULT_TRAIN_CONFIG: TrainingConfigPayload = {
  name: '',
  epoch: 100,
  size: 640,
  batch: 8,
  device: 'cpu',
  label_format: 'bbox',
  export_onnx: false,
  augmentation: {
    enabled: true,
    mosaic: 1,
    mixup: 0,
    copy_paste: 0,
    close_mosaic: 10,
    auto_augment: 'randaugment',
    erasing: 0.4,
  },
};

const getStaleMinutes = (seconds?: number | null) => Math.max(1, Math.floor((seconds || 0) / 60));

const getExpectedAnnotationType = (taskType: number) => (
  taskType === 1
    ? AnnotationType.Classification
    : taskType === 2
      ? AnnotationType.Segmentation
      : taskType === 3
        ? AnnotationType.Pose
        : AnnotationType.Detection
);

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
  const [baseModels, setBaseModels] = useState<BaseModelResponse[]>([]);
  const [trainerStatus, setTrainerStatus] = useState<TrainerStatusResponse | null>(null);
  const [form, setForm] = useState<{
    task_type: number;
    sources: TaskSourceItem[];
    detection_mode: DetectionMode;
    train_config: TrainingConfigPayload;
  }>({
    task_type: 0,
    sources: [{ dataset_id: 0, annotation_id: 0 }],
    detection_mode: 'bbox',
    train_config: DEFAULT_TRAIN_CONFIG,
  });
  const [streamVersion, setStreamVersion] = useState(0);

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

  const resetStream = useCallback(() => {
    setStreamVersion((prev) => prev + 1);
  }, []);

  const handleManualRefresh = useCallback(() => {
    resetStream();
    fetchTasks();
    fetchTrainer();
  }, [fetchTasks, fetchTrainer, resetStream]);

  useEffect(() => { fetchTasks(); fetchTrainer(); }, [fetchTasks, fetchTrainer]);

  useEffect(() => {
    let refreshTimer: ReturnType<typeof setTimeout> | null = null;

    const scheduleRefresh = () => {
      if (refreshTimer) return;
      refreshTimer = setTimeout(() => {
        refreshTimer = null;
        fetchTasks();
      }, 300);
    };

    const stop = subscribeTaskStream({
      onEvent: (payload: TaskStreamEnvelope) => {
        if (payload.event === 'trainer_status' && payload.data.trainer_status) {
          setTrainerStatus(payload.data.trainer_status);
          return;
        }

        if (payload.event === 'task_upsert' && payload.data.task) {
          const nextTask = payload.data.task;
          setTasks((prev) => {
            const matchedStatus = statusFilter === 'all' || Number(statusFilter) === nextTask.status;
            const index = prev.findIndex((item) => item.id === nextTask.id);

            if (!matchedStatus) {
              if (index === -1) return prev;
              return prev.filter((item) => item.id !== nextTask.id);
            }

            if (index === -1) {
              scheduleRefresh();
              return prev;
            }

            const next = [...prev];
            next[index] = nextTask;
            next.sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf());
            return next;
          });

          if (nextTask.status === TaskStatus.Pending) {
            scheduleRefresh();
          }
        }
      },
      onError: () => {
        scheduleRefresh();
        fetchTrainer();
      },
    });

    return () => {
      if (refreshTimer) clearTimeout(refreshTimer);
      stop();
    };
  }, [fetchTasks, fetchTrainer, statusFilter, streamVersion]);

  const openCreate = async () => {
    setCreateOpen(true);
    try {
      const [d, a, b] = await Promise.all([listDatasets(1, 100), listAnnotations(1, 100), getBaseModels()]);
      if (d) setDatasets(d.items);
      if (a) setAnnotations(a.items);
      if (b) setBaseModels(Array.isArray(b) ? b : []);
    } catch { }
  };

  const handleCreate = async () => {
    if (form.sources.length === 0) { message.warning(t('pleaseAddSource')); return; }
    if (form.sources.some((source) => !source.dataset_id)) { message.warning(t('pleaseSelectDataset')); return; }
    if (form.sources.some((source) => !source.annotation_id)) { message.warning(t('pleaseSelectAnnotation')); return; }
    if (!form.train_config.name) { message.warning(t('pleaseSelectBaseModel')); return; }
    setCreating(true);
    try {
      const trainConfig: TrainingConfigPayload = {
        ...form.train_config,
        label_format: form.task_type === 0 ? form.detection_mode : undefined,
      };
      const [firstSource] = form.sources;
      const data: TaskCreate = {
        task_type: form.task_type,
        dataset_id: firstSource?.dataset_id,
        annotation_id: firstSource?.annotation_id,
        sources: form.sources,
        config: JSON.stringify(trainConfig),
      };
      await createTrainTask(data);
      message.success(tc('msg.createSuccess'));
      emitTasksChanged();
      setCreateOpen(false);
      setForm({
        task_type: 0,
        sources: [{ dataset_id: 0, annotation_id: 0 }],
        detection_mode: 'bbox',
        train_config: DEFAULT_TRAIN_CONFIG,
      });
      fetchTasks();
    } catch { message.error(tc('msg.createFailed')); }
    finally { setCreating(false); }
  };

  const handleDeleteTask = (event: React.MouseEvent, taskId: number) => {
    event.stopPropagation();
    const onDelete = async () => {
      await deleteTask(taskId);
      emitTasksChanged();
      message.success(tc('msg.deleted'));
      fetchTasks();
    };
    if (!getTaskDeleteConfirmEnabled()) {
      void onDelete();
      return;
    }
    Modal.confirm({
      title: t('deleteTitle'),
      content: tc('msg.confirmDelete'),
      okButtonProps: { danger: true },
      onOk: onDelete,
    });
  };

  const tabs = [
    { key: 'all', label: tc('label.all') }, { key: '0', label: tc('status.queued') },
    { key: '1', label: tc('status.running') }, { key: '2', label: '后处理' }, { key: '3', label: tc('status.completed') }, { key: '4', label: tc('status.failed') },
  ];
  const typeLabels: Record<number, string> = {
    0: t('detection'),
    1: t('classification'),
    2: t('segmentation'),
    3: t('pose'),
  };
  const currentAnnotation = annotations.find((item) => item.id === form.sources[0]?.annotation_id);
  const annotationTypeHint = currentAnnotation?.annotation_type === 0
    ? t('detection')
    : currentAnnotation?.annotation_type === 1
      ? t('classification')
      : currentAnnotation?.annotation_type === 2
        ? t('segmentationUnsupported')
        : undefined;
  const availableBaseModels = baseModels.filter((model) => {
    if (form.task_type === 1) {
      return model.model_type === 'classification';
    }
    if (form.task_type === 2) {
      return model.model_type === 'segmentation';
    }
    if (form.task_type === 3) {
      return model.model_type === 'pose';
    }
    return form.detection_mode === 'obb'
      ? model.model_type === 'detection_obb'
      : model.model_type === 'detection';
  });
  const getSourceDisplayName = useCallback((source: TaskSourceResponse) => (
    source.source_name?.trim()
    || t('sourceFallbackName', {
      datasetId: source.dataset_id,
      annotationId: source.annotation_id,
    })
  ), [t]);
  const getSourceSummary = useCallback((task: TaskResponse) => {
    const sources = task.sources || [];
    if (sources.length === 0) {
      if (task.dataset_id != null && task.annotation_id != null) {
        return t('sourceFallbackName', {
          datasetId: task.dataset_id,
          annotationId: task.annotation_id,
        });
      }
      return '-';
    }

    const [first] = sources;
    const firstName = getSourceDisplayName(first);
    if (sources.length === 1) {
      return firstName;
    }
    return t('sourceSummaryMore', {
      first: firstName,
      remaining: sources.length - 1,
    });
  }, [getSourceDisplayName, t]);
  const getSourceTitle = useCallback((task: TaskResponse) => {
    const sources = task.sources || [];
    if (sources.length === 0) {
      return getSourceSummary(task);
    }
    return sources.map((source, index) => (
      `${index + 1}. ${getSourceDisplayName(source)}`
    )).join('\n');
  }, [getSourceDisplayName, getSourceSummary]);

  const updateTrainConfig = <K extends keyof TrainingConfigPayload>(key: K, value: TrainingConfigPayload[K]) => {
    setForm((prev) => ({
      ...prev,
      train_config: {
        ...prev.train_config,
        [key]: value,
      },
    }));
  };

  const updateAugmentationConfig = <K extends keyof TrainingAugmentationConfig>(
    key: K,
    value: TrainingAugmentationConfig[K],
  ) => {
    setForm((prev) => ({
      ...prev,
      train_config: {
        ...prev.train_config,
        augmentation: {
          ...(prev.train_config.augmentation || DEFAULT_TRAIN_CONFIG.augmentation!),
          [key]: value,
        },
      },
    }));
  };

  const handleTaskTypeChange = (taskType: number) => {
    setForm((prev) => ({
      ...prev,
      task_type: taskType,
      sources: prev.sources.map((source) => ({ ...source, annotation_id: 0 })),
      train_config: {
        ...prev.train_config,
        name: '',
        label_format: taskType === 0 ? prev.detection_mode : undefined,
      },
    }));
  };

  const handleDetectionModeChange = (mode: DetectionMode) => {
    setForm((prev) => ({
      ...prev,
      detection_mode: mode,
      train_config: {
        ...prev.train_config,
        name: '',
        label_format: mode,
      },
    }));
  };

  const addSource = () => {
    setForm((prev) => ({
      ...prev,
      sources: [...prev.sources, { dataset_id: 0, annotation_id: 0 }],
    }));
  };

  const removeSource = (index: number) => {
    setForm((prev) => ({
      ...prev,
      sources: prev.sources.length === 1
        ? [{ dataset_id: 0, annotation_id: 0 }]
        : prev.sources.filter((_, idx) => idx !== index),
    }));
  };

  const updateSource = (index: number, key: keyof TaskSourceItem, value: number) => {
    setForm((prev) => ({
      ...prev,
      sources: prev.sources.map((source, idx) => (
        idx === index
          ? {
            ...source,
            [key]: value,
            ...(key === 'dataset_id' ? { annotation_id: 0 } : {}),
          }
          : source
      )),
    }));
  };

  const getAnnotationOptions = (datasetId?: number) => (
    annotations
      .filter((annotation) => (
        (!datasetId || annotation.dataset_id === datasetId)
        && annotation.annotation_type === getExpectedAnnotationType(form.task_type)
      ))
      .map((annotation) => ({ label: annotation.name, value: annotation.id }))
  );

  const augmentation = form.train_config.augmentation || DEFAULT_TRAIN_CONFIG.augmentation!;
  const showDetectionAugmentation = form.task_type === 0 || form.task_type === 2;
  const showClassificationAugmentation = form.task_type === 1;

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon">
            <ExperimentOutlined />
          </div>
          <div>
            <h1 className="page-title">{t('title')}</h1>
            <p className="page-subtitle">{t('subtitle')}</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="button-text" onClick={handleManualRefresh} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 14px', border: '1px solid #e5e5e5', borderRadius: 8, background: '#fff', color: '#666', cursor: 'pointer' }}><ReloadOutlined /> {tc('action.refresh')}</button>
          <button className="button-text" onClick={openCreate} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 16px', background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer' }}><PlusOutlined /> {t('createTask')}</button>
        </div>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: '14px 18px', marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div className="card-title">{t('trainerStatusTitle')}</div>
          <span style={{
            padding: '2px 10px',
            borderRadius: 999,
            background: trainerStatus?.reachable ? '#f0fdf4' : '#fef2f2',
            color: trainerStatus?.reachable ? '#16a34a' : '#dc2626',
          }} className="tag-text">
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
              <div className="info-label" style={{ marginBottom: 2 }}>{item.label}</div>
              <div className="info-value">{item.value}</div>
            </div>
          ))}
        </div>
        {trainerStatus?.message && (
          <div className="caption-text" style={{ marginTop: 10, color: '#999' }}>{trainerStatus.message}</div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #eee', marginBottom: 20 }}>
        {tabs.map((t) => (
          <button key={t.key} onClick={() => { setStatusFilter(t.key); setPage(1); }} style={{
            padding: '10px 16px', cursor: 'pointer', border: 'none', background: 'none',
            borderBottom: statusFilter === t.key ? '2px solid #4f6ef7' : '2px solid transparent',
            color: statusFilter === t.key ? '#4f6ef7' : '#888', marginBottom: -1,
          }} className="button-text">{t.label}</button>
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
                      <div className="body-text-sm" style={{ width: 36, height: 36, borderRadius: 8, background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4f6ef7', fontWeight: 600 }}>#{task.id}</div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span className="body-text" style={{ fontWeight: 500, color: '#111' }}>{typeLabels[task.task_type] ?? `${t('taskType')}${task.task_type}`} {t('training')}</span>
                          <span className="tag-text" style={{ padding: '1px 8px', borderRadius: 999, background: s.bg, color: s.fg }}>{TaskStatusLabels[task.status] || tc('status.unknown')}</span>
                          {task.is_stale && (
                            <span className="tag-text" style={{ padding: '1px 8px', borderRadius: 999, background: '#fff7ed', color: '#c2410c' }}>
                              {t('staleBadge')}
                            </span>
                          )}
                        </div>
                        <div className="caption-text" style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#999', marginTop: 2 }}>
                          <span
                            title={getSourceTitle(task)}
                            style={{
                              maxWidth: 520,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              color: '#4b5563',
                            }}
                          >
                            {t('sources')}: {getSourceSummary(task)}
                          </span>
                          <span>{t('sourceCount', { count: task.sources?.length ?? 0 })}</span>
                          <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><ClockCircleOutlined /> {dayjs(task.created_at).format('MM-DD HH:mm')}</span>
                          {task.is_stale && (
                            <span style={{ color: '#c2410c' }}>
                              {t('staleSeconds', { minutes: getStaleMinutes(task.stale_seconds) })}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <button
                        onClick={(event) => handleDeleteTask(event, task.id)}
                        style={{
                          width: 30,
                          height: 30,
                          borderRadius: 8,
                          border: '1px solid #eee',
                          background: '#fff',
                          color: '#999',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                        title={t('deleteTask')}
                      >
                        <DeleteOutlined />
                      </button>
                      <RightOutlined style={{ color: '#ddd' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

      <div className="body-text-sm" style={{ marginTop: 16, color: '#bbb', textAlign: 'center' }}>{t('totalTasks', { count: total })}</div>

      <Modal title={<span className="modal-title">{t('createTitle')}</span>} open={createOpen} onOk={handleCreate} onCancel={() => setCreateOpen(false)} confirmLoading={creating} okText={tc('action.create')} cancelText={tc('action.cancel')}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
          <div>
            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('taskType')}</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {Object.entries(typeLabels).map(([k, v]) => (
                <button key={k} className="button-text" onClick={() => handleTaskTypeChange(Number(k))} style={{
                  padding: '5px 14px', borderRadius: 8, cursor: 'pointer',
                  border: form.task_type === Number(k) ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                  background: form.task_type === Number(k) ? '#eef2ff' : '#fff',
                  color: form.task_type === Number(k) ? '#4f6ef7' : '#666',
                }} disabled={Number(k) === 3}>{Number(k) === 3 ? `${v} (${t('comingSoon')})` : v}</button>
              ))}
            </div>
          </div>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label className="form-label" style={{ display: 'block' }}>{t('sources')}</label>
              <button
                className="button-text"
                type="button"
                onClick={addSource}
                style={{
                  padding: '4px 10px',
                  borderRadius: 8,
                  cursor: 'pointer',
                  border: '1px solid #e5e5e5',
                  background: '#fff',
                  color: '#666',
                }}
              >
                <PlusOutlined /> {t('addSource')}
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {form.sources.map((source, index) => (
                <div key={`source-${index}`} style={{ border: '1px solid #eee', borderRadius: 10, padding: 12, display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8, alignItems: 'end' }}>
                  <div>
                    <label className="caption-text" style={{ display: 'block', color: '#777', marginBottom: 4 }}>{t('dataset')}</label>
                    <Select
                      style={{ width: '100%' }}
                      placeholder={t('selectDataset')}
                      value={source.dataset_id || undefined}
                      onChange={(value) => updateSource(index, 'dataset_id', value)}
                      options={datasets.map((d) => ({ label: d.name, value: d.id }))}
                      showSearch
                      optionFilterProp="label"
                    />
                  </div>
                  <div>
                    <label className="caption-text" style={{ display: 'block', color: '#777', marginBottom: 4 }}>{t('annotationOptional')}</label>
                    <Select
                      style={{ width: '100%' }}
                      placeholder={t('selectAnnotation')}
                      value={source.annotation_id || undefined}
                      onChange={(value) => updateSource(index, 'annotation_id', value)}
                      options={getAnnotationOptions(source.dataset_id)}
                      showSearch
                      optionFilterProp="label"
                    />
                  </div>
                  <button
                    className="button-text"
                    type="button"
                    onClick={() => removeSource(index)}
                    style={{
                      height: 32,
                      padding: '0 10px',
                      borderRadius: 8,
                      cursor: 'pointer',
                      border: '1px solid #f0f0f0',
                      background: '#fff',
                      color: '#999',
                    }}
                  >
                    {t('removeSource')}
                  </button>
                </div>
              ))}
            </div>
          </div>
          {form.task_type === 0 && (
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('detectionMode')}</label>
              <div style={{ display: 'flex', gap: 8 }}>
                {[
                  { key: 'bbox', label: t('bboxDetection') },
                  { key: 'obb', label: t('obbDetection') },
                ].map((item) => (
                  <button key={item.key} className="button-text" onClick={() => handleDetectionModeChange(item.key as DetectionMode)} style={{
                    padding: '5px 14px', borderRadius: 8, cursor: 'pointer',
                    border: form.detection_mode === item.key ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                    background: form.detection_mode === item.key ? '#eef2ff' : '#fff',
                    color: form.detection_mode === item.key ? '#4f6ef7' : '#666',
                  }}>{item.label}</button>
                ))}
              </div>
              {annotationTypeHint && (
                <div className="caption-text" style={{ marginTop: 6, color: '#999' }}>
                  {t('annotationTypeHint', { type: annotationTypeHint })}
                </div>
              )}
            </div>
          )}
          {form.task_type === 3 && (
            <div className="caption-text" style={{ color: '#999' }}>{t('posePlaceholder')}</div>
          )}
          <div>
            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('baseModel')}</label>
            <Select
              style={{ width: '100%' }}
              placeholder={t('selectBaseModel')}
              value={form.train_config.name || undefined}
              onChange={(value) => updateTrainConfig('name', value)}
              options={availableBaseModels.map((model) => ({
                label: `${model.name}${model.description ? ` · ${model.description}` : ''}`,
                value: model.save_path || model.name,
              }))}
              showSearch
              optionFilterProp="label"
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('epochs')}</label>
              <InputNumber min={1} max={10000} value={form.train_config.epoch} onChange={(value) => updateTrainConfig('epoch', Number(value || 1))} style={{ width: '100%' }} />
            </div>
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('batchSize')}</label>
              <InputNumber min={1} max={1024} value={form.train_config.batch} onChange={(value) => updateTrainConfig('batch', Number(value || 1))} style={{ width: '100%' }} />
            </div>
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('imageSize')}</label>
              <InputNumber min={32} max={4096} step={32} value={form.train_config.size} onChange={(value) => updateTrainConfig('size', Number(value || 640))} style={{ width: '100%' }} />
            </div>
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('device')}</label>
              <Select
                style={{ width: '100%' }}
                value={form.train_config.device}
                onChange={(value) => updateTrainConfig('device', value)}
                options={[
                  { label: 'CPU', value: 'cpu' },
                  { label: 'CUDA', value: 'cuda' },
                ]}
              />
            </div>
          </div>
          <Divider style={{ margin: '4px 0 0' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <div>
                <div className="form-label">{t('augmentationTitle')}</div>
                <div className="caption-text" style={{ color: '#999', marginTop: 2 }}>{t('augmentationHint')}</div>
              </div>
              <Switch
                checked={Boolean(augmentation.enabled)}
                onChange={(checked) => updateAugmentationConfig('enabled', checked)}
              />
            </div>
            {showDetectionAugmentation && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                <div>
                  <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('augmentationMosaic')}</label>
                  <InputNumber
                    min={0}
                    max={1}
                    step={0.1}
                    disabled={!augmentation.enabled}
                    value={augmentation.mosaic}
                    onChange={(value) => updateAugmentationConfig('mosaic', Number(value ?? 0))}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('augmentationMixup')}</label>
                  <InputNumber
                    min={0}
                    max={1}
                    step={0.1}
                    disabled={!augmentation.enabled}
                    value={augmentation.mixup}
                    onChange={(value) => updateAugmentationConfig('mixup', Number(value ?? 0))}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('augmentationCopyPaste')}</label>
                  <InputNumber
                    min={0}
                    max={1}
                    step={0.1}
                    disabled={!augmentation.enabled}
                    value={augmentation.copy_paste}
                    onChange={(value) => updateAugmentationConfig('copy_paste', Number(value ?? 0))}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('augmentationCloseMosaic')}</label>
                  <InputNumber
                    min={0}
                    max={10000}
                    disabled={!augmentation.enabled}
                    value={augmentation.close_mosaic}
                    onChange={(value) => updateAugmentationConfig('close_mosaic', Number(value ?? 0))}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>
            )}
            {showClassificationAugmentation && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                <div>
                  <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('augmentationAutoPolicy')}</label>
                  <Select
                    style={{ width: '100%' }}
                    disabled={!augmentation.enabled}
                    value={augmentation.auto_augment}
                    onChange={(value) => updateAugmentationConfig('auto_augment', value)}
                    options={[
                      { label: 'RandAugment', value: 'randaugment' },
                      { label: 'AutoAugment', value: 'autoaugment' },
                      { label: 'AugMix', value: 'augmix' },
                      { label: t('augmentationDisabledPolicy'), value: 'none' },
                    ]}
                  />
                </div>
                <div>
                  <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>{t('augmentationErasing')}</label>
                  <InputNumber
                    min={0}
                    max={1}
                    step={0.1}
                    disabled={!augmentation.enabled}
                    value={augmentation.erasing}
                    onChange={(value) => updateAugmentationConfig('erasing', Number(value ?? 0))}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '10px 12px', border: '1px solid #eee', borderRadius: 8 }}>
            <div>
              <div className="form-label">{t('exportOnnx')}</div>
              <div className="caption-text" style={{ color: '#999', marginTop: 2 }}>{t('exportOnnxHint')}</div>
            </div>
            <Switch
              checked={Boolean(form.train_config.export_onnx)}
              onChange={(checked) => updateTrainConfig('export_onnx', checked)}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default TaskListPage;
