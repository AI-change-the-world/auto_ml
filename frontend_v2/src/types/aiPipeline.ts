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

export interface AiPipelineTemplateDetail extends AiPipelineTemplateListItem {
  definition_json?: Record<string, unknown> | unknown[] | string | null;
  form_schema_json?: Record<string, unknown> | unknown[] | string | null;
  change_note?: string | null;
}

export interface AiPipelineTemplatePublishRequest {
  version: number;
}

export interface AiPipelineTemplateCreateRequest {
  template_key: string;
  name: string;
  description?: string;
  scene_type: string;
  input_kind?: string;
  output_kind?: string;
  status?: string;
  is_builtin?: boolean;
  created_by?: string;
}

export interface AiPipelineTemplateVersionCreateRequest {
  version: number;
  definition_json: Record<string, unknown> | unknown[] | string;
  form_schema_json?: Record<string, unknown> | unknown[] | string | null;
  change_note?: string;
  is_published?: boolean;
  created_by?: string;
}

export interface AiPipelineTemplateDraftSaveRequest {
  definition_json: Record<string, unknown> | unknown[] | string;
  form_schema_json?: Record<string, unknown> | unknown[] | string | null;
  change_note?: string;
  created_by?: string;
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
  name?: string;
  description?: string;
  is_default?: boolean;
  runtime_input_defaults_json?: Record<string, unknown> | unknown[] | string | null;
  resource_bindings_json?: Record<string, unknown> | unknown[] | string | null;
  created_by?: string;
}

export interface AiPipelineBindingUpdateRequest {
  template_id?: number;
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

export interface AiPipelineProviderResourceItem {
  id?: number;
  resource_id: string;
  provider_name: string;
  display_name: string;
  description?: string | null;
  role: string;
  kind?: string | null;
  base_url?: string | null;
  api_key_configured: boolean;
  model?: string | null;
  timeout_seconds?: number | null;
  temperature?: number | null;
  max_tokens?: number | null;
  extra_headers_json?: Record<string, unknown> | unknown[] | string | null;
  extra_json?: Record<string, unknown> | unknown[] | string | null;
  enabled?: boolean;
  created_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AiPipelineProviderResourceOption {
  id?: number;
  resource_id: string;
  provider_name: string;
  display_name: string;
  role: string;
  kind?: string | null;
  model?: string | null;
  enabled?: boolean;
}

export interface AiPipelineProviderResourceCreateRequest {
  resource_id: string;
  provider_name: string;
  display_name: string;
  description?: string;
  kind: string;
  role: string;
  base_url?: string;
  api_key?: string;
  model?: string;
  timeout_seconds?: number;
  temperature?: number;
  max_tokens?: number;
  extra_headers_json?: Record<string, unknown> | unknown[] | string | null;
  extra_json?: Record<string, unknown> | unknown[] | string | null;
  enabled?: boolean;
  created_by?: string;
}

export interface AiPipelineProviderResourceUpdateRequest {
  display_name?: string;
  description?: string;
  kind?: string;
  role?: string;
  base_url?: string;
  api_key?: string;
  model?: string;
  timeout_seconds?: number;
  temperature?: number;
  max_tokens?: number;
  extra_headers_json?: Record<string, unknown> | unknown[] | string | null;
  extra_json?: Record<string, unknown> | unknown[] | string | null;
  enabled?: boolean;
}

export interface AiPipelineFieldSchema {
  key: string;
  label: string;
  value_type?: string;
  required?: boolean;
  default_value?: unknown;
  description?: string;
  widget?: string;
  widget_props?: Record<string, unknown> | null;
  options?: Array<{ label: string; value: string | number | boolean }>;
  multiline?: boolean;
}

export interface AiPipelineResourceSlotSchema extends AiPipelineFieldSchema {
  value_type?: 'resource_ref' | string;
}

export interface AiPipelineTemplateFormSchema {
  runtime_inputs?: AiPipelineFieldSchema[];
  resource_slots?: AiPipelineResourceSlotSchema[];
}

export interface AiPipelineCapabilityFieldOption {
  label: string;
  value: string | number | boolean;
}

export interface AiPipelineCapabilityField {
  key: string;
  label: string;
  value_type?: string;
  required?: boolean;
  description?: string | null;
  widget?: string | null;
  default_value?: unknown;
  placeholder?: string | null;
  binding_kind?: string;
  resource_type?: string | null;
  task_kind?: string | null;
  deployed_only?: boolean | null;
  options?: AiPipelineCapabilityFieldOption[];
}

export interface AiPipelineCapabilityContextTarget {
  key: string;
  label: string;
  description?: string | null;
  accepted_output_types?: string[];
}

export interface AiPipelineCapabilityItem {
  name: string;
  display_name: string;
  description?: string | null;
  category: string;
  requires_provider: boolean;
  provider_role?: string | null;
  recommended_output_key?: string | null;
  input_types?: string[];
  output_type?: string | null;
  scene_types: string[];
  parameter_fields: AiPipelineCapabilityField[];
  context_mapping_targets: AiPipelineCapabilityContextTarget[];
}
