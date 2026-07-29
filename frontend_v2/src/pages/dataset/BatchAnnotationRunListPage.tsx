import React from 'react';
import { useNavigate } from 'react-router-dom';
import { DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { Button, Empty, Popconfirm, Progress, Select, Spin, Table, Tag, Tooltip, Typography, message } from 'antd';
import { deleteBatchAnnotationRun, listBatchAnnotationRuns } from '../../api/batchAnnotation';
import type { AiPipelineBatchRun } from '../../types';
import { BATCH_ANNOTATION_RUNS_CHANGED_EVENT, emitBatchAnnotationRunsChanged } from '../../utils/projectEvents';

const { Text } = Typography;
const activeStatuses = new Set(['queued', 'running']);

const statusTag = (status: string) => {
  const colorMap: Record<string, string> = { queued: 'default', running: 'processing', succeeded: 'success', failed: 'error', canceled: 'warning' };
  const labelMap: Record<string, string> = { queued: '等待执行', running: '执行中', succeeded: '已完成', failed: '失败', canceled: '已取消' };
  return <Tag color={colorMap[status] ?? 'default'}>{labelMap[status] ?? status}</Tag>;
};

const formatTime = (value?: string | null) => value ? new Date(value).toLocaleString() : '-';

const BatchAnnotationRunListPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [runs, setRuns] = React.useState<AiPipelineBatchRun[]>([]);
  const [statusFilter, setStatusFilter] = React.useState<string | undefined>();
  const [deletingRunId, setDeletingRunId] = React.useState<string>();

  const loadRuns = React.useCallback(async (initial = false) => {
    if (initial) setLoading(true);
    else setRefreshing(true);
    try {
      setRuns(await listBatchAnnotationRuns(undefined, 100));
    } catch {
      message.error('加载批量标注任务失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  React.useEffect(() => { void loadRuns(true); }, [loadRuns]);

  React.useEffect(() => {
    const refresh = () => { void loadRuns(); };
    window.addEventListener(BATCH_ANNOTATION_RUNS_CHANGED_EVENT, refresh);
    return () => window.removeEventListener(BATCH_ANNOTATION_RUNS_CHANGED_EVENT, refresh);
  }, [loadRuns]);

  React.useEffect(() => {
    if (!runs.some((run) => activeStatuses.has(run.status))) return;
    const timer = window.setInterval(() => { void loadRuns(); }, 2000);
    return () => window.clearInterval(timer);
  }, [loadRuns, runs]);

  const visibleRuns = React.useMemo(() => runs.filter((run) => (
    statusFilter === undefined || run.status === statusFilter
  )), [runs, statusFilter]);

  const handleDelete = async (run: AiPipelineBatchRun) => {
    if (deletingRunId) return;
    setDeletingRunId(run.run_id);
    try {
      await deleteBatchAnnotationRun(run.run_id);
      setRuns((current) => current.filter((item) => item.run_id !== run.run_id));
      emitBatchAnnotationRunsChanged();
      navigate('/batch-annotation/runs', { replace: true });
      message.success('批量标注任务已删除');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除批量标注任务失败');
    } finally {
      setDeletingRunId(undefined);
    }
  };

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, marginBottom: 18 }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>批量标注任务</h1>
          <Text type="secondary">查看运行进度、样本结果和异常信息</Text>
        </div>
        <Button icon={<ReloadOutlined />} loading={refreshing} onClick={() => void loadRuns()}>刷新</Button>
      </div>

      <Select
        allowClear
        value={statusFilter}
        placeholder="全部状态"
        style={{ width: 180, marginBottom: 14 }}
        onChange={setStatusFilter}
        options={[
          { label: '等待执行', value: 'queued' },
          { label: '执行中', value: 'running' },
          { label: '已完成', value: 'succeeded' },
          { label: '失败', value: 'failed' },
          { label: '已取消', value: 'canceled' },
        ]}
      />

      {loading ? <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}><Spin /></div> : visibleRuns.length === 0 ? <Empty description="暂无批量标注任务" /> : (
        <Table<AiPipelineBatchRun>
          rowKey="run_id"
          size="small"
          dataSource={visibleRuns}
          pagination={{ pageSize: 20, showSizeChanger: false }}
          onRow={(run) => ({
            onClick: (event) => {
              if ((event.target as HTMLElement).closest('[data-batch-run-action]')) return;
              navigate(`/batch-annotation/runs/${run.run_id}`);
            },
            style: { cursor: 'pointer' },
          })}
          columns={[
            { title: '工具', dataIndex: 'script_key', ellipsis: true },
            { title: '数据集', width: 105, render: (_, run) => `#${run.dataset_id}` },
            { title: '标注项目', width: 115, render: (_, run) => `#${run.annotation_id}` },
            { title: '状态', dataIndex: 'status', width: 105, render: statusTag },
            { title: '进度', width: 180, render: (_, run) => <Progress percent={run.progress} size="small" status={run.status === 'failed' ? 'exception' : 'normal'} /> },
            { title: '结果', width: 180, render: (_, run) => `${run.succeeded_count} 成功 / ${run.failed_count} 失败 / ${run.skipped_count} 跳过` },
            { title: '创建时间', dataIndex: 'created_at', width: 180, render: formatTime },
            {
              title: '',
              width: 56,
              onCell: () => ({ onClick: (event) => event.stopPropagation() }),
              render: (_, run) => (
                <span data-batch-run-action>
                  {activeStatuses.has(run.status) ? (
                    <Tooltip title="请先取消任务">
                      <Button aria-label="删除任务" type="text" danger icon={<DeleteOutlined />} disabled />
                    </Tooltip>
                  ) : (
                    <Popconfirm
                      title="删除批量标注任务？"
                      description="删除后将不再显示该任务及其运行记录。"
                      okText="删除"
                      okButtonProps={{ danger: true, loading: deletingRunId === run.run_id }}
                      cancelText="取消"
                      onConfirm={() => void handleDelete(run)}
                    >
                      <Tooltip title="删除任务">
                        <Button
                          aria-label="删除任务"
                          type="text"
                          danger
                          icon={<DeleteOutlined />}
                          loading={deletingRunId === run.run_id}
                          onClick={(event) => event.stopPropagation()}
                        />
                      </Tooltip>
                    </Popconfirm>
                  )}
                </span>
              ),
            },
          ]}
        />
      )}
    </div>
  );
};

export default BatchAnnotationRunListPage;
