export interface TrainingRuntimeSupportedTask {
  task_kind?: string;
  data_modalities?: string[];
  annotation_kinds?: string[];
}

export interface TrainingRuntimeCodePackage {
  id: number;
  package_key: string;
  version: string;
  name: string;
  description: string | null;
  runtime_id: string;
  entrypoint: string;
  package_sha256: string;
  package_size_bytes: number;
  package_file_name: string;
  supported_tasks: TrainingRuntimeSupportedTask[];
  parameters_schema: Record<string, unknown>;
  model_input_contract: Record<string, unknown> | null;
  output_contract: Record<string, unknown>;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrainingRuntimeModelPackage {
  id: number;
  name: string;
  package_sha256: string;
  package_size_bytes: number;
  package_file_name: string;
  task_kind: string;
  class_names: string[];
  framework_id: string;
  framework_version: string;
  artifact_format: string;
  initialize_sha256: string;
  initialize_size_bytes: number;
  has_resume_checkpoint: boolean;
  metadata: Record<string, unknown>;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrainingRuntimeCodePackageImportResponse {
  package: TrainingRuntimeCodePackage;
  registration_created: boolean;
  catalog_created: boolean;
}

export interface TrainingRuntimeModelPackageImportResponse {
  package: TrainingRuntimeModelPackage;
  registration_created: boolean;
  catalog_created: boolean;
}
