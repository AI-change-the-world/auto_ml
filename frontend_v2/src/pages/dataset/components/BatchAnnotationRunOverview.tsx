import React from 'react';
import { Link } from 'react-router-dom';
import {
  PlayCircleFilled,
  SyncOutlined,
} from '@ant-design/icons';
import { Alert, Button, Empty, Progress, Steps, Tag } from 'antd';
import type { AiPipelineBatchRunDetail, AiPipelineBatchRunEvent } from '../../../types';
import {
  activeBatchRunStatuses,
  batchRunEventTitles,
  batchRunStatusLabels,
  buildProcessingRatePoints,
  formatClock,
  formatDateTime,
  formatDuration,
  formatNumber,
  getBatchRunEventText,
} from './batchAnnotationRunDetailUtils';

const panelClassName = 'rounded-[6px] border-0 bg-white shadow-sm';

const statusClassNames: Record<string, string> = {
  queued: 'border-blue-200 bg-blue-50 text-blue-500',
  running: 'border-blue-200 bg-blue-50 text-blue-500',
  succeeded: 'border-green-200 bg-green-50 text-green-500',
  failed: 'border-red-200 bg-red-50 text-red-500',
  canceled: 'border-orange-200 bg-orange-50 text-orange-500',
};

export const BatchRunStatusTag: React.FC<{ status: string; compact?: boolean }> = ({ status, compact = false }) => (
  <Tag className={`m-0 ${compact ? 'rounded-[4px] border-0 px-2' : 'rounded-[6px] px-3 py-0.5'} ${statusClassNames[status] ?? statusClassNames.queued}`}>
    {activeBatchRunStatuses.has(status) ? <SyncOutlined spin className="mr-1" /> : null}
    {batchRunStatusLabels[status] ?? status}
  </Tag>
);

const getRunDurationText = (run: AiPipelineBatchRunDetail) => {
  if (run.status === 'queued') {
    return `已等待 ${formatDuration(run.created_at)}`;
  }
  if (run.started_at) {
    return `${activeBatchRunStatuses.has(run.status) ? '已运行' : '运行时长'} ${formatDuration(run.started_at, run.finished_at)}`;
  }
  return '-';
};

interface RunOverviewProps {
  run: AiPipelineBatchRunDetail;
  pendingCount: number;
  processedCount: number;
}

