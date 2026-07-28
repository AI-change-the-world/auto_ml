import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import {
  Alert,
  Button,
  Divider,
  Empty,
  Form,
  Input,
  InputNumber,
  Progress,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { getDataset } from '../../api/dataset';
import { listAnnotations } from '../../api/annotation';
import {
  cancelBatchAnnotationRun,
  createBatchAnnotationRun,
  getBatchAnnotationRun,
  getBatchAnnotationRunEvents,
  listBatchAnnotationRuns,
  listBatchAnnotationScripts,
} from '../../api/batchAnnotation';
import type {
  AiPipelineBatchRun,
  AiPipelineBatchRunEvent,
  AiPipelineBatchScript,
  AnnotationProject,
  Dataset,
} from '../../types';

const { Text } = Typography;

interface BatchFormValues {
  annotation_id?: number;
  script_key?: string;
  selection_mode: 'all' | 'unannotated';
  overwrite_policy: 'skip_existing' | 'overwrite_draft' | 'overwrite_all';
  batch_size: number;
  script_params: Record<string, unknown>;
}

const activeStatuses = new Set(['queued', 'running']);

const statusTag = (status: string) => {
  const colorMap: Record<string, string> = {
    queued: 'default',
    running: 'processing',
    succeeded: 'success',
    failed: 'error',
    canceled: 'warning',
  };
  const labelMap: Record<string, string> = {
    queued: '等待执行',
    running: '执行中',
    succeeded: '已完成',
    failed: '失败',
    canceled: '已取消',
  };
  return <Tag color={colorMap[status] ?? 'default'}>{labelMap[status] ?? status}</Tag>;
};

const formatTime = (value?: string | null) => value ? new Date(value).toLocaleString() : '-';

const getAnnotationClassNames = (raw?: string | null) => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((item) => {
      if (typeof item === 'string') return item;
      if (item && typeof item === 'object' && 'name' in item) return String(item.name);
      return String(item);
    }).filter(Boolean);
  } catch {
    return [];
  }
};

const toEventText = (event: AiPipelineBatchRunEvent) => {
  if (typeof event.event_payload === 'string') return event.event_payload;
  if (event.event_payload && typeof event.event_payload === 'object') {
    const payload = event.event_payload as Record<string, unknown>;
    return String(payload.message ?? payload.error ?? payload.chunk_key ?? event.event_type);
  }
  return event.event_type;
};

const BatchAnnotationPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const datasetId = Number(id);
  const [form] = Form.useForm<BatchFormValues>();
  const [loading, setLoading] = React.useState(true);
  const [submitting, setSubmitting] = React.useState(false);
  const [dataset, setDataset] = React.useState<Dataset | null>(null);
  const [annotations, setAnnotations] = React.useState<AnnotationProject[]>([]);
  const [scripts, setScripts] = React.useState<AiPipelineBatchScript[]>([]);
  const [runs, setRuns] = React.useState<AiPipelineBatchRun[]>([]);
  const [activeRun, setActiveRun] = React.useState<AiPipelineBatchRun | null>(null);
  const [events, setEvents] = React.useState<AiPipelineBatchRunEvent[]>([]);
  const lastEventIdRef = React.useRef(0);

  const selectedAnnotationId = Form.useWatch('annotation_id', form);
  const selectedScriptKey = Form.useWatch('script_key', form);
  const selectedAnnotation = annotations.find((item) => item.id === selectedAnnotationId);
  const selectedScript = scripts.find((item) => item.key === selectedScriptKey);
  const annotationClassNames = getAnnotationClassNames(selectedAnnotation?.classes);
  const compatibleScripts = scripts.filter((script) => {
    if (!dataset || !selectedAnnotation) return true;
    return script.supported_data_types.includes(dataset.data_type)
      && script.supported_annotation_types.includes(selectedAnnotation.annotation_type);
  });

  const loadRuns = React.useCallback(async () => {
    const nextRuns = await listBatchAnnotationRuns(datasetId);
    setRuns(nextRuns);
    return nextRuns;
  }, [datasetId]);

  const loadInitialData = React.useCallback(async () => {
    setLoading(true);
    try {
      const [nextDataset, annotationPage, nextScripts] = await Promise.all([
        getDataset(datasetId),
        listAnnotations(1, 200),
        listBatchAnnotationScripts(),
      ]);
      if (!nextDataset) {
        message.error('数据集不存在');
        navigate('/datasets', { replace: true });
        return;
      }
      setDataset(nextDataset);
      setAnnotations((annotationPage?.items ?? []).filter((item) => item.dataset_id === datasetId));
      setScripts(nextScripts);
      const nextRuns = await loadRuns();
      const newestActive = nextRuns.find((item) => activeStatuses.has(item.status));
      if (newestActive) {
        setActiveRun(newestActive);
        lastEventIdRef.current = 0;
      }
    } catch {
      message.error('加载批量标注配置失败');
    } finally {
      setLoading(false);
    }
  }, [datasetId, loadRuns, navigate]);

  React.useEffect(() => { void loadInitialData(); }, [loadInitialData]);

  React.useEffect(() => {
    if (!selectedAnnotation || !dataset) return;
    const nextCompatibleScripts = scripts.filter((script) => (
      script.supported_data_types.includes(dataset.data_type)
      && script.supported_annotation_types.includes(selectedAnnotation.annotation_type)
    ));
    if (nextCompatibleScripts.length === 0) {
      form.setFieldValue('script_key', undefined);
      return;
    }
    if (!nextCompatibleScripts.some((script) => script.key === selectedScriptKey)) {
      const script = nextCompatibleScripts[0];
      form.setFieldValue('script_key', script.key);
      form.setFieldValue(
        'script_params',
        Object.fromEntries(script.parameter_fields.map((field) => [field.key, field.default_value])),
      );
    }
  }, [dataset, form, scripts, selectedAnnotation, selectedScriptKey]);

  const refreshActiveRun = React.useCallback(async () => {
    if (!activeRun) return;
    const [nextRun, nextEvents] = await Promise.all([
      getBatchAnnotationRun(activeRun.run_id),
      getBatchAnnotationRunEvents(activeRun.run_id, lastEventIdRef.current),
    ]);
    if (!nextRun) return;
    setActiveRun(nextRun);
    setRuns((current) => [nextRun, ...current.filter((item) => item.run_id !== nextRun.run_id)]);
    if (nextEvents.length > 0) {
      lastEventIdRef.current = nextEvents[nextEvents.length - 1].id;
      setEvents((current) => [...current, ...nextEvents].slice(-12));
    }
  }, [activeRun]);

  React.useEffect(() => {
    if (!activeRun || !activeStatuses.has(activeRun.status)) return;
    const timer = window.setInterval(() => { void refreshActiveRun(); }, 1500);
    return () => window.clearInterval(timer);
  }, [activeRun, refreshActiveRun]);

  const handleScriptChange = (scriptKey: string) => {
    const script = scripts.find((item) => item.key === scriptKey);
    if (!script) return;
    form.setFieldValue(
      'script_params',
      Object.fromEntries(script.parameter_fields.map((field) => [field.key, field.default_value])),
    );
  };

  const handleStart = async (values: BatchFormValues) => {
    if (!values.annotation_id || !values.script_key) return;
    setSubmitting(true);
    try {
      const run = await createBatchAnnotationRun({
        dataset_id: datasetId,
        annotation_id: values.annotation_id,
        script_key: values.script_key,
        selection_mode: values.selection_mode,
        overwrite_policy: values.overwrite_policy,
        script_params: values.script_params ?? {},
        batch_size: values.batch_size,
        parallelism: 1,
      });
      if (!run) throw new Error('任务创建失败');
      lastEventIdRef.current = 0;
      setEvents([]);
      setActiveRun(run);
      await refreshActiveRun();
      await loadRuns();
      message.success('批量标注任务已创建');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '创建批量标注任务失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSelectRun = async (run: AiPipelineBatchRun) => {
    lastEventIdRef.current = 0;
    setEvents([]);
    setActiveRun(run);
    try {
      const [nextRun, nextEvents] = await Promise.all([
        getBatchAnnotationRun(run.run_id),
        getBatchAnnotationRunEvents(run.run_id),
      ]);
      if (nextRun) setActiveRun(nextRun);
      if (nextEvents.length > 0) {
        lastEventIdRef.current = nextEvents[nextEvents.length - 1].id;
        setEvents(nextEvents.slice(-12));
      }
    } catch {
      message.error('加载任务详情失败');
    }
  };

  const handleCancel = async () => {
    if (!activeRun) return;
    try {
      const run = await cancelBatchAnnotationRun(activeRun.run_id);
      if (run) setActiveRun(run);
      await loadRuns();
      message.success('任务已取消，已完成的标注会保留');
    } catch {
      message.error('取消任务失败');
    }
  };

  if (loading) {
    return <div className="page-container" style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}><Spin /></div>;
  }
  if (!dataset) return null;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(`/datasets/${datasetId}`)}>返回数据集</Button>
          <div>
            <h1 className="page-title" style={{ margin: 0 }}>批量自动标注</h1>
            <Text type="secondary">{dataset.name}</Text>
          </div>
        </Space>
      </div>

      {annotations.length === 0 ? (
        <Alert
          type="warning"
          showIcon
          message="当前数据集还没有可用标注项目"
          description="请先创建并关联一个标注项目，再执行批量自动标注。"
          action={<Button size="small" onClick={() => navigate('/annotations')}>前往创建</Button>}
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(360px, 0.9fr) minmax(420px, 1.1fr)', gap: 24, alignItems: 'start' }}>
          <section style={{ paddingRight: 24, borderRight: '1px solid #f0f0f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <RobotOutlined />
              <Text strong>执行配置</Text>
            </div>
            <Form<BatchFormValues>
              form={form}
              layout="vertical"
              initialValues={{ selection_mode: 'unannotated', overwrite_policy: 'skip_existing', batch_size: 20, script_params: {} }}
              onFinish={handleStart}
            >
              <Form.Item name="annotation_id" label="写入标注项目" rules={[{ required: true, message: '请选择标注项目' }]}>
                <Select
                  placeholder="选择标注项目"
                  options={annotations.map((item) => ({ label: `${item.name} · ${item.annotation_type === 0 ? '检测' : '其他类型'}`, value: item.id }))}
                />
              </Form.Item>
              {selectedAnnotation ? (
                <Text type="secondary" style={{ display: 'block', marginTop: -14, marginBottom: 16 }}>
                  标注类型：{selectedAnnotation.annotation_type === 0 ? '检测' : selectedAnnotation.annotation_type}
                  {annotationClassNames.length > 0 ? ` · 类别：${annotationClassNames.join('、')}` : ''}
                </Text>
              ) : null}
              <Form.Item name="script_key" label="自动标注脚本" rules={[{ required: true, message: '请选择脚本' }]}>
                <Select
                  placeholder="选择脚本"
                  onChange={handleScriptChange}
                  options={compatibleScripts.map((script) => ({ label: `${script.name} · v${script.version}`, value: script.key }))}
                />
              </Form.Item>
              {selectedScript?.description ? <Text type="secondary" style={{ display: 'block', marginTop: -14, marginBottom: 16 }}>{selectedScript.description}</Text> : null}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <Form.Item name="selection_mode" label="执行范围">
                  <Select options={[{ label: '仅未标注样本', value: 'unannotated' }, { label: '全部样本', value: 'all' }]} />
                </Form.Item>
                <Form.Item name="overwrite_policy" label="已有标注处理">
                  <Select options={[
                    { label: '跳过已有结果', value: 'skip_existing' },
                    { label: '仅覆盖草稿', value: 'overwrite_draft' },
                    { label: '覆盖全部', value: 'overwrite_all' },
                  ]} />
                </Form.Item>
              </div>
              <Form.Item name="batch_size" label="单批样本数">
                <InputNumber min={1} max={100} style={{ width: '100%' }} />
              </Form.Item>
              {selectedScript?.parameter_fields.map((field) => (
                <Form.Item
                  key={field.key}
                  name={['script_params', field.key]}
                  label={field.label}
                  extra={field.description}
                  rules={field.required ? [{ required: true, message: `请填写${field.label}` }] : undefined}
                >
                  {field.value_type === 'number'
                    ? <InputNumber style={{ width: '100%' }} />
                    : <Input />}
                </Form.Item>
              ))}
              <Button type="primary" htmlType="submit" icon={<PlayCircleOutlined />} loading={submitting} block>
                创建并执行任务
              </Button>
            </Form>
          </section>

          <section>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <Text strong>任务进度</Text>
              {activeRun ? statusTag(activeRun.status) : null}
            </div>
            {!activeRun ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="尚未选择任务" /> : (
              <>
                <Progress percent={activeRun.progress} status={activeRun.status === 'failed' ? 'exception' : activeRun.status === 'canceled' ? 'normal' : 'active'} />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 12 }}>
                  <div><Text type="secondary">总数</Text><div>{activeRun.total_count}</div></div>
                  <div><Text type="secondary">成功</Text><div>{activeRun.succeeded_count}</div></div>
                  <div><Text type="secondary">失败</Text><div>{activeRun.failed_count}</div></div>
                  <div><Text type="secondary">跳过</Text><div>{activeRun.skipped_count}</div></div>
                </div>
                <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text type="secondary">开始于 {formatTime(activeRun.started_at ?? activeRun.created_at)}</Text>
                  {activeStatuses.has(activeRun.status) ? <Button danger size="small" icon={<DeleteOutlined />} onClick={handleCancel}>取消任务</Button> : null}
                </div>
                {activeRun.error_message ? <Alert style={{ marginTop: 12 }} type="error" showIcon message={activeRun.error_message} /> : null}
                <Divider style={{ margin: '16px 0 12px' }} />
                <Text strong>最新事件</Text>
                <div style={{ marginTop: 8, display: 'grid', gap: 6 }}>
                  {events.length === 0 ? <Text type="secondary">等待事件…</Text> : events.slice().reverse().map((event) => (
                    <div key={event.id} style={{ display: 'flex', gap: 8, fontSize: 12 }}>
                      <Text type="secondary">{formatTime(event.created_at)}</Text>
                      <span>{toEventText(event)}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>
        </div>
      )}

      <Divider />
      <Text strong>任务历史</Text>
      <Table<AiPipelineBatchRun>
        size="small"
        style={{ marginTop: 12 }}
        rowKey="run_id"
        pagination={false}
        dataSource={runs}
        onRow={(run) => ({ onClick: () => { void handleSelectRun(run); }, style: { cursor: 'pointer' } })}
        columns={[
          { title: '脚本', dataIndex: 'script_key', render: (_, run) => <span>{run.script_key}<Text type="secondary"> · v{run.script_version}</Text></span> },
          { title: '状态', dataIndex: 'status', width: 100, render: (status) => statusTag(status) },
          { title: '进度', dataIndex: 'progress', width: 180, render: (value, run) => <Progress percent={value} size="small" status={run.status === 'failed' ? 'exception' : 'normal'} /> },
          { title: '结果', width: 150, render: (_, run) => `${run.succeeded_count} 成功 / ${run.failed_count} 失败 / ${run.skipped_count} 跳过` },
          { title: '创建时间', dataIndex: 'created_at', width: 180, render: formatTime },
        ]}
      />
    </div>
  );
};

export default BatchAnnotationPage;
