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
