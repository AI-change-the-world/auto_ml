import React from 'react';
import {
  CheckCircleFilled,
  ClockCircleOutlined,
  CloseCircleFilled,
  FilterOutlined,
  SearchOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { Button, Empty, Input, Pagination, Table, Tooltip } from 'antd';
import type { AiPipelineBatchRunDetail, AiPipelineBatchRunItem } from '../../../types';
import {
  batchRunItemPageSize,
  batchRunStatusLabels,
  formatClock,
  formatNumber,
  getItemDuration,
} from './batchAnnotationRunDetailUtils';

const itemStatus = (status: string) => {
  if (status === 'succeeded') return <span className="flex items-center text-green-500"><CheckCircleFilled className="mr-1" />成功</span>;
  if (status === 'failed') return <span className="flex items-center text-red-500"><CloseCircleFilled className="mr-1" />失败</span>;
  if (status === 'running') return <span className="flex items-center text-blue-500"><SyncOutlined spin className="mr-1" />处理中</span>;
  if (status === 'skipped') return <span className="flex items-center text-yellow-600"><ClockCircleOutlined className="mr-1" />已跳过</span>;
  if (status === 'canceled') return <span className="flex items-center text-orange-500"><CloseCircleFilled className="mr-1" />已取消</span>;
  return <span className="flex items-center text-gray-400"><ClockCircleOutlined className="mr-1" />{batchRunStatusLabels[status] ?? '待处理'}</span>;
};

interface BatchAnnotationRunItemsPanelProps {
  run: AiPipelineBatchRunDetail;
  pendingCount: number;
  items: AiPipelineBatchRunItem[];
  loading: boolean;
  page: number;
  total: number;
  status?: string;
  searchInput: string;
  appliedKeyword: string;
  onStatusChange: (status?: string) => void;
  onSearchInputChange: (value: string) => void;
  onSearch: (value: string) => void;
  onPageChange: (page: number) => void;
  onSelectItem: (item: AiPipelineBatchRunItem) => void;
}

export const BatchAnnotationRunItemsPanel: React.FC<BatchAnnotationRunItemsPanelProps> = ({
  run,
  pendingCount,
  items,
  loading,
  page,
  total,
  status,
  searchInput,
  appliedKeyword,
  onStatusChange,
  onSearchInputChange,
  onSearch,
  onPageChange,
  onSelectItem,
}) => {
  const tabs = [
    { key: 'all', label: '全部', count: run.total_count, countClass: 'text-blue-500' },
    { key: 'succeeded', label: '成功', count: run.succeeded_count, countClass: 'bg-green-50 text-green-500' },
    { key: 'failed', label: '失败', count: run.failed_count, countClass: 'bg-red-50 text-red-500' },
    { key: 'pending', label: '待处理', count: pendingCount, countClass: 'bg-gray-100 text-gray-500' },
    { key: 'skipped', label: '已跳过', count: run.skipped_count, countClass: 'bg-yellow-50 text-yellow-600' },
    { key: 'canceled', label: '已取消', count: run.canceled_count, countClass: 'bg-orange-50 text-orange-500' },
  ];
  const activeKey = status ?? 'all';
  const hasFilters = Boolean(status || appliedKeyword || searchInput);

  return (
    <section className="min-w-0 rounded-[6px] border-0 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="mb-4 text-base font-bold text-gray-900">样本处理列表</h2>
      <div className="mb-4 flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
        <div className="flex min-w-0 gap-6 overflow-x-auto text-sm">
          {tabs.map((tab) => {
            const active = activeKey === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                aria-pressed={active}
                className={`shrink-0 border-b-2 pb-2 ${active ? 'border-blue-500 font-medium text-blue-500' : 'border-transparent text-gray-600 hover:text-gray-800'}`}
                onClick={() => onStatusChange(tab.key === 'all' ? undefined : tab.key)}
              >
                {tab.label} <span className={`ml-1 rounded px-1 ${tab.countClass}`}>{formatNumber(tab.count)}</span>
              </button>
            );
          })}
        </div>
        <div className="flex shrink-0 gap-2">
          <Input
            allowClear
            aria-label="搜索文件名"
            className="w-full sm:w-52"
            placeholder="搜索文件名"
            prefix={<SearchOutlined className="text-gray-400" />}
            value={searchInput}
            onChange={(event) => {
              onSearchInputChange(event.target.value);
              if (!event.target.value) onSearch('');
            }}
            onPressEnter={() => onSearch(searchInput.trim())}
          />
          <Tooltip title="清除筛选">
            <Button
              aria-label="清除筛选"
              disabled={!hasFilters}
              icon={<FilterOutlined />}
              onClick={() => {
                onSearchInputChange('');
                onSearch('');
                onStatusChange(undefined);
              }}
            />
          </Tooltip>
        </div>
      </div>

      <Table<AiPipelineBatchRunItem>
        className="[&_.ant-table-thead>tr>th]:bg-gray-50 [&_.ant-table-thead>tr>th]:text-gray-600 [&_.ant-table-tbody>tr>td]:text-gray-600"
        rowKey="id"
        size="middle"
        loading={loading}
        dataSource={items}
        pagination={false}
        scroll={{ x: 820 }}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无样本结果" /> }}
        columns={[
          { title: '文件名', dataIndex: 'item_key', ellipsis: true, render: (value) => <span className="text-gray-800">{value}</span> },
          { title: '状态', dataIndex: 'status', width: 110, render: itemStatus },
          { title: '处理耗时', width: 110, render: (_, item) => getItemDuration(item) },
          { title: '错误信息', dataIndex: 'error_message', ellipsis: true, render: (value) => value || '-' },
          { title: '完成时间', dataIndex: 'finished_at', width: 110, render: formatClock },
          {
            title: '',
            width: 90,
            render: (_, item) => ['pending', 'queued', 'running'].includes(item.status) ? null : (
              <Button className="text-blue-500" type="link" size="small" onClick={() => onSelectItem(item)}>{item.status === 'failed' ? '查看详情' : '查看结果'}</Button>
            ),
          },
        ]}
      />

      {total > 0 ? (
        <div className="mt-4 flex flex-col gap-3 text-sm text-gray-500 sm:flex-row sm:items-center sm:justify-between">
          <span>共 {formatNumber(total)} 条，每页 {batchRunItemPageSize} 条</span>
          <Pagination
            size="small"
            responsive
            showQuickJumper
            showSizeChanger={false}
            current={page}
            pageSize={batchRunItemPageSize}
            total={total}
            onChange={onPageChange}
          />
        </div>
      ) : null}
    </section>
  );
};
