import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Select, InputNumber, Switch, Tooltip, Collapse } from 'antd';
import { PlusOutlined, ExperimentOutlined, ReloadOutlined, ClockCircleOutlined, RightOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { listTasks, createTrainTask, getBaseModels, getTrainerStatus, deleteTask, getTrainingHistoryCandidates } from '../../api/task';
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
  TrainingOptimizerConfig,
  TaskSourceItem,
  TaskSourceResponse,
  TrainingHistoryCandidateResponse,
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
type TrainingEngine = 'ultralytics-yolo';

const DEFAULT_TRAIN_CONFIG: TrainingConfigPayload = {
  name: '',
  epoch: 100,
  size: 640,
  batch: 8,
  device: 'cpu',
  label_format: 'bbox',
  export_onnx: false,
  dataset_cache_mode: 'off',
  augmentation: {
    enabled: true,
    degrees: 0,
    translate: 0.1,
    scale: 0.5,
    shear: 0,
    perspective: 0,
    fliplr: 0.5,
    flipud: 0,
    hsv_h: 0.015,
    hsv_s: 0.7,
    hsv_v: 0.4,
    mosaic: 1,
    mixup: 0,
    copy_paste: 0,
    close_mosaic: 10,
    auto_augment: 'randaugment',
    erasing: 0.4,
  },
  optimizer_config: {
    optimizer: 'auto',
    patience: 100,
    lr0: 0.01,
    lrf: 0.01,
    momentum: 0.937,
    weight_decay: 0.0005,
    warmup_epochs: 3,
    cos_lr: false,
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

const renderParameterLabel = (label: string, description?: string) => (
  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
    <span>{label}</span>
    {description ? (
      <Tooltip title={description}>
        <InfoCircleOutlined style={{ color: '#9ca3af', fontSize: 13, cursor: 'help' }} />
      </Tooltip>
    ) : null}
  </span>
);

const resolveTrainingEngine = (_baseModel?: BaseModelResponse | null): TrainingEngine => 'ultralytics-yolo';

const formatDeviceLabel = (device: string) => {
  const normalized = device.toLowerCase();
  if (normalized === 'cpu') return 'CPU';
  if (normalized === 'cuda') return 'CUDA';
  if (normalized === 'mps') return 'MPS';
  return device.toUpperCase();
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
  const [baseModels, setBaseModels] = useState<BaseModelResponse[]>([]);
  const [trainerStatus, setTrainerStatus] = useState<TrainerStatusResponse | null>(null);
  const [historyCandidates, setHistoryCandidates] = useState<TrainingHistoryCandidateResponse[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
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
  const availableDevices = trainerStatus?.available_devices?.length ? trainerStatus.available_devices : ['cpu'];

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
    if (!availableDevices.includes(form.train_config.device)) {
      updateTrainConfig('device', availableDevices[0] || 'cpu');
    }
  }, [availableDevices, form.train_config.device]);

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
    setHistoryCandidates([]);
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
      setHistoryCandidates([]);
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
  const selectedBaseModel = availableBaseModels.find(
    (model) => (model.save_path || model.name) === form.train_config.name,
  ) || null;
  const selectedTrainingEngine = selectedBaseModel ? resolveTrainingEngine(selectedBaseModel) : null;
  const selectedResumeModel = historyCandidates.find(
    (item) => item.model_id === form.train_config.resume_model_id,
  ) || null;
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

  const updateOptimizerConfig = <K extends keyof TrainingOptimizerConfig>(
    key: K,
    value: TrainingOptimizerConfig[K],
  ) => {
    setForm((prev) => ({
      ...prev,
      train_config: {
        ...prev.train_config,
        optimizer_config: {
          ...(prev.train_config.optimizer_config || DEFAULT_TRAIN_CONFIG.optimizer_config!),
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
        resume_model_id: undefined,
        label_format: taskType === 0 ? prev.detection_mode : undefined,
      },
    }));
    setHistoryCandidates([]);
  };

  const handleDetectionModeChange = (mode: DetectionMode) => {
    setForm((prev) => ({
      ...prev,
      detection_mode: mode,
      train_config: {
        ...prev.train_config,
        name: '',
        resume_model_id: undefined,
        label_format: mode,
      },
    }));
    setHistoryCandidates([]);
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

  const fetchHistoryCandidates = useCallback(async () => {
    const readySources = form.sources.filter((source) => source.dataset_id && source.annotation_id);
    if (readySources.length === 0 || readySources.length !== form.sources.length) {
      setHistoryCandidates([]);
      return;
    }
    setHistoryLoading(true);
    try {
      const result = await getTrainingHistoryCandidates({
        task_type: form.task_type,
        sources: readySources,
        label_format: form.task_type === 0 ? form.detection_mode : undefined,
      });
      setHistoryCandidates(result || []);
      setForm((prev) => {
        const resumeModelId = prev.train_config.resume_model_id;
        if (!resumeModelId) {
          return prev;
        }
        const exists = (result || []).some((item) => item.model_id === resumeModelId);
        if (exists) {
          return prev;
        }
        return {
          ...prev,
          train_config: {
            ...prev.train_config,
            resume_model_id: undefined,
          },
        };
      });
    } catch {
      setHistoryCandidates([]);
    } finally {
      setHistoryLoading(false);
    }
  }, [form.sources, form.task_type, form.detection_mode]);

  useEffect(() => {
    if (!createOpen) {
      return;
    }
    void fetchHistoryCandidates();
  }, [createOpen, fetchHistoryCandidates]);

  const getAnnotationOptions = (datasetId?: number) => (
    annotations
      .filter((annotation) => (
        (!datasetId || annotation.dataset_id === datasetId)
        && annotation.annotation_type === getExpectedAnnotationType(form.task_type)
      ))
      .map((annotation) => ({ label: annotation.name, value: annotation.id }))
  );

  const augmentation = form.train_config.augmentation || DEFAULT_TRAIN_CONFIG.augmentation!;
  const optimizerConfig = form.train_config.optimizer_config || DEFAULT_TRAIN_CONFIG.optimizer_config!;
  const showDetectionAugmentation = form.task_type === 0 || form.task_type === 2;
  const showClassificationAugmentation = form.task_type === 1;
  const historyOptions = historyCandidates.map((item) => ({
    label: `${item.model_name} · ${dayjs(item.created_at).format('MM-DD HH:mm')}`,
    value: item.model_id,
  }));

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

      <Modal
        title={<span className="modal-title">{t('createTitle')}</span>}
        open={createOpen}
        onOk={handleCreate}
        onCancel={() => setCreateOpen(false)}
        confirmLoading={creating}
        okText={tc('action.create')}
        cancelText={tc('action.cancel')}
        width={760}
        styles={{ body: { maxHeight: '72vh', overflowY: 'auto', paddingTop: 16 } }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
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
            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
              {renderParameterLabel(t('baseModel'), t('baseModelDesc'))}
            </label>
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
          <div style={{ padding: '12px 14px', border: '1px solid #e5e7eb', borderRadius: 10, background: '#fafafa', display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                  {renderParameterLabel(t('datasetCacheMode'), t('datasetCacheModeDesc'))}
                </label>
                <Select
                  style={{ width: '100%' }}
                  value={form.train_config.dataset_cache_mode || 'off'}
                  onChange={(value) => updateTrainConfig('dataset_cache_mode', value)}
                  options={[
                    { label: t('datasetCacheOff'), value: 'off' },
                    { label: t('datasetCacheReuse'), value: 'reuse' },
                    { label: t('datasetCacheRefresh'), value: 'refresh' },
                  ]}
                />
              </div>
              <div>
                <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                  {renderParameterLabel(t('resumeTrainingModel'), t('resumeTrainingModelDesc'))}
                </label>
                <Select
                  allowClear
                  style={{ width: '100%' }}
                  loading={historyLoading}
                  placeholder={historyCandidates.length > 0 ? t('selectResumeTrainingModel') : t('resumeTrainingEmpty')}
                  value={form.train_config.resume_model_id}
                  onChange={(value) => updateTrainConfig('resume_model_id', value)}
                  options={historyOptions}
                  disabled={historyCandidates.length === 0}
                  showSearch
                  optionFilterProp="label"
                />
              </div>
            </div>
            <div className="caption-text" style={{ color: '#6b7280' }}>
              {selectedResumeModel
                ? t('resumeTrainingSelected', {
                  model: selectedResumeModel.model_name,
                  time: dayjs(selectedResumeModel.created_at).format('YYYY-MM-DD HH:mm'),
                })
                : historyCandidates.length > 0
                  ? t('resumeTrainingHint', { count: historyCandidates.length })
                  : t('resumeTrainingEmptyHint')}
            </div>
            {selectedResumeModel && (
              <div className="caption-text" style={{ color: '#9ca3af' }}>
                {t('resumeTrainingPriorityHint')}
              </div>
            )}
          </div>
          {selectedTrainingEngine ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ padding: '12px 14px', border: '1px solid #e5e7eb', borderRadius: 10, background: '#fafafa' }}>
                <div className="form-label" style={{ marginBottom: 4 }}>{t('trainingEngine')}</div>
                <div className="body-text-sm" style={{ color: '#111827', fontWeight: 500 }}>
                  {t('trainingEngineUltralytics')}
                </div>
                <div className="caption-text" style={{ color: '#6b7280', marginTop: 4 }}>
                  {t('trainingParamsReady', { engine: t('trainingEngineUltralytics') })}
                </div>
              </div>
              <Collapse
                bordered={false}
                defaultActiveKey={['basic']}
                items={[
                  {
                    key: 'basic',
                    label: <span className="form-label">{t('basicTrainingParams')}</span>,
                    children: (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                        <div>
                          <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                            {renderParameterLabel(t('epochs'), t('epochsDesc'))}
                          </label>
                          <InputNumber min={1} max={10000} value={form.train_config.epoch} onChange={(value) => updateTrainConfig('epoch', Number(value || 1))} style={{ width: '100%' }} />
                        </div>
                        <div>
                          <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                            {renderParameterLabel(t('batchSize'), t('batchSizeDesc'))}
                          </label>
                          <InputNumber min={1} max={1024} value={form.train_config.batch} onChange={(value) => updateTrainConfig('batch', Number(value || 1))} style={{ width: '100%' }} />
                        </div>
                        <div>
                          <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                            {renderParameterLabel(t('imageSize'), t('imageSizeDesc'))}
                          </label>
                          <InputNumber min={32} max={4096} step={32} value={form.train_config.size} onChange={(value) => updateTrainConfig('size', Number(value || 640))} style={{ width: '100%' }} />
                        </div>
                        <div>
                          <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                            {renderParameterLabel(t('device'), t('deviceDesc'))}
                          </label>
                          <Select
                            style={{ width: '100%' }}
                            value={form.train_config.device}
                            onChange={(value) => updateTrainConfig('device', value)}
                            options={availableDevices.map((device) => ({
                              label: formatDeviceLabel(device),
                              value: device,
                            }))}
                          />
                        </div>
                      </div>
                    ),
                  },
                  {
                    key: 'optimizer',
                    label: <span className="form-label">{t('advancedOptimization')}</span>,
                    children: (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div className="caption-text" style={{ color: '#999' }}>{t('optimizerHint')}</div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                          <div>
                            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                              {renderParameterLabel(t('optimizerName'), t('optimizerNameDesc'))}
                            </label>
                            <Select
                              style={{ width: '100%' }}
                              value={optimizerConfig.optimizer}
                              onChange={(value) => updateOptimizerConfig('optimizer', value)}
                              options={[
                                { label: 'Auto', value: 'auto' },
                                { label: 'SGD', value: 'SGD' },
                                { label: 'Adam', value: 'Adam' },
                                { label: 'AdamW', value: 'AdamW' },
                                { label: 'Adamax', value: 'Adamax' },
                                { label: 'NAdam', value: 'NAdam' },
                                { label: 'RAdam', value: 'RAdam' },
                                { label: 'RMSProp', value: 'RMSProp' },
                              ]}
                            />
                          </div>
                          <div>
                            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                              {renderParameterLabel(t('patience'), t('patienceDesc'))}
                            </label>
                            <InputNumber
                              min={0}
                              max={100000}
                              value={optimizerConfig.patience}
                              onChange={(value) => updateOptimizerConfig('patience', Number(value ?? 100))}
                              style={{ width: '100%' }}
                            />
                          </div>
                          <div>
                            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                              {renderParameterLabel(t('lr0'), t('lr0Desc'))}
                            </label>
                            <InputNumber
                              min={0.000001}
                              max={10}
                              step={0.0001}
                              value={optimizerConfig.lr0}
                              onChange={(value) => updateOptimizerConfig('lr0', Number(value ?? 0.01))}
                              style={{ width: '100%' }}
                            />
                          </div>
                          <div>
                            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                              {renderParameterLabel(t('lrf'), t('lrfDesc'))}
                            </label>
                            <InputNumber
                              min={0}
                              max={10}
                              step={0.0001}
                              value={optimizerConfig.lrf}
                              onChange={(value) => updateOptimizerConfig('lrf', Number(value ?? 0.01))}
                              style={{ width: '100%' }}
                            />
                          </div>
                          <div>
                            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                              {renderParameterLabel(t('momentum'), t('momentumDesc'))}
                            </label>
                            <InputNumber
                              min={0}
                              max={1}
                              step={0.001}
                              value={optimizerConfig.momentum}
                              onChange={(value) => updateOptimizerConfig('momentum', Number(value ?? 0.937))}
                              style={{ width: '100%' }}
                            />
                          </div>
                          <div>
                            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                              {renderParameterLabel(t('weightDecay'), t('weightDecayDesc'))}
                            </label>
                            <InputNumber
                              min={0}
                              max={1}
                              step={0.0001}
                              value={optimizerConfig.weight_decay}
                              onChange={(value) => updateOptimizerConfig('weight_decay', Number(value ?? 0.0005))}
                              style={{ width: '100%' }}
                            />
                          </div>
                          <div>
                            <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                              {renderParameterLabel(t('warmupEpochs'), t('warmupEpochsDesc'))}
                            </label>
                            <InputNumber
                              min={0}
                              max={1000}
                              step={0.5}
                              value={optimizerConfig.warmup_epochs}
                              onChange={(value) => updateOptimizerConfig('warmup_epochs', Number(value ?? 3))}
                              style={{ width: '100%' }}
                            />
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, paddingTop: 24 }}>
                            <span className="form-label">{renderParameterLabel(t('cosineLr'), t('cosineLrDesc'))}</span>
                            <Switch
                              checked={Boolean(optimizerConfig.cos_lr)}
                              onChange={(checked) => updateOptimizerConfig('cos_lr', checked)}
                            />
                          </div>
                        </div>
                      </div>
                    ),
                  },
                  {
                    key: 'augmentation',
                    label: <span className="form-label">{t('dataAugmentationSection')}</span>,
                    children: (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                          <div className="caption-text" style={{ color: '#999' }}>{t('augmentationHint')}</div>
                          <Switch
                            checked={Boolean(augmentation.enabled)}
                            onChange={(checked) => updateAugmentationConfig('enabled', checked)}
                          />
                        </div>
                        {showDetectionAugmentation && (
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationDegrees'), t('augmentationDegreesDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={180}
                                step={1}
                                disabled={!augmentation.enabled}
                                value={augmentation.degrees}
                                onChange={(value) => updateAugmentationConfig('degrees', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationTranslate'), t('augmentationTranslateDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={1}
                                step={0.01}
                                disabled={!augmentation.enabled}
                                value={augmentation.translate}
                                onChange={(value) => updateAugmentationConfig('translate', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationScale'), t('augmentationScaleDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={1}
                                step={0.01}
                                disabled={!augmentation.enabled}
                                value={augmentation.scale}
                                onChange={(value) => updateAugmentationConfig('scale', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationShear'), t('augmentationShearDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={180}
                                step={1}
                                disabled={!augmentation.enabled}
                                value={augmentation.shear}
                                onChange={(value) => updateAugmentationConfig('shear', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationPerspective'), t('augmentationPerspectiveDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={0.001}
                                step={0.0001}
                                disabled={!augmentation.enabled}
                                value={augmentation.perspective}
                                onChange={(value) => updateAugmentationConfig('perspective', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationFliplr'), t('augmentationFliplrDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={1}
                                step={0.01}
                                disabled={!augmentation.enabled}
                                value={augmentation.fliplr}
                                onChange={(value) => updateAugmentationConfig('fliplr', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationFlipud'), t('augmentationFlipudDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={1}
                                step={0.01}
                                disabled={!augmentation.enabled}
                                value={augmentation.flipud}
                                onChange={(value) => updateAugmentationConfig('flipud', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationHsvH'), t('augmentationHsvHDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={1}
                                step={0.001}
                                disabled={!augmentation.enabled}
                                value={augmentation.hsv_h}
                                onChange={(value) => updateAugmentationConfig('hsv_h', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationHsvS'), t('augmentationHsvSDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={1}
                                step={0.01}
                                disabled={!augmentation.enabled}
                                value={augmentation.hsv_s}
                                onChange={(value) => updateAugmentationConfig('hsv_s', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationHsvV'), t('augmentationHsvVDesc'))}
                              </label>
                              <InputNumber
                                min={0}
                                max={1}
                                step={0.01}
                                disabled={!augmentation.enabled}
                                value={augmentation.hsv_v}
                                onChange={(value) => updateAugmentationConfig('hsv_v', Number(value ?? 0))}
                                style={{ width: '100%' }}
                              />
                            </div>
                            <div>
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationMosaic'), t('augmentationMosaicDesc'))}
                              </label>
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
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationMixup'), t('augmentationMixupDesc'))}
                              </label>
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
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationCopyPaste'), t('augmentationCopyPasteDesc'))}
                              </label>
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
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationCloseMosaic'), t('augmentationCloseMosaicDesc'))}
                              </label>
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
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationAutoPolicy'), t('augmentationAutoPolicyDesc'))}
                              </label>
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
                              <label className="form-label" style={{ display: 'block', marginBottom: 4 }}>
                                {renderParameterLabel(t('augmentationErasing'), t('augmentationErasingDesc'))}
                              </label>
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
                    ),
                  },
                  {
                    key: 'export',
                    label: <span className="form-label">{t('exportOptions')}</span>,
                    children: (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '4px 0' }}>
                        <div>
                          <div className="form-label">{renderParameterLabel(t('exportOnnx'), t('exportOnnxDesc'))}</div>
                          <div className="caption-text" style={{ color: '#999', marginTop: 2 }}>{t('exportOnnxHint')}</div>
                        </div>
                        <Switch
                          checked={Boolean(form.train_config.export_onnx)}
                          onChange={(checked) => updateTrainConfig('export_onnx', checked)}
                        />
                      </div>
                    ),
                  },
                ]}
              />
            </div>
          ) : (
            <div style={{ padding: '16px 18px', border: '1px dashed #d1d5db', borderRadius: 10, background: '#fafafa' }}>
              <div className="form-label" style={{ marginBottom: 6 }}>{t('trainingEngine')}</div>
              <div className="body-text-sm" style={{ color: '#374151' }}>{t('trainingParamsPending')}</div>
              <div className="caption-text" style={{ color: '#9ca3af', marginTop: 4 }}>
                {t('trainingEngineDesc')}
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default TaskListPage;
