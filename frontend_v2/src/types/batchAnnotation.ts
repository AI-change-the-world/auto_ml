export type AiPipelineBatchScriptParameterValue = string | number | boolean;

export interface AiPipelineBatchScriptField {
  key: string;
  label: string;
  value_type?: string;
  required?: boolean;
  default_value?: AiPipelineBatchScriptParameterValue;
  description?: string;
  widget?: string;
  value_source?: string;
  options?: Array<string | number>;
}

export interface AiPipelineBatchScript {
  key: string;
  version: string;
  name: string;
  description?: string | null;
  supported_data_types: number[];
  supported_annotation_types: number[];
  parameter_fields: AiPipelineBatchScriptField[];
  entrypoint?: string | null;
  is_builtin: boolean;
  enabled: boolean;
}

export interface AiPipelineBatchScriptUpdateRequest {
  enabled?: boolean;
}

export interface AiPipelineBatchRun {
  id: number;
  run_id: string;
  dataset_id: number;
  annotation_id: number;
  script_key: string;
  script_version: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'canceled' | string;
  selection_mode: 'all' | 'unannotated' | 'selected';
  overwrite_policy: 'skip_existing' | 'overwrite_draft' | 'overwrite_all';
  batch_size: number;
  parallelism: number;
  total_count: number;
  succeeded_count: number;
  failed_count: number;
  skipped_count: number;
  canceled_count: number;
  progress: number;
  cancel_requested: boolean;
  script_params: Record<string, unknown>;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AiPipelineBatchRunItem {
  id: number;
  sample_item_id: number;
  item_key: string;
  status: string;
  attempt_count: number;
  annotation_record_id?: number | null;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AiPipelineBatchRunEvent {
  id: number;
  event_type: string;
  event_payload?: Record<string, unknown> | unknown[] | string | null;
  created_at?: string | null;
}

export interface AiPipelineBatchRunCreateRequest {
  dataset_id: number;
  annotation_id: number;
  script_key: string;
  selection_mode: 'all' | 'unannotated' | 'selected';
  sample_item_ids?: number[];
  overwrite_policy: 'skip_existing' | 'overwrite_draft' | 'overwrite_all';
  script_params: Record<string, unknown>;
  batch_size: number;
  parallelism: number;
}
