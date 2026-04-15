import type { TaskStreamEnvelope } from '../types';

function buildStreamUrl(taskId?: number) {
  const base = import.meta.env.VITE_API_BASE_URL || '/api';
  const url = new URL(`${window.location.origin}${base}/task/stream`);
  if (taskId !== undefined) {
    url.searchParams.set('task_id', String(taskId));
  }
  return url.toString();
}

export function subscribeTaskStream(
  handlers: {
    onEvent: (payload: TaskStreamEnvelope) => void;
    onError?: () => void;
  },
  taskId?: number,
) {
  const source = new EventSource(buildStreamUrl(taskId));

  const register = (eventName: TaskStreamEnvelope['event']) => {
    source.addEventListener(eventName, (event) => {
      const message = event as MessageEvent<string>;
      handlers.onEvent({
        event: eventName,
        data: JSON.parse(message.data),
      });
    });
  };

  register('task_upsert');
  register('task_log');
  register('trainer_status');

  source.onerror = () => {
    handlers.onError?.();
  };

  return () => {
    source.close();
  };
}
