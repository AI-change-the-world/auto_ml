import React from 'react';
import { useParams } from 'react-router-dom';
import {
  CloseOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import {
  Alert,
  Button,
  ConfigProvider,
  Descriptions,
  Drawer,
  Empty,
  Popconfirm,
  Spin,
  Table,
  message,
} from 'antd';
import {
  cancelBatchAnnotationRun,
  getBatchAnnotationRun,
  getBatchAnnotationRunEvents,
  getBatchAnnotationRunItems,
} from '../../api/batchAnnotation';
import { subscribeBatchAnnotationRunStream } from '../../api/batchAnnotationStream';
import type {
  AiPipelineBatchRunDetail,
  AiPipelineBatchRunEvent,
  AiPipelineBatchRunItem,
} from '../../types';
import { emitBatchAnnotationRunsChanged } from '../../utils/projectEvents';
import {
  BatchAnnotationRunInfo,
  BatchAnnotationRunOverview,
  BatchAnnotationRunResults,
  BatchAnnotationRunTimeline,
} from './components/BatchAnnotationRunOverview';
import { BatchAnnotationRunItemsPanel } from './components/BatchAnnotationRunItemsPanel';
import {
  activeBatchRunStatuses,
  appendProgressPointFromEvent,
  batchRunEventTitles,
  batchRunItemPageSize,
  batchRunStatusLabels,
  formatClock,
  formatDateTime,
  getBatchRunEventText,
  mergeBatchRunEvents,
} from './components/batchAnnotationRunDetailUtils';

const BatchAnnotationRunDetailPage: React.FC = () => {
  const { runId = '' } = useParams<{ runId: string }>();
  const [run, setRun] = React.useState<AiPipelineBatchRunDetail | null>(null);
  const [items, setItems] = React.useState<AiPipelineBatchRunItem[]>([]);
  const [itemsPage, setItemsPage] = React.useState(1);
  const [itemsTotal, setItemsTotal] = React.useState(0);
  const [itemStatus, setItemStatus] = React.useState<string>();
  const [searchInput, setSearchInput] = React.useState('');
  const [itemKeyword, setItemKeyword] = React.useState('');
  const [events, setEvents] = React.useState<AiPipelineBatchRunEvent[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [itemsLoading, setItemsLoading] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);
  const [canceling, setCanceling] = React.useState(false);
  const [logDrawerOpen, setLogDrawerOpen] = React.useState(false);
  const [selectedItem, setSelectedItem] = React.useState<AiPipelineBatchRunItem | null>(null);
  const lastEventIdRef = React.useRef(0);
  const itemsPageRef = React.useRef(1);

  const loadRun = React.useCallback(async (initial = false) => {
    if (!runId) return;
    if (initial) setLoading(true);
    else setRefreshing(true);
    try {
      const [nextRun, nextEvents] = await Promise.all([
        getBatchAnnotationRun(runId),
        getBatchAnnotationRunEvents(runId, initial ? 0 : lastEventIdRef.current, true),
      ]);
      if (!nextRun) throw new Error('任务不存在');
      setRun(nextRun);
      setEvents((current) => mergeBatchRunEvents(current, nextEvents));
      if (nextEvents.length > 0) {
        lastEventIdRef.current = Math.max(lastEventIdRef.current, nextEvents[nextEvents.length - 1].id);
      }
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
      const result = await getBatchAnnotationRunItems(
        runId,
        page,
        batchRunItemPageSize,
        itemStatus,
        itemKeyword || undefined,
      );
      setItems(result?.items ?? []);
      setItemsTotal(result?.total ?? 0);
    } catch {
      message.error('加载样本结果失败');
    } finally {
      setItemsLoading(false);
    }
  }, [itemKeyword, itemStatus, runId]);

  const loadItemsRef = React.useRef(loadItems);
  React.useEffect(() => {
    loadItemsRef.current = loadItems;
  }, [loadItems]);

  React.useEffect(() => {
    lastEventIdRef.current = 0;
    itemsPageRef.current = 1;
    setItemsPage(1);
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
        setRun((current) => current ? {
          ...current,
          ...data.run,
          progress_points: appendProgressPointFromEvent(current.progress_points, data.event),
        } : current);
        lastEventIdRef.current = Math.max(lastEventIdRef.current, data.event.id);
        setEvents((current) => mergeBatchRunEvents(current, [data.event]));
        void loadItemsRef.current();
      },
    });
  }, [runId]);

  React.useEffect(() => {
    if (!run || !activeBatchRunStatuses.has(run.status)) return;
    const timer = window.setInterval(() => setRun((current) => current ? { ...current } : current), 1000);
    return () => window.clearInterval(timer);
  }, [run?.status]);

  const handleRefresh = async () => {
    await Promise.all([loadRun(), loadItems()]);
  };

  const handleCancel = async () => {
    if (!run) return;
    setCanceling(true);
    try {
      const nextRun = await cancelBatchAnnotationRun(run.run_id);
      if (nextRun) setRun((current) => current ? { ...current, ...nextRun } : current);
      emitBatchAnnotationRunsChanged();
      message.success('任务已取消，已完成的标注会保留');
      await Promise.all([loadRun(), loadItems()]);
    } catch {
      message.error('取消任务失败');
    } finally {
      setCanceling(false);
    }
  };

  const handlePageChange = (page: number) => {
    itemsPageRef.current = page;
    setItemsPage(page);
    void loadItems(page);
  };

  if (loading) {
    return <div className="flex min-h-full items-start justify-center bg-gray-50 pt-32"><Spin /></div>;
  }
  if (!run) {
    return <div className="min-h-full bg-gray-50 p-8"><Empty description="批量标注任务不存在" /></div>;
  }

  const pendingCount = Math.max(
    run.total_count - run.succeeded_count - run.failed_count - run.skipped_count - run.canceled_count,
    0,
  );
  const processedCount = run.total_count - pendingCount;

  return (
    <ConfigProvider theme={{ token: { colorPrimary: '#3b82f6', borderRadius: 6 } }}>
      <div className="min-h-full min-w-0 bg-gray-50">
      <div className="mx-auto max-w-[1440px] p-4 sm:p-6">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-gray-900">运行详情</h1>
            <p className="mt-1 text-sm text-gray-500">实时查看批量标注任务的执行进度、样本处理状态和运行日志</p>
          </div>
          <div className="flex shrink-0 gap-3">
            <Button icon={<SyncOutlined />} loading={refreshing} onClick={() => void handleRefresh()}>刷新</Button>
            {activeBatchRunStatuses.has(run.status) ? (
              <Popconfirm
                title="确认取消当前任务？"
                description="已经完成的标注结果会保留。"
                okText="取消任务"
                cancelText="继续执行"
                okButtonProps={{ danger: true, loading: canceling }}
                onConfirm={() => void handleCancel()}
              >
                <Button danger type="primary" icon={<CloseOutlined />} loading={canceling}>取消任务</Button>
              </Popconfirm>
            ) : null}
          </div>
        </div>

        <BatchAnnotationRunOverview run={run} pendingCount={pendingCount} processedCount={processedCount} />

        <div className="mt-6 grid min-w-0 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
          <aside className="flex h-full min-w-0 flex-col gap-6">
            <BatchAnnotationRunTimeline run={run} events={events} onShowAll={() => setLogDrawerOpen(true)} />
            <BatchAnnotationRunInfo run={run} className="flex-1" />
          </aside>
          <main className="flex min-w-0 flex-col gap-6">
            <BatchAnnotationRunResults run={run} pendingCount={pendingCount} processedCount={processedCount} />
            <BatchAnnotationRunItemsPanel
              run={run}
              pendingCount={pendingCount}
              items={items}
              loading={itemsLoading}
              page={itemsPage}
              total={itemsTotal}
              status={itemStatus}
              searchInput={searchInput}
              appliedKeyword={itemKeyword}
              onStatusChange={setItemStatus}
              onSearchInputChange={setSearchInput}
              onSearch={(keyword) => setItemKeyword(keyword.trim())}
              onPageChange={handlePageChange}
              onSelectItem={setSelectedItem}
            />
          </main>
        </div>
      </div>

      <Drawer title="运行日志" width="min(620px, 100vw)" open={logDrawerOpen} onClose={() => setLogDrawerOpen(false)}>
        {events.length === 0 ? <Empty description="暂无运行日志" /> : (
          <Table<AiPipelineBatchRunEvent>
            rowKey="id"
            size="small"
            pagination={{ pageSize: 10, showSizeChanger: false }}
            dataSource={events.slice().reverse()}
            scroll={{ x: 520 }}
            columns={[
              { title: '时间', dataIndex: 'created_at', width: 170, render: formatDateTime },
              { title: '类型', dataIndex: 'event_type', width: 110, render: (value) => batchRunEventTitles[value] ?? value },
              { title: '内容', render: (_, event) => getBatchRunEventText(event) },
            ]}
          />
        )}
      </Drawer>

      <Drawer
        title={selectedItem?.status === 'failed' ? '样本失败详情' : '样本标注结果'}
        width="min(620px, 100vw)"
        open={selectedItem !== null}
        onClose={() => setSelectedItem(null)}
      >
        {selectedItem ? (
          <>
            {selectedItem.error_message ? <Alert className="mb-5" type="error" showIcon message={selectedItem.error_message} /> : null}
            <Descriptions
              size="small"
              column={1}
              items={[
                { key: 'file', label: '文件名', children: selectedItem.item_key },
                { key: 'status', label: '状态', children: batchRunStatusLabels[selectedItem.status] ?? selectedItem.status },
                { key: 'record', label: '标注记录', children: selectedItem.annotation_record_id ? `#${selectedItem.annotation_record_id}` : '-' },
                { key: 'time', label: '完成时间', children: formatClock(selectedItem.finished_at) },
              ]}
            />
            {selectedItem.result ? (
              <pre className="mt-5 max-h-[60vh] overflow-auto rounded-[6px] bg-gray-950 p-4 text-xs leading-5 text-gray-100">{JSON.stringify(selectedItem.result, null, 2)}</pre>
            ) : null}
          </>
        ) : null}
      </Drawer>
      </div>
    </ConfigProvider>
  );
};

export default BatchAnnotationRunDetailPage;
