import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeftOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { Alert, Button, Descriptions, Divider, Empty, Progress, Space, Spin, Table, Tag, Typography, message } from 'antd';
import {
  cancelBatchAnnotationRun,
  getBatchAnnotationRun,
  getBatchAnnotationRunEvents,
  getBatchAnnotationRunItems,
} from '../../api/batchAnnotation';
import { emitBatchAnnotationRunsChanged } from '../../utils/projectEvents';
import type { AiPipelineBatchRun, AiPipelineBatchRunEvent, AiPipelineBatchRunItem } from '../../types';

const { Text } = Typography;
const activeStatuses = new Set(['queued', 'running']);

const statusTag = (status: string) => {
  const colorMap: Record<string, string> = { queued: 'default', running: 'processing', succeeded: 'success', failed: 'error', canceled: 'warning', pending: 'default', skipped: 'warning' };
  const labelMap: Record<string, string> = { queued: '等待执行', running: '执行中', succeeded: '成功', failed: '失败', canceled: '已取消', pending: '待处理', skipped: '已跳过' };
  return <Tag color={colorMap[status] ?? 'default'}>{labelMap[status] ?? status}</Tag>;
};

const formatTime = (value?: string | null) => value ? new Date(value).toLocaleString() : '-';

const eventText = (event: AiPipelineBatchRunEvent) => {
  if (typeof event.event_payload === 'string') return event.event_payload;
  if (event.event_payload && typeof event.event_payload === 'object') {
    const payload = event.event_payload as Record<string, unknown>;
    return String(payload.message ?? payload.error ?? payload.chunk_key ?? event.event_type);
  }
  return event.event_type;
};

const BatchAnnotationRunDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { runId = '' } = useParams<{ runId: string }>();
  const [run, setRun] = React.useState<AiPipelineBatchRun | null>(null);
  const [items, setItems] = React.useState<AiPipelineBatchRunItem[]>([]);
  const [itemsPage, setItemsPage] = React.useState(1);
  const [itemsTotal, setItemsTotal] = React.useState(0);
  const [events, setEvents] = React.useState<AiPipelineBatchRunEvent[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [canceling, setCanceling] = React.useState(false);
  const lastEventIdRef = React.useRef(0);
  const itemsPageRef = React.useRef(1);
  const itemsPageSize = 50;

  const loadRun = React.useCallback(async (initial = false) => {
    if (!runId) return;
    if (initial) setLoading(true);
    else setRefreshing(true);
    try {
      const [nextRun, nextEvents] = await Promise.all([
        getBatchAnnotationRun(runId),
        getBatchAnnotationRunEvents(runId, initial ? 0 : lastEventIdRef.current),
      ]);
      if (!nextRun) throw new Error('任务不存在');
      setRun(nextRun);
      if (initial) {
        setEvents(nextEvents);
      } else if (nextEvents.length > 0) {
        setEvents((current) => [...current, ...nextEvents].slice(-100));
      }
      if (nextEvents.length > 0) lastEventIdRef.current = nextEvents[nextEvents.length - 1].id;
    } catch (error) {
      if (initial) {
        message.error(error instanceof Error ? error.message : '加载批量标注任务失败');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [runId]);

  const loadItems = React.useCallback(async (page = itemsPageRef.current) => {
    if (!runId) return;
    try {
      const result = await getBatchAnnotationRunItems(runId, page, itemsPageSize);
      setItems(result?.items ?? []);
      setItemsTotal(result?.total ?? 0);
    } catch {
      message.error('加载样本结果失败');
    }
  }, [runId]);

  React.useEffect(() => {
    lastEventIdRef.current = 0;
    setEvents([]);
    itemsPageRef.current = 1;
    setItemsPage(1);
    void loadRun(true);
    void loadItems(1);
  }, [loadItems, loadRun]);

  React.useEffect(() => {
    if (!run || !activeStatuses.has(run.status)) return;
    const timer = window.setInterval(() => {
      void loadRun();
      void loadItems();
    }, 1500);
    return () => window.clearInterval(timer);
  }, [loadItems, loadRun, run]);

  const handleCancel = async () => {
    if (!run) return;
    setCanceling(true);
    try {
      const nextRun = await cancelBatchAnnotationRun(run.run_id);
      if (nextRun) setRun(nextRun);
      emitBatchAnnotationRunsChanged();
      message.success('任务已取消，已完成的标注会保留');
      await loadRun();
      await loadItems();
    } catch {
      message.error('取消任务失败');
    } finally {
      setCanceling(false);
    }
  };

  if (loading) return <div className="page-container" style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}><Spin /></div>;
  if (!run) return <div className="page-container"><Empty description="批量标注任务不存在" /></div>;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/batch-annotation/runs')}>返回任务列表</Button>
          <div style={{ minWidth: 0 }}>
            <h1 className="page-title" style={{ margin: 0 }}>批量标注任务</h1>
            <Text type="secondary">{run.script_key} · {run.run_id}</Text>
          </div>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} loading={refreshing} onClick={() => void loadRun()}>刷新</Button>
          {activeStatuses.has(run.status) ? <Button danger icon={<DeleteOutlined />} loading={canceling} onClick={() => void handleCancel()}>取消任务</Button> : null}
        </Space>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <Text strong>执行进度</Text>{statusTag(run.status)}
      </div>
      <Progress percent={run.progress} status={run.status === 'failed' ? 'exception' : run.status === 'canceled' ? 'normal' : 'active'} />
      <Descriptions size="small" column={{ xs: 2, sm: 3, lg: 6 }} style={{ marginTop: 16 }}>
        <Descriptions.Item label="总数">{run.total_count}</Descriptions.Item>
        <Descriptions.Item label="成功">{run.succeeded_count}</Descriptions.Item>
        <Descriptions.Item label="失败">{run.failed_count}</Descriptions.Item>
        <Descriptions.Item label="跳过">{run.skipped_count}</Descriptions.Item>
        <Descriptions.Item label="数据集">#{run.dataset_id}</Descriptions.Item>
        <Descriptions.Item label="标注项目">#{run.annotation_id}</Descriptions.Item>
      </Descriptions>
      {run.error_message ? <Alert style={{ marginTop: 16 }} type="error" showIcon message={run.error_message} /> : null}

      <Divider />
      <Text strong>运行参数</Text>
      <Descriptions size="small" column={{ xs: 1, sm: 2, lg: 3 }} style={{ marginTop: 12 }}>
        {Object.entries(run.script_params).length === 0 ? <Descriptions.Item label="参数">无</Descriptions.Item> : Object.entries(run.script_params).map(([key, value]) => <Descriptions.Item key={key} label={key}>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</Descriptions.Item>)}
      </Descriptions>

      <Divider />
      <Text strong>样本结果</Text>
      <Table<AiPipelineBatchRunItem>
        rowKey="id"
        size="small"
        style={{ marginTop: 12 }}
        pagination={{
          current: itemsPage,
          pageSize: itemsPageSize,
          total: itemsTotal,
          showSizeChanger: false,
          onChange: (page) => {
            itemsPageRef.current = page;
            setItemsPage(page);
            void loadItems(page);
          },
        }}
        dataSource={items}
        columns={[
          { title: '样本', dataIndex: 'item_key', ellipsis: true },
          { title: '状态', dataIndex: 'status', width: 110, render: statusTag },
          { title: '尝试', dataIndex: 'attempt_count', width: 75 },
          { title: '标注记录', dataIndex: 'annotation_record_id', width: 110, render: (value) => value ? `#${value}` : '-' },
          { title: '错误', dataIndex: 'error_message', ellipsis: true, render: (value) => value || '-' },
          { title: '完成时间', dataIndex: 'finished_at', width: 180, render: formatTime },
        ]}
      />

      <Divider />
      <Text strong>事件</Text>
      {events.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无事件" /> : (
        <Table<AiPipelineBatchRunEvent>
          rowKey="id"
          size="small"
          style={{ marginTop: 12 }}
          pagination={{ pageSize: 10, showSizeChanger: false }}
          dataSource={events.slice().reverse()}
          columns={[
            { title: '时间', dataIndex: 'created_at', width: 190, render: formatTime },
            { title: '类型', dataIndex: 'event_type', width: 120 },
            { title: '内容', render: (_, event) => eventText(event) },
          ]}
        />
      )}
    </div>
  );
};

export default BatchAnnotationRunDetailPage;
