import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeftOutlined,
  CheckCircleFilled,
  ClockCircleOutlined,
  CloseCircleFilled,
  DeleteOutlined,
  LoadingOutlined,
  ReloadOutlined,
  RobotOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import {
  Alert,
  Button,
  Drawer,
  Empty,
  Input,
  Progress,
  Spin,
  Table,
  Tag,
  Timeline,
  Tooltip,
  Typography,
  message,
} from 'antd';
import {
  cancelBatchAnnotationRun,
  getBatchAnnotationRun,
  getBatchAnnotationRunEvents,
  getBatchAnnotationRunItems,
} from '../../api/batchAnnotation';
import { subscribeBatchAnnotationRunStream } from '../../api/batchAnnotationStream';
import { emitBatchAnnotationRunsChanged } from '../../utils/projectEvents';
import type { AiPipelineBatchRun, AiPipelineBatchRunEvent, AiPipelineBatchRunItem } from '../../types';

const { Text } = Typography;
const activeStatuses = new Set(['queued', 'running']);
const itemPageSize = 50;

const statusLabelMap: Record<string, string> = {
  queued: '等待执行',
  running: '执行中',
  succeeded: '成功',
  failed: '失败',
  canceled: '已取消',
  pending: '待处理',
  skipped: '已跳过',
};

const statusColorMap: Record<string, string> = {
  queued: 'default',
  running: 'processing',
  succeeded: 'success',
  failed: 'error',
  canceled: 'warning',
  pending: 'default',
  skipped: 'warning',
};

const eventTitleMap: Record<string, string> = {
  queued: '任务等待执行',
  progress: '样本处理中',
  result: '样本处理完成',
  canceled: '任务已取消',
};

const formatNumber = (value: number) => new Intl.NumberFormat('zh-CN').format(value);
const formatTime = (value?: string | null) => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-';

const formatDuration = (start?: string | null, end?: string | null) => {
  if (!start) return '-';
  const milliseconds = Math.max(0, new Date(end ?? new Date()).getTime() - new Date(start).getTime());
  const totalSeconds = Math.floor(milliseconds / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) return `${hours}小时${minutes}分${seconds}秒`;
  if (minutes > 0) return `${minutes}分${seconds}秒`;
  return `${seconds}秒`;
};

const itemDuration = (item: AiPipelineBatchRunItem) => (
  item.started_at ? formatDuration(item.started_at, item.finished_at) : '-'
);

const statusTag = (status: string) => (
  <Tag color={statusColorMap[status] ?? 'default'} style={{ marginInlineEnd: 0 }}>
    {statusLabelMap[status] ?? status}
  </Tag>
);

const eventText = (event: AiPipelineBatchRunEvent) => {
  const payload = event.event_payload;
  if (event.event_type === 'queued') return '任务已创建，等待调度执行';
  if (event.event_type === 'progress' && payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const data = payload as Record<string, unknown>;
    const processed = data.processed;
    const total = data.total;
    return processed !== undefined && total !== undefined ? `当前批次已处理 ${processed}/${total}` : '正在处理当前批次';
  }
  if (event.event_type === 'result' && payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const data = payload as Record<string, unknown>;
    return `成功 ${data.succeeded_count ?? 0}，失败 ${data.failed_count ?? 0}，已跳过 ${data.skipped_count ?? 0}`;
  }
  if (event.event_type === 'canceled') return '任务已取消，已完成的标注结果已保留';
  if (typeof payload === 'string') return payload;
  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const data = payload as Record<string, unknown>;
    return String(data.message ?? data.error ?? data.chunk_key ?? event.event_type);
  }
  return event.event_type;
};

const eventDot = (eventType: string) => {
  if (eventType === 'result') return <CheckCircleFilled style={{ color: '#22c55e' }} />;
  if (eventType === 'canceled') return <CloseCircleFilled style={{ color: '#f59e0b' }} />;
  if (eventType === 'progress') return <LoadingOutlined style={{ color: '#2563eb' }} />;
  return <ClockCircleOutlined style={{ color: '#94a3b8' }} />;
};

const panelStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #e8edf3',
  borderRadius: 6,
};

const BatchAnnotationRunDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { runId = '' } = useParams<{ runId: string }>();
  const [run, setRun] = React.useState<AiPipelineBatchRun | null>(null);
  const [items, setItems] = React.useState<AiPipelineBatchRunItem[]>([]);
  const [itemsPage, setItemsPage] = React.useState(1);
  const [itemsTotal, setItemsTotal] = React.useState(0);
  const [itemStatus, setItemStatus] = React.useState<string>();
  const [itemKeyword, setItemKeyword] = React.useState('');
  const [events, setEvents] = React.useState<AiPipelineBatchRunEvent[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [itemsLoading, setItemsLoading] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);
  const [canceling, setCanceling] = React.useState(false);
  const [logDrawerOpen, setLogDrawerOpen] = React.useState(false);
  const lastEventIdRef = React.useRef(0);
  const itemsPageRef = React.useRef(1);

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
      setEvents((current) => initial ? nextEvents : [...current, ...nextEvents].slice(-100));
      if (nextEvents.length > 0) lastEventIdRef.current = nextEvents[nextEvents.length - 1].id;
    } catch (error) {
      if (initial) message.error(error instanceof Error ? error.message : '加载批量标注任务失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [runId]);

  const loadItems = React.useCallback(async (page = itemsPageRef.current) => {
    if (!runId) return;
    setItemsLoading(true);
    try {
      const result = await getBatchAnnotationRunItems(runId, page, itemPageSize, itemStatus);
      setItems(result?.items ?? []);
      setItemsTotal(result?.total ?? 0);
    } catch {
      message.error('加载样本结果失败');
    } finally {
      setItemsLoading(false);
    }
  }, [itemStatus, runId]);

  React.useEffect(() => {
    lastEventIdRef.current = 0;
    setEvents([]);
    void loadRun(true);
  }, [loadRun]);

  React.useEffect(() => {
    itemsPageRef.current = 1;
    setItemsPage(1);
    void loadItems(1);
  }, [loadItems]);

  React.useEffect(() => {
    if (!runId) return;

    return subscribeBatchAnnotationRunStream(runId, {
      onEvent: ({ data }) => {
        setRun(data.run);
        lastEventIdRef.current = Math.max(lastEventIdRef.current, data.event.id);
        setEvents((current) => {
          if (current.some((event) => event.id === data.event.id)) return current;
          return [...current, data.event].slice(-100);
        });
        void loadItems();
      },
    });
  }, [loadItems, runId]);

  const handleCancel = async () => {
    if (!run) return;
    setCanceling(true);
    try {
      const nextRun = await cancelBatchAnnotationRun(run.run_id);
      if (nextRun) setRun(nextRun);
      emitBatchAnnotationRunsChanged();
      message.success('任务已取消，已完成的标注会保留');
      await Promise.all([loadRun(), loadItems()]);
    } catch {
      message.error('取消任务失败');
    } finally {
      setCanceling(false);
    }
  };

  if (loading) {
    return <div className="page-container" style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}><Spin /></div>;
  }

  if (!run) {
    return <div className="page-container"><Empty description="批量标注任务不存在" /></div>;
  }

  const pendingCount = Math.max(
    run.total_count - run.succeeded_count - run.failed_count - run.skipped_count - run.canceled_count,
    0,
  );
  const completedCount = run.total_count - pendingCount;
  const parameterEntries = Object.entries(run.script_params);
  const visibleItems = itemKeyword.trim()
    ? items.filter((item) => item.item_key.toLowerCase().includes(itemKeyword.trim().toLowerCase()))
    : items;
  const runElapsed = formatDuration(run.started_at ?? run.created_at, run.finished_at);
  const progressStatus = run.status === 'failed' ? 'exception' : run.status === 'canceled' ? 'normal' : 'active';
  const statusTabs = [
    { key: 'all', label: '全部', count: run.total_count },
    { key: 'succeeded', label: '成功', count: run.succeeded_count },
    { key: 'failed', label: '失败', count: run.failed_count },
    { key: 'pending', label: '待处理', count: pendingCount },
    { key: 'skipped', label: '已跳过', count: run.skipped_count },
  ];

  return (
    <div className="page-container" style={{ maxWidth: 1440, paddingTop: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#64748b', fontSize: 13, marginBottom: 18 }}>
        <Tooltip title="返回运行记录">
          <Button type="text" size="small" icon={<ArrowLeftOutlined />} aria-label="返回运行记录" onClick={() => navigate('/batch-annotation/runs')} />
        </Tooltip>
        <span>批量标注</span>
        <span style={{ color: '#cbd5e1' }}>/</span>
        <span>运行记录</span>
        <span style={{ color: '#cbd5e1' }}>/</span>
        <span style={{ color: '#334155' }}>运行详情</span>
      </div>

      <div className="page-header" style={{ marginBottom: 22 }}>
        <div>
          <h1 className="page-title">运行详情</h1>
          <p className="page-subtitle">查看批量标注任务的执行进度、样本状态和运行日志</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Button icon={<ReloadOutlined />} loading={refreshing} onClick={() => void loadRun()}>刷新</Button>
          {activeStatuses.has(run.status) ? (
            <Button danger type="primary" icon={<DeleteOutlined />} loading={canceling} onClick={() => void handleCancel()}>
              取消任务
            </Button>
          ) : null}
        </div>
      </div>

      <section style={{ ...panelStyle, padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 24, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: 14, minWidth: 0 }}>
            <div style={{ width: 52, height: 52, flex: '0 0 auto', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', borderRadius: 6, background: '#eff6ff', color: '#2563eb', fontSize: 26 }}>
              <RobotOutlined />
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                <h2 style={{ margin: 0, color: '#1e293b', fontSize: 20, lineHeight: '28px' }}>批量标注任务 #{run.run_id}</h2>
                {statusTag(run.status)}
              </div>
              <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>{run.script_key} · v{run.script_version}</Text>
            </div>
          </div>
          <div style={{ color: '#64748b', fontSize: 13, whiteSpace: 'nowrap' }}>
            {run.started_at ? `已运行 ${runElapsed}` : '等待执行'}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '20px 28px', marginTop: 22 }}>
          {[
            { label: '创建时间', value: formatTime(run.created_at) },
            { label: '开始时间', value: formatTime(run.started_at) },
            { label: '数据集', value: `数据集 ID #${run.dataset_id}`, accent: true },
            { label: '标注项目', value: `标注 ID #${run.annotation_id}`, accent: true },
            { label: '执行范围', value: run.selection_mode === 'unannotated' ? '仅未标注样本' : run.selection_mode === 'selected' ? '指定样本' : '全部样本' },
            { label: '并发数', value: `${run.parallelism} 个批次` },
          ].map((item) => (
            <div key={item.label} style={{ minWidth: 0 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>{item.label}</Text>
              <div style={{ marginTop: 4, color: item.accent ? '#2563eb' : '#334155', fontSize: 14, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.value}
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(260px, 1fr) repeat(4, minmax(98px, auto))', gap: 24, alignItems: 'end', marginTop: 26, paddingTop: 20, borderTop: '1px solid #edf1f5' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 8 }}>
              <Text strong style={{ color: '#334155' }}>总体进度</Text>
              <Text style={{ color: '#2563eb', fontWeight: 600 }}>{run.progress.toFixed(1)}%</Text>
            </div>
            <Progress percent={run.progress} showInfo={false} status={progressStatus} strokeColor="#2563eb" trailColor="#eaf0f7" />
            <Text type="secondary" style={{ display: 'block', marginTop: 7, fontSize: 12 }}>已完成 {formatNumber(completedCount)} / {formatNumber(run.total_count)}</Text>
          </div>
          {[
            { label: '总样本数', value: run.total_count, color: '#1e293b' },
            { label: '成功', value: run.succeeded_count, color: '#22c55e' },
            { label: '失败', value: run.failed_count, color: '#ef4444' },
            { label: '待处理', value: pendingCount, color: '#64748b' },
          ].map((metric) => (
            <div key={metric.label}>
              <Text type="secondary" style={{ fontSize: 12 }}>{metric.label}</Text>
              <div style={{ marginTop: 4, color: metric.color, fontSize: 20, lineHeight: '28px', fontWeight: 700 }}>{formatNumber(metric.value)}</div>
            </div>
          ))}
        </div>
        {run.error_message ? <Alert style={{ marginTop: 18 }} type="error" showIcon message={run.error_message} /> : null}
      </section>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[304px_minmax(0,1fr)]">
        <aside style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <section style={{ ...panelStyle, padding: '18px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <h2 style={{ margin: 0, fontSize: 16, color: '#1e293b' }}>运行状态</h2>
              <Button type="link" size="small" onClick={() => setLogDrawerOpen(true)}>全部日志</Button>
            </div>
            {events.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无运行日志" style={{ marginBlock: 18 }} />
            ) : (
              <Timeline
                items={events.slice(-5).map((event) => ({
                  dot: eventDot(event.event_type),
                  children: (
                    <div style={{ paddingBottom: 7 }}>
                      <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <Text strong style={{ color: '#334155', fontSize: 13 }}>{eventTitleMap[event.event_type] ?? event.event_type}</Text>
                        <Text type="secondary" style={{ fontSize: 11, whiteSpace: 'nowrap' }}>{formatTime(event.created_at)}</Text>
                      </div>
                      <Text type="secondary" style={{ display: 'block', marginTop: 3, fontSize: 12, lineHeight: '18px' }}>{eventText(event)}</Text>
                    </div>
                  ),
                }))}
              />
            )}
          </section>

          <section style={{ ...panelStyle, padding: '18px 16px' }}>
            <h2 style={{ margin: '0 0 12px', fontSize: 16, color: '#1e293b' }}>任务信息</h2>
            {[
              { label: '运行 ID', value: run.run_id },
              { label: '状态', value: statusTag(run.status) },
              { label: '批次大小', value: run.batch_size },
              { label: '并发数', value: run.parallelism },
              { label: '已有标注处理', value: run.overwrite_policy === 'overwrite_all' ? '覆盖全部' : run.overwrite_policy === 'overwrite_draft' ? '仅覆盖草稿' : '跳过已有结果' },
              { label: '结束时间', value: formatTime(run.finished_at) },
            ].map((item, index) => (
              <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', padding: '11px 0', borderTop: index === 0 ? 'none' : '1px solid #f0f3f6' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>{item.label}</Text>
                <span style={{ color: '#334155', fontSize: 12, fontWeight: 500, textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.value}</span>
              </div>
            ))}
          </section>
        </aside>

        <main style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>
          <section style={{ ...panelStyle, padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 26, flexWrap: 'wrap' }}>
              <div style={{ minWidth: 180, textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={run.total_count ? Math.round((run.succeeded_count / run.total_count) * 100) : 0}
                  size={164}
                  strokeWidth={10}
                  strokeColor="#22c55e"
                  trailColor="#e8eef5"
                  format={() => (
                    <div>
                      <div style={{ color: '#1e293b', fontSize: 25, fontWeight: 700, lineHeight: '30px' }}>{formatNumber(run.total_count)}</div>
                      <div style={{ color: '#64748b', fontSize: 12, marginTop: 3 }}>总样本数</div>
                    </div>
                  )}
                />
              </div>
              <div style={{ flex: '1 1 230px', minWidth: 220 }}>
                <h2 style={{ margin: '0 0 16px', fontSize: 16, color: '#1e293b' }}>样本处理结果</h2>
                <div style={{ display: 'grid', gap: 13 }}>
                  {[
                    { label: '成功', value: run.succeeded_count, color: '#22c55e' },
                    { label: '失败', value: run.failed_count, color: '#ef4444' },
                    { label: '待处理', value: pendingCount, color: '#94a3b8' },
                    { label: '已跳过', value: run.skipped_count, color: '#f59e0b' },
                  ].map((item) => (
                    <div key={item.label} style={{ display: 'grid', gridTemplateColumns: '10px 54px 1fr auto', gap: 8, alignItems: 'center', fontSize: 13 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: item.color }} />
                      <span style={{ color: '#475569' }}>{item.label}</span>
                      <Progress percent={run.total_count ? (item.value / run.total_count) * 100 : 0} showInfo={false} strokeColor={item.color} trailColor="#edf1f5" size="small" />
                      <span style={{ color: '#475569', fontVariantNumeric: 'tabular-nums' }}>{formatNumber(item.value)} ({run.total_count ? ((item.value / run.total_count) * 100).toFixed(1) : 0}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {parameterEntries.length > 0 ? (
            <section style={{ ...panelStyle, padding: '16px 20px' }}>
              <h2 style={{ margin: '0 0 14px', fontSize: 16, color: '#1e293b' }}>运行参数</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px 24px' }}>
                {parameterEntries.map(([key, value]) => (
                  <div key={key} style={{ minWidth: 0 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>{key}</Text>
                    <div style={{ marginTop: 3, color: '#334155', fontSize: 13, wordBreak: 'break-word' }}>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</div>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          <section style={{ ...panelStyle, overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap', padding: '18px 20px 12px' }}>
              <h2 style={{ margin: 0, fontSize: 18, color: '#1e293b' }}>样本处理列表</h2>
              <Input
                allowClear
                prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
                placeholder="搜索当前页文件名"
                value={itemKeyword}
                onChange={(event) => setItemKeyword(event.target.value)}
                style={{ width: 220 }}
              />
            </div>
            <div style={{ paddingInline: 20 }}>
              <div style={{ display: 'flex', gap: 20, overflowX: 'auto', borderBottom: '1px solid #edf1f5' }}>
                {statusTabs.map((tab) => {
                  const active = (itemStatus ?? 'all') === tab.key;
                  return (
                    <button
                      key={tab.key}
                      type="button"
                      onClick={() => setItemStatus(tab.key === 'all' ? undefined : tab.key)}
                      style={{
                        appearance: 'none',
                        border: 'none',
                        borderBottom: active ? '2px solid #2563eb' : '2px solid transparent',
                        background: 'transparent',
                        color: active ? '#2563eb' : '#64748b',
                        cursor: 'pointer',
                        fontSize: 14,
                        fontWeight: active ? 600 : 500,
                        padding: '0 2px 10px',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {tab.label} <span style={{ color: active ? '#2563eb' : '#94a3b8', fontVariantNumeric: 'tabular-nums' }}>{formatNumber(tab.count)}</span>
                    </button>
                  );
                })}
              </div>
            </div>
            <Table<AiPipelineBatchRunItem>
              rowKey="id"
              size="middle"
              loading={itemsLoading}
              dataSource={visibleItems}
              scroll={{ x: 980 }}
              pagination={{
                current: itemsPage,
                pageSize: itemPageSize,
                total: itemsTotal,
                showSizeChanger: false,
                showTotal: (total) => `共 ${formatNumber(total)} 条`,
                onChange: (page) => {
                  itemsPageRef.current = page;
                  setItemsPage(page);
                  void loadItems(page);
                },
              }}
              columns={[
                { title: '文件名', dataIndex: 'item_key', ellipsis: true, render: (value) => <span style={{ color: '#334155', fontWeight: 500 }}>{value}</span> },
                { title: '状态', dataIndex: 'status', width: 110, render: statusTag },
                { title: '处理耗时', width: 110, render: (_, item) => itemDuration(item) },
                { title: '错误信息', dataIndex: 'error_message', ellipsis: true, render: (value) => value || '-' },
                { title: '完成时间', dataIndex: 'finished_at', width: 172, render: formatTime },
                { title: '标注记录', dataIndex: 'annotation_record_id', width: 110, render: (value) => value ? `#${value}` : '-' },
              ]}
            />
          </section>
        </main>
      </div>

      <Drawer title="运行日志" width={620} open={logDrawerOpen} onClose={() => setLogDrawerOpen(false)}>
        {events.length === 0 ? <Empty description="暂无运行日志" /> : (
          <Table<AiPipelineBatchRunEvent>
            rowKey="id"
            size="small"
            pagination={{ pageSize: 10, showSizeChanger: false }}
            dataSource={events.slice().reverse()}
            scroll={{ x: 520 }}
            columns={[
              { title: '时间', dataIndex: 'created_at', width: 170, render: formatTime },
              { title: '类型', dataIndex: 'event_type', width: 110, render: (value) => eventTitleMap[value] ?? value },
              { title: '内容', render: (_, event) => eventText(event) },
            ]}
          />
        )}
      </Drawer>
    </div>
  );
};

export default BatchAnnotationRunDetailPage;
