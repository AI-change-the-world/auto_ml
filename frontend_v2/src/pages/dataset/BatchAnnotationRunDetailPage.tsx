import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  CloseOutlined,
  PlayCircleOutlined,
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
  createIncrementalBatchAnnotationRun,
  getBatchAnnotationRun,
  getBatchAnnotationRunEvents,
  getBatchAnnotationRunIncrementalStatus,
  getBatchAnnotationRunItems,
  resumeBatchAnnotationRun,
} from '../../api/batchAnnotation';
import { getAnnotation } from '../../api/annotation';
import { subscribeBatchAnnotationRunStream } from '../../api/batchAnnotationStream';
import type {
  AiPipelineBatchRunDetail,
  AiPipelineBatchRunEvent,
  AiPipelineBatchRunItem,
} from '../../types';
import { emitBatchAnnotationRunsChanged } from '../../utils/projectEvents';
import { parseAnnotationClasses } from '../../utils/annotationClasses';
import {
  BatchAnnotationRunInfo,
  BatchAnnotationRunOverview,
  BatchAnnotationRunResults,
  BatchAnnotationRunTimeline,
} from './components/BatchAnnotationRunOverview';
import { BatchAnnotationRunItemsPanel } from './components/BatchAnnotationRunItemsPanel';
import { BatchAnnotationResultPreview } from './components/BatchAnnotationResultPreview';
import {
  activeBatchRunStatuses,
  appendProgressPointFromEvent,
  batchRunErrorSourceLabels,
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
  const navigate = useNavigate();
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
  const [resuming, setResuming] = React.useState(false);
  const [incrementalCount, setIncrementalCount] = React.useState(0);
  const [startingIncremental, setStartingIncremental] = React.useState(false);
  const [logDrawerOpen, setLogDrawerOpen] = React.useState(false);
  const [selectedItem, setSelectedItem] = React.useState<AiPipelineBatchRunItem | null>(null);
  const [annotationClassNames, setAnnotationClassNames] = React.useState<string[]>([]);
  const lastEventIdRef = React.useRef(0);
  const itemsPageRef = React.useRef(1);
  const streamRefreshTimerRef = React.useRef<number | null>(null);
  const runRequestVersionRef = React.useRef(0);
  const missingRunHandledRef = React.useRef(false);
  const hasLoadedRun = run !== null;
  const latestResultEventId = React.useMemo(
    () => events.filter((event) => event.event_type === 'result').at(-1)?.id,
    [events],
  );

  const handleMissingRun = React.useCallback((error: unknown) => {
    if (!(error instanceof Error) || !error.message.startsWith('Batch run ')) return false;
    if (!missingRunHandledRef.current) {
      missingRunHandledRef.current = true;
      navigate('/batch-annotation/runs', { replace: true });
    }
    return true;
  }, [navigate]);

  const syncRun = React.useCallback(async () => {
    if (!runId) return;
    const requestVersion = ++runRequestVersionRef.current;
    try {
      const nextRun = await getBatchAnnotationRun(runId);
      if (nextRun && requestVersion === runRequestVersionRef.current) setRun(nextRun);
    } catch (error) {
      handleMissingRun(error);
    }
  }, [handleMissingRun, runId]);

  const loadRun = React.useCallback(async (initial = false) => {
    if (!runId) return;
    if (initial) setLoading(true);
    else setRefreshing(true);
    const requestVersion = ++runRequestVersionRef.current;
    try {
      const nextRun = await getBatchAnnotationRun(runId);
      if (!nextRun) throw new Error('任务不存在');
      const nextEvents = await getBatchAnnotationRunEvents(runId, initial ? 0 : lastEventIdRef.current, true);
      if (requestVersion !== runRequestVersionRef.current) return;
      setRun(nextRun);
      setEvents((current) => mergeBatchRunEvents(current, nextEvents));
      if (nextEvents.length > 0) {
        lastEventIdRef.current = Math.max(lastEventIdRef.current, nextEvents[nextEvents.length - 1].id);
      }
    } catch (error) {
      if (handleMissingRun(error)) return;
      if (initial) message.error(error instanceof Error ? error.message : '加载批量标注任务失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [handleMissingRun, runId]);

  const loadItems = React.useCallback(async (page = itemsPageRef.current) => {
    if (!runId || !hasLoadedRun) return;
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
    } catch (error) {
      if (!handleMissingRun(error)) message.error('加载样本结果失败');
    } finally {
      setItemsLoading(false);
    }
  }, [handleMissingRun, hasLoadedRun, itemKeyword, itemStatus, runId]);

  const loadItemsRef = React.useRef(loadItems);
  React.useEffect(() => {
    loadItemsRef.current = loadItems;
  }, [loadItems]);

  const loadIncrementalStatus = React.useCallback(async () => {
    if (!run || activeBatchRunStatuses.has(run.status)) {
      setIncrementalCount(0);
      return;
    }
    try {
      const status = await getBatchAnnotationRunIncrementalStatus(run.run_id);
      setIncrementalCount(status?.incremental_count ?? 0);
    } catch (error) {
      if (!handleMissingRun(error)) setIncrementalCount(0);
    }
  }, [handleMissingRun, run?.run_id, run?.status]);

  React.useEffect(() => {
    lastEventIdRef.current = 0;
    missingRunHandledRef.current = false;
    itemsPageRef.current = 1;
    setItemsPage(1);
    setEvents([]);
    void loadRun(true);
  }, [loadRun]);

  React.useEffect(() => {
    let disposed = false;
    const annotationId = run?.annotation_id;
    if (!annotationId) {
      setAnnotationClassNames([]);
      return () => {
        disposed = true;
      };
    }

    void getAnnotation(annotationId)
      .then((annotation) => {
        if (!disposed) setAnnotationClassNames(parseAnnotationClasses(annotation?.classes));
      })
      .catch(() => {
        if (!disposed) setAnnotationClassNames([]);
      });

    return () => {
      disposed = true;
    };
  }, [run?.annotation_id]);

  React.useEffect(() => {
    itemsPageRef.current = 1;
    setItemsPage(1);
    void loadItems(1);
  }, [loadItems]);

  React.useEffect(() => {
    void loadIncrementalStatus();
  }, [loadIncrementalStatus]);

  React.useEffect(() => {
    if (!runId || !hasLoadedRun) return;
    return subscribeBatchAnnotationRunStream(runId, {
      onEvent: ({ data }) => {
        runRequestVersionRef.current += 1;
        setRun((current) => current ? {
          ...current,
          ...data.run,
          progress_points: appendProgressPointFromEvent(current.progress_points, data.event),
        } : current);
        lastEventIdRef.current = Math.max(lastEventIdRef.current, data.event.id);
        setEvents((current) => mergeBatchRunEvents(current, [data.event]));
        void loadItemsRef.current();
        emitBatchAnnotationRunsChanged();
        if (streamRefreshTimerRef.current !== null) window.clearTimeout(streamRefreshTimerRef.current);
        streamRefreshTimerRef.current = window.setTimeout(() => {
          void syncRun();
          streamRefreshTimerRef.current = null;
        }, 100);
      },
    });
  }, [hasLoadedRun, runId, syncRun]);

  React.useEffect(() => () => {
    if (streamRefreshTimerRef.current !== null) window.clearTimeout(streamRefreshTimerRef.current);
  }, []);

  React.useEffect(() => {
    if (!run || !activeBatchRunStatuses.has(run.status)) return;
    const clockTimer = window.setInterval(() => setRun((current) => current ? { ...current } : current), 1000);
    const syncTimer = window.setInterval(() => {
      void syncRun();
      void loadItemsRef.current();
    }, 2000);
    return () => {
      window.clearInterval(clockTimer);
      window.clearInterval(syncTimer);
    };
  }, [run?.status, syncRun]);

  const handleRefresh = async () => {
    await Promise.all([loadRun(), loadItems(), loadIncrementalStatus()]);
  };

  const handleCancel = async () => {
    if (!run) return;
    setCanceling(true);
    try {
      const nextRun = await cancelBatchAnnotationRun(run.run_id);
      if (nextRun) setRun((current) => current ? { ...current, ...nextRun } : current);
      emitBatchAnnotationRunsChanged();
      message.success('任务已取消，已完成的标注会保留');
      await Promise.all([loadRun(), loadItems(), loadIncrementalStatus()]);
    } catch {
      message.error('取消任务失败');
    } finally {
      setCanceling(false);
    }
  };

  const handleResume = async () => {
    if (!run) return;
    setResuming(true);
    try {
      const nextRun = await resumeBatchAnnotationRun(run.run_id);
      if (nextRun) setRun((current) => current ? { ...current, ...nextRun } : current);
      emitBatchAnnotationRunsChanged();
      if (nextRun?.status === 'failed') {
        message.error(nextRun.error_message ?? '重新派发失败，请查看任务事件和服务端日志');
      } else {
        message.success(run.status === 'queued' ? '任务已重新派发，等待执行端处理' : '失败样本已重新派发，等待执行端处理');
      }
      await Promise.all([loadRun(), loadItems(), loadIncrementalStatus()]);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '重新派发任务失败');
    } finally {
      setResuming(false);
    }
  };

  const handleStartIncremental = async () => {
    if (!run) return;
    setStartingIncremental(true);
    try {
      const nextRun = await createIncrementalBatchAnnotationRun(run.run_id);
      if (!nextRun) throw new Error('创建增量任务失败');
      emitBatchAnnotationRunsChanged();
      message.success(`已创建增量任务，处理 ${incrementalCount} 个新增样本`);
      navigate(`/batch-annotation/runs/${nextRun.run_id}`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '创建增量任务失败');
      await loadIncrementalStatus();
    } finally {
      setStartingIncremental(false);
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
  const completedCount = run.total_count - pendingCount;
  const processedCount = Math.min(
    run.total_count,
    Math.max(completedCount, Math.round((run.progress / 100) * run.total_count)),
  );

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
            {!activeBatchRunStatuses.has(run.status) && incrementalCount > 0 ? (
              <Button type="primary" icon={<PlayCircleOutlined />} loading={startingIncremental} onClick={() => void handleStartIncremental()}>
                处理新增 {incrementalCount} 个样本
              </Button>
            ) : null}
            {run.status === 'queued' || (
              ['failed', 'succeeded'].includes(run.status) && run.failed_count > 0
            ) ? (
              <Button type="primary" icon={<PlayCircleOutlined />} loading={resuming} onClick={() => void handleResume()}>
                {run.status === 'queued' ? '继续执行' : '重试失败项'}
              </Button>
            ) : null}
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
              {
                title: '内容',
                render: (_, event) => getBatchRunEventText(
                  event,
                  event.id === latestResultEventId ? run : undefined,
                ),
              },
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
            {selectedItem.error_message ? (
              <Alert
                className="mb-5"
                type="error"
                showIcon
                message={selectedItem.error_detail ? (batchRunErrorSourceLabels[selectedItem.error_detail.source] ?? selectedItem.error_detail.source) : '样本处理失败'}
                description={selectedItem.error_message}
              />
            ) : null}
            <Descriptions
              size="small"
              column={1}
              items={[
                { key: 'file', label: '文件名', children: selectedItem.item_key },
                { key: 'status', label: '状态', children: batchRunStatusLabels[selectedItem.status] ?? selectedItem.status },
                { key: 'record', label: '标注记录', children: selectedItem.annotation_record_id ? `#${selectedItem.annotation_record_id}` : '-' },
                { key: 'time', label: '完成时间', children: formatClock(selectedItem.finished_at) },
                ...(selectedItem.status === 'failed' ? [
                  { key: 'source', label: '错误来源', children: selectedItem.error_detail ? (batchRunErrorSourceLabels[selectedItem.error_detail.source] ?? selectedItem.error_detail.source) : '-' },
                  { key: 'stage', label: '失败阶段', children: selectedItem.error_detail?.stage ?? '-' },
                  { key: 'http', label: 'HTTP 状态', children: selectedItem.error_detail?.http_status ?? '-' },
                  { key: 'type', label: '异常类型', children: selectedItem.error_detail?.exception_type ?? '-' },
                  { key: 'request', label: '请求标识', children: selectedItem.error_detail?.request_id ?? '-' },
                ] : []),
              ]}
            />
            {selectedItem.status === 'succeeded' ? (
              <BatchAnnotationResultPreview
                datasetId={run.dataset_id}
                item={selectedItem}
                classNames={annotationClassNames}
              />
            ) : null}
            {selectedItem.error_detail?.traceback ? (
              <pre className="mt-5 max-h-[40vh] overflow-auto rounded-[6px] bg-gray-950 p-4 text-xs leading-5 text-gray-100">{selectedItem.error_detail.traceback}</pre>
            ) : null}
            {selectedItem.status !== 'succeeded' && selectedItem.result ? (
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
