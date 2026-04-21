/** 部署请求 */
export interface DeployRequest {
  model_id: number;
  device: string;
  version: string;
}

/** 可用模型响应 */
export interface AvailableModelResponse {
  id: number;
  name: string | null;
  model_path: string | null;
  onnx_model_path: string | null;
  model_type: string | null;
  dataset_id: number | null;
  task_id: number | null;
  loss: number | null;
  is_deployed: boolean;
  deployment_id: string | null;
  deployment_port: number | null;
  deployment_version: string | null;
  deployment_device: string | null;
  created_at: string;
  updated_at: string;
}

/** 部署状态响应 */
export interface DeployStatusResponse {
  model_id: number;
  is_deployed: boolean;
  deployment_id: string | null;
  port: number | null;
  version: string | null;
  device: string | null;
}

export interface InferenceBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface InferenceParams {
  input_type?: string | null;
  inference_mode?: 'direct' | 'tile' | 'scene' | string | null;
  tile_size?: number | null;
  tile_overlap?: number | null;
  merge_strategy?: 'nms' | 'wbf' | string | null;
  merge_iou?: number | null;
  edge_filter?: boolean | null;
  return_global_coords?: boolean | null;
  extra?: Record<string, unknown> | null;
}

export interface InferenceDetectionResult {
  type: 'bbox' | 'obb' | 'classification' | string;
  class_id: number;
  class_name: string;
  confidence: number;
  box?: InferenceBox | null;
  obb?: {
    cx: number;
    cy: number;
    w: number;
    h: number;
    angle: number;
  } | null;
  points?: Array<{ x: number; y: number }> | null;
}

export interface InferencePredictResponse {
  success: boolean;
  model_id: number | null;
  model_name: string | null;
  task_kind: string | null;
  backend: string | null;
  device: string | null;
  results: InferenceDetectionResult[];
  image_width: number | null;
  image_height: number | null;
  error: string | null;
  raw?: Record<string, unknown> | null;
}

export interface InferenceHealthResponse {
  model_id: number;
  model_name: string | null;
  task_kind: string | null;
  backend: string | null;
  is_deployed: boolean;
  backend_healthy: boolean;
  deployment_port: number | null;
  deployment_device: string | null;
  deployment_version: string | null;
  detail?: Record<string, unknown> | null;
}

export interface RenameModelRequest {
  name: string;
}