export const BatchAnnotationRunOverview: React.FC<RunOverviewProps> = ({ run, pendingCount, processedCount }) => {
  const metadata = [
    { label: '创建时间', value: formatDateTime(run.created_at) },
    { label: '开始时间', value: formatDateTime(run.started_at) },
    { label: '标注项目', value: run.annotation_name || `标注项目 #${run.annotation_id}` },
    { label: '数据集', value: run.dataset_name || `数据集 #${run.dataset_id}`, link: `/datasets/${run.dataset_id}` },
    { label: 'AI 流程', value: `${run.script_name || run.script_key} v${run.script_version}` },
    { label: '描述', value: run.script_description || '-' },
  ];
  const metrics = [
    { label: '总样本数', value: run.total_count, color: 'text-gray-800' },
    { label: '已完成', value: run.succeeded_count, color: 'text-green-500' },
    { label: '失败', value: run.failed_count, color: 'text-red-500' },
    { label: '待处理', value: pendingCount, color: 'text-gray-800' },
  ];

  return (
    <section className={`${panelClassName} p-5 sm:p-6`}>
      <div className="flex min-w-0 items-start gap-4">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-[6px] bg-blue-100 text-3xl text-blue-500">
          <PlayCircleFilled />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
            <h2 className="text-xl font-bold text-gray-900">批量标注任务 #{run.id}</h2>
            <BatchRunStatusTag status={run.status} />
            <span className="ml-1 text-sm text-gray-400">{getRunDurationText(run)}</span>
          </div>
          <div className="mt-5 grid grid-cols-2 gap-x-4 gap-y-4 text-sm md:grid-cols-3 xl:grid-cols-6">
            {metadata.map((item) => (
              <div key={item.label} className="min-w-0">
                <div className="mb-1 text-gray-500">{item.label}</div>
                {item.link ? (
                  <Link className="line-clamp-2 text-blue-500 hover:text-blue-600" to={item.link}>{item.value}</Link>
                ) : (
                  <div className="line-clamp-2 text-gray-800" title={item.value}>{item.value}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 flex flex-col gap-6 border-t border-gray-100 pt-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="w-full lg:w-1/2">
          <div className="mb-1.5 flex items-center justify-between text-sm">
            <span className="font-medium text-gray-800">总体进度</span>
            <span className="font-medium text-blue-500">{run.progress.toFixed(1)}%</span>
          </div>
          <Progress
            className="m-0"
            percent={run.progress}
            showInfo={false}
            status={run.status === 'failed' ? 'exception' : 'normal'}
            strokeColor="#3b82f6"
            trailColor="#f1f5f9"
          />
          <div className="mt-1 text-xs text-gray-400">已处理 {formatNumber(processedCount)} / {formatNumber(run.total_count)}</div>
        </div>
        <div className="grid grid-cols-2 gap-x-8 gap-y-5 sm:grid-cols-4 lg:gap-x-12">
          {metrics.map((metric) => (
            <div key={metric.label} className="text-center">
              <div className="mb-1 text-sm text-gray-500">{metric.label}</div>
              <div className={`text-2xl font-bold ${metric.color}`}>{formatNumber(metric.value)}</div>
            </div>
          ))}
        </div>
      </div>
      {run.error_message ? <Alert className="mt-5" type="error" showIcon message={run.error_message} /> : null}
    </section>
  );
};

interface RunTimelineProps {
  run: AiPipelineBatchRunDetail;
  events: AiPipelineBatchRunEvent[];
  onShowAll: () => void;
}

export const BatchAnnotationRunTimeline: React.FC<RunTimelineProps> = ({ run, events, onShowAll }) => {
  const visibleEvents = events.slice(-5);
  const latestResultEventId = events.filter((event) => event.event_type === 'result').at(-1)?.id;
  return (
    <section className={`${panelClassName} p-5`}>
      <h2 className="mb-5 text-base font-bold text-gray-900">运行状态</h2>
      {visibleEvents.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无运行日志" />
      ) : (
        <Steps
          direction="vertical"
          size="small"
          items={visibleEvents.map((event, index) => {
            const isLatest = index === visibleEvents.length - 1;
            const isError = isLatest && run.status === 'failed';
            const isProcessing = isLatest && activeBatchRunStatuses.has(run.status);
            return {
              status: isError ? 'error' : isProcessing ? 'process' : 'finish',
              title: (
                <div className="flex min-w-0 items-center justify-between gap-3 text-sm">
                  <span className={isProcessing ? 'truncate font-medium text-blue-500' : 'truncate text-gray-800'}>{batchRunEventTitles[event.event_type] ?? event.event_type}</span>
                  <span className="shrink-0 text-xs font-normal text-gray-400">{formatClock(event.created_at)}</span>
                </div>
              ),
              description: <span className="text-xs text-gray-500">{getBatchRunEventText(event, event.id === latestResultEventId ? run : undefined)}</span>,
            };
          })}
        />
      )}
      <Button block className="mt-3 border-gray-200 text-blue-500" onClick={onShowAll}>查看全部日志</Button>
    </section>
  );
};

export const BatchAnnotationRunInfo: React.FC<{ run: AiPipelineBatchRunDetail; className?: string }> = ({ run, className }) => {
  const items = [
    { label: '运行 ID', value: run.run_id },
    { label: '状态', value: <BatchRunStatusTag status={run.status} compact /> },
    { label: '标注项目', value: run.annotation_name || `#${run.annotation_id}` },
    { label: '并发数', value: run.parallelism },
    { label: '批次大小', value: run.batch_size },
    { label: '已有标注处理', value: run.overwrite_policy === 'overwrite_all' ? '覆盖全部' : run.overwrite_policy === 'overwrite_draft' ? '仅覆盖草稿' : '跳过已有结果' },
  ];
  return (
    <section className={`${panelClassName} p-5 ${className ?? ''}`}>
      <h2 className="mb-3 text-base font-bold text-gray-900">任务信息</h2>
      <div className="divide-y divide-gray-100 text-sm">
        {items.map((item) => (
          <div key={item.label} className="flex min-w-0 items-center justify-between gap-4 py-3">
            <span className="shrink-0 text-gray-500">{item.label}</span>
            <span className="min-w-0 truncate text-right text-gray-800" title={typeof item.value === 'string' ? item.value : undefined}>{item.value}</span>
          </div>
        ))}
      </div>
    </section>
  );
};

const ResultDonut: React.FC<{ run: AiPipelineBatchRunDetail; pendingCount: number }> = ({ run, pendingCount }) => {
  const values = [
    { value: run.succeeded_count, color: '#4ade80' },
    { value: run.failed_count, color: '#ef4444' },
    { value: pendingCount, color: '#d1d5db' },
    { value: run.skipped_count, color: '#f59e0b' },
    { value: run.canceled_count, color: '#f97316' },
  ];
  let offset = 0;
  return (
    <div className="relative h-36 w-36 shrink-0">
      <svg className="h-full w-full" viewBox="0 0 144 144" aria-hidden="true">
        <circle cx="72" cy="72" r="54" fill="none" stroke="#f1f5f9" strokeWidth="12" />
        {run.total_count > 0 ? values.map((item, index) => {
          const percent = (item.value / run.total_count) * 100;
          const dashOffset = offset;
          offset += percent;
          return (
            <circle
              key={index}
              cx="72"
              cy="72"
              r="54"
              pathLength="100"
              fill="none"
              stroke={item.color}
              strokeWidth="12"
              strokeDasharray={`${percent} ${100 - percent}`}
              strokeDashoffset={-dashOffset}
              transform="rotate(-90 72 72)"
            />
          );
        }) : null}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <strong className="text-2xl font-bold text-gray-800">{formatNumber(run.total_count)}</strong>
        <span className="text-xs text-gray-500">总样本数</span>
      </div>
    </div>
  );
};

const ProcessingSpeedChart: React.FC<{ run: AiPipelineBatchRunDetail }> = ({ run }) => {
  const points = buildProcessingRatePoints(run.progress_points, run.total_count);
  const currentRate = points.at(-1)?.rate;
  const scaleMax = Math.max(30, Math.ceil(Math.max(...points.map((point) => point.rate), 0) / 30) * 30);
  const left = 38;
  const top = 8;
  const width = 312;
  const height = 92;
  const coordinates = points.map((point, index) => ({
    ...point,
    x: points.length === 1 ? left + width / 2 : left + (index / (points.length - 1)) * width,
    y: top + height - (point.rate / scaleMax) * height,
  }));
  const linePath = coordinates.map((point, index) => `${index === 0 ? 'M' : 'L'}${point.x},${point.y}`).join(' ');
  const areaPath = coordinates.length > 0 ? `${linePath} L${coordinates.at(-1)?.x},${top + height} L${coordinates[0].x},${top + height} Z` : '';
  const gridValues = [scaleMax, Math.round(scaleMax * 2 / 3), Math.round(scaleMax / 3), 0];
  const labelIndexes = Array.from(new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])).filter((index) => index >= 0);

  return (
    <div className="min-w-0 lg:border-l lg:border-gray-100 lg:pl-6">
      <div className="mb-2 flex items-start justify-between gap-4">
        <span className="text-sm text-gray-600">处理速度（样本/分钟）</span>
        <span className="shrink-0 text-right text-xs text-gray-400">当前速度<br /><strong className="text-sm font-bold text-blue-500">{currentRate ?? '-'} 样本/分钟</strong></span>
      </div>
      {coordinates.length > 0 ? (
        <svg viewBox="0 0 360 126" className="h-32 w-full" role="img" aria-label="任务处理速度曲线">
          {gridValues.map((value, index) => {
            const y = top + (index / (gridValues.length - 1)) * height;
            return (
              <g key={value}>
                <line x1={left} x2={left + width} y1={y} y2={y} stroke="#e5e7eb" strokeWidth="1" />
                <text x="0" y={y + 3} fill="#9ca3af" fontSize="10">{value}</text>
              </g>
            );
          })}
          <path d={areaPath} fill="#eff6ff" opacity="0.9" />
          <path d={linePath} fill="none" stroke="#3b82f6" strokeWidth="2" vectorEffect="non-scaling-stroke" />
          {labelIndexes.map((index) => {
            const point = coordinates[index];
            const anchor = index === 0 ? 'start' : index === coordinates.length - 1 ? 'end' : 'middle';
            return <text key={index} x={point.x} y="121" textAnchor={anchor} fill="#9ca3af" fontSize="10">{formatClock(point.createdAt).slice(0, 5)}</text>;
          })}
        </svg>
      ) : (
        <div className="flex h-32 items-center justify-center border-y border-gray-100 text-xs text-gray-400">暂无处理速度数据</div>
      )}
    </div>
  );
};

export const BatchAnnotationRunResults: React.FC<RunOverviewProps> = ({ run, pendingCount }) => {
  const legend = [
    { label: '成功', value: run.succeeded_count, color: 'bg-green-500' },
    { label: '失败', value: run.failed_count, color: 'bg-red-500' },
    { label: '待处理', value: pendingCount, color: 'bg-gray-300' },
    { label: '已跳过', value: run.skipped_count, color: 'bg-yellow-500' },
    { label: '已取消', value: run.canceled_count, color: 'bg-orange-500' },
  ];
  return (
    <section className={`${panelClassName} p-5 sm:p-6`}>
      <h2 className="mb-5 text-base font-bold text-gray-900">样本处理结果</h2>
      <div className="grid items-center gap-6 lg:grid-cols-2">
        <div className="flex min-w-0 items-center justify-center gap-6 sm:gap-8">
          <ResultDonut run={run} pendingCount={pendingCount} />
          <div className="min-w-[170px] space-y-3 text-sm">
            {legend.map((item) => (
              <div key={item.label} className="flex items-center justify-between gap-5">
                <span className="text-gray-600"><span className={`mr-2 inline-block h-2 w-2 rounded-full ${item.color}`} />{item.label}</span>
                <span className="whitespace-nowrap text-gray-600">{formatNumber(item.value)} ({run.total_count ? ((item.value / run.total_count) * 100).toFixed(1) : '0.0'}%)</span>
              </div>
            ))}
          </div>
        </div>
        <ProcessingSpeedChart run={run} />
      </div>
    </section>
  );
};
