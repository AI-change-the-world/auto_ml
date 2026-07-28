import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeftOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { Alert, Button, Empty, Progress, Space, Spin, Table, Tag, Typography, message } from 'antd';
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
  const parameterEntries = Object.entries(run.script_params);
  const summaryItems = [
    { label: '标注工具', value: run.script_key },
    { label: '数据集', value: `数据集 ID #${run.dataset_id}` },
    { label: '标注项目', value: `标注 ID #${run.annotation_id}` },
    { label: '状态', value: statusTag(run.status) },
    { label: '执行范围', value: run.selection_mode === 'unannotated' ? '仅未标注样本' : run.selection_mode === 'selected' ? '指定样本' : '全部样本' },
    { label: '已有标注处理', value: run.overwrite_policy === 'overwrite_all' ? '覆盖全部' : run.overwrite_policy === 'overwrite_draft' ? '仅覆盖草稿' : '跳过已有结果' },
    { label: '创建时间', value: formatTime(run.created_at) },
    { label: '更新时间', value: formatTime(run.updated_at) },
  ];

  return (
    <div className="page-container" style={{ maxWidth: 1280, margin: '0 auto', paddingTop: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <Button size="large" icon={<ArrowLeftOutlined />} onClick={() => navigate('/batch-annotation/runs')} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
            <h1 className="page-title" style={{ margin: 0 }}>批量标注任务</h1>
            {statusTag(run.status)}
          </div>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} loading={refreshing} onClick={() => void loadRun()}>刷新</Button>
          {activeStatuses.has(run.status) ? <Button danger icon={<DeleteOutlined />} loading={canceling} onClick={() => void handleCancel()}>取消任务</Button> : null}
        </Space>
      </div>

      <section style={{ background: '#fff', border: '1px solid #e8eaee', borderRadius: 8, padding: 28, marginBottom: 20 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '26px 36px' }}>
          {summaryItems.map((item) => (
            <div key={item.label}>
              <Text type="secondary">{item.label}</Text>
              <div style={{ marginTop: 5, fontWeight: 600, color: '#1f2937', minHeight: 24 }}>{item.value}</div>
            </div>
          ))}
        </div>

        <div style={{ background: '#f7f8fa', borderRadius: 6, padding: 18, marginTop: 26 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <Text strong>执行进度</Text>
            <Text type="secondary">{run.progress}%</Text>
          </div>
          <Progress
            percent={run.progress}
            showInfo={false}
            status={run.status === 'failed' ? 'exception' : run.status === 'canceled' ? 'normal' : 'active'}
          />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 16, marginTop: 16 }}>
            {[
              { label: '总样本', value: run.total_count },
              { label: '成功', value: run.succeeded_count },
              { label: '失败', value: run.failed_count },
              { label: '跳过', value: run.skipped_count },
            ].map((item) => (
              <div key={item.label}>
                <Text type="secondary" style={{ fontSize: 12 }}>{item.label}</Text>
                <div style={{ marginTop: 3, fontWeight: 600 }}>{item.value}</div>
              </div>
            ))}
          </div>
        </div>
        {run.error_message ? <Alert style={{ marginTop: 14 }} type="error" showIcon message={run.error_message} /> : null}

        <div style={{ background: '#f7f8fa', borderRadius: 6, padding: 18, marginTop: 16 }}>
          <Text type="secondary">运行参数</Text>
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 6, padding: '14px 16px', marginTop: 10 }}>
            {parameterEntries.length === 0 ? <Text type="secondary">无</Text> : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px 24px' }}>
                {parameterEntries.map(([key, value]) => (
                  <div key={key} style={{ minWidth: 0 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>{key}</Text>
                    <div style={{ marginTop: 3, wordBreak: 'break-word' }}>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      <section style={{ background: '#fff', border: '1px solid #e8eaee', borderRadius: 8, overflow: 'hidden', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid #f0f0f0' }}>
          <Text strong style={{ fontSize: 18 }}>样本结果</Text>
          <Text type="secondary">共 {itemsTotal} 条</Text>
        </div>
        <Table<AiPipelineBatchRunItem>
          rowKey="id"
          size="small"
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
      </section>

      <section style={{ background: '#fff', border: '1px solid #e8eaee', borderRadius: 8, overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid #f0f0f0' }}>
          <Text strong style={{ fontSize: 18 }}>任务事件</Text>
          <Text type="secondary">共 {events.length} 条</Text>
        </div>
        {events.length === 0 ? <Empty style={{ padding: '24px 0' }} image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无事件" /> : (
          <Table<AiPipelineBatchRunEvent>
            rowKey="id"
            size="small"
            pagination={{ pageSize: 10, showSizeChanger: false }}
            dataSource={events.slice().reverse()}
            columns={[
              { title: '时间', dataIndex: 'created_at', width: 190, render: formatTime },
              { title: '类型', dataIndex: 'event_type', width: 120 },
              { title: '内容', render: (_, event) => eventText(event) },
            ]}
          />
        )}
      </section>
    </div>
  );
};

export default BatchAnnotationRunDetailPage;
