export interface AiPipelineTemplateListItem {
  id: number;
  template_key: string;
  name: string;
  description?: string | null;
  scene_type: string;
  input_kind?: string | null;
  output_kind?: string | null;
  status: string;
  latest_version: number;
  published_version?: number | null;
  is_builtin: boolean;
  created_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AiPipelineBindingResponse {
  id: number;
  binding_type: string;
  binding_target_id: number;
  template_id: number;
  template_version: number;
  template_key?: string | null;
  template_name?: string | null;
  name?: string | null;
  description?: string | null;
  pipeline_type?: string | null;
  supported_annotation_types: number[];
  supported_shapes: string[];
  enabled: boolean;
  is_default: boolean;
  runtime_input_defaults_json?: Record<string, unknown> | unknown[] | string | null;
  resource_bindings_json?: Record<string, unknown> | unknown[] | string | null;
  created_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AiPipelineBindingCreateRequest {
  binding_type: string;
  binding_target_id: number;
  template_id: number;
  template_version: number;
  name?: string;
  description?: string;
  is_default?: boolean;
  runtime_input_defaults_json?: Record<string, unknown> | unknown[] | string | null;
  resource_bindings_json?: Record<string, unknown> | unknown[] | string | null;
  created_by?: string;
}

export interface AiPipelineBindingUpdateRequest {
  name?: string;
  description?: string;
  is_default?: boolean;
  runtime_input_defaults_json?: Record<string, unknown> | unknown[] | string | null;
  resource_bindings_json?: Record<string, unknown> | unknown[] | string | null;
}

export interface AiPipelineModelResourceItem {
  resource_id: string;
  model_id: number;
  display_name: string;
  model_name?: string | null;
  model_type?: string | null;
  runtime_template?: string | null;
  is_deployed: boolean;
  deployment_device?: string | null;
  deployed_at?: string | null;
}
