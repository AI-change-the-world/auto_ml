import type { AiPipelineBatchRunStreamEnvelope } from '../types';

function buildBatchRunStreamUrl(runId: string) {
  const base = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
  return new URL(
    `${base}/ai-pipeline/batch-runs/${encodeURIComponent(runId)}/stream`,
    window.location.origin,
  ).toString();
}

export function subscribeBatchAnnotationRunStream(
  runId: string,
  handlers: {
    onEvent: (payload: AiPipelineBatchRunStreamEnvelope) => void;
    onError?: () => void;
  },
) {
  const source = new EventSource(buildBatchRunStreamUrl(runId));

  source.addEventListener('batch_run_updated', (event) => {
    const message = event as MessageEvent<string>;
    handlers.onEvent({
      event: 'batch_run_updated',
      data: JSON.parse(message.data),
    });
  });

  source.onerror = () => {
    handlers.onError?.();
  };

  return () => {
    source.close();
  };
}
