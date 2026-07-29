import type {
  AiPipelineBatchRunEvent,
  AiPipelineBatchRunItem,
  AiPipelineBatchRunProgressPoint,
} from '../../../types';

export const activeBatchRunStatuses = new Set(['queued', 'running']);
export const batchRunItemPageSize = 50;

export const batchRunStatusLabels: Record<string, string> = {
  queued: '等待执行',
  running: '执行中',
  succeeded: '已完成',
  failed: '失败',
  canceled: '已取消',
  pending: '待处理',
  skipped: '已跳过',
};

export const batchRunEventTitles: Record<string, string> = {
  queued: '任务开始执行',
  progress: '样本处理中',
  result: '批次处理完成',
  canceled: '任务已取消',
};

export const mergeBatchRunEvents = (
  current: AiPipelineBatchRunEvent[],
  incoming: AiPipelineBatchRunEvent[],
) => Array.from(
  new Map([...current, ...incoming].map((event) => [event.id, event])).values(),
).sort((left, right) => left.id - right.id).slice(-100);

export const appendProgressPointFromEvent = (
  current: AiPipelineBatchRunProgressPoint[] = [],
  event: AiPipelineBatchRunEvent,
) => {
  if (!event.created_at || !['progress', 'result'].includes(event.event_type)) return current;
  const payload = event.event_payload;
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return current;
  const rawProgress = payload.run_progress ?? payload.progress;
  if (typeof rawProgress !== 'number' || !Number.isFinite(rawProgress)) return current;
  const progress = Math.min(Math.max(Math.floor(rawProgress), 0), 100);
  if (current.at(-1)?.progress === progress) return current;
  return [...current, { progress, created_at: event.created_at }].slice(-240);
};

const parseDate = (value?: string | null) => {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
};

const padNumber = (value: number) => String(value).padStart(2, '0');

export const formatNumber = (value: number) => new Intl.NumberFormat('zh-CN').format(value);

export const formatDateTime = (value?: string | null) => {
  const date = parseDate(value);
  if (!date) return '-';
  return `${date.getFullYear()}-${padNumber(date.getMonth() + 1)}-${padNumber(date.getDate())} ${padNumber(date.getHours())}:${padNumber(date.getMinutes())}:${padNumber(date.getSeconds())}`;
};

export const formatClock = (value?: string | null) => {
  const date = parseDate(value);
  if (!date) return '-';
  return `${padNumber(date.getHours())}:${padNumber(date.getMinutes())}:${padNumber(date.getSeconds())}`;
};

export const formatDuration = (start?: string | null, end?: string | null) => {
  const startDate = parseDate(start);
  if (!startDate) return '-';
  const endDate = parseDate(end) ?? new Date();
  const totalSeconds = Math.floor(Math.max(0, endDate.getTime() - startDate.getTime()) / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map(padNumber).join(':');
};

export const getItemDuration = (item: AiPipelineBatchRunItem) => {
  if (!item.started_at) return '-';
  const start = parseDate(item.started_at);
  const end = parseDate(item.finished_at);
  if (!start || !end) return '-';
  const seconds = Math.max(0, end.getTime() - start.getTime()) / 1000;
  return `${seconds.toFixed(seconds < 10 ? 2 : 1)}s`;
};

export const getBatchRunEventText = (event: AiPipelineBatchRunEvent) => {
  const payload = event.event_payload;
  if (event.event_type === 'queued') return '批量标注任务已创建，等待调度执行';
  if (event.event_type === 'progress' && payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const data = payload as Record<string, unknown>;
    return data.processed !== undefined && data.total !== undefined
      ? `已处理 ${data.processed} / ${data.total}`
      : '正在处理当前批次';
  }
  if (event.event_type === 'result' && payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const data = payload as Record<string, unknown>;
    return `成功 ${data.succeeded_count ?? 0}，失败 ${data.failed_count ?? 0}，已跳过 ${data.skipped_count ?? 0}`;
  }
  if (event.event_type === 'canceled') return '任务已取消，已完成的标注结果会保留';
  if (typeof payload === 'string') return payload;
  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const data = payload as Record<string, unknown>;
    return String(data.message ?? data.error ?? data.chunk_key ?? event.event_type);
  }
  return event.event_type;
};

export interface ProcessingRatePoint {
  createdAt: string;
  rate: number;
}

export const buildProcessingRatePoints = (
  progressPoints: AiPipelineBatchRunProgressPoint[] = [],
  totalCount: number,
): ProcessingRatePoint[] => {
  if (progressPoints.length < 2 || totalCount <= 0) return [];
  const points: ProcessingRatePoint[] = [];
  for (let index = 1; index < progressPoints.length; index += 1) {
    const previous = progressPoints[index - 1];
    const current = progressPoints[index];
    const elapsedMinutes = (new Date(current.created_at).getTime() - new Date(previous.created_at).getTime()) / 60000;
    const processedCount = ((current.progress - previous.progress) / 100) * totalCount;
    if (elapsedMinutes <= 0 || processedCount < 0) continue;
    points.push({ createdAt: current.created_at, rate: Math.round(processedCount / elapsedMinutes) });
  }
  return points;
};
