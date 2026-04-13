/** 工具模型创建请求 */
export interface ToolModelCreate {
  name: string;
  model_type?: string;
  endpoint?: string;
  config?: string;
}

/** 工具模型响应 */
export interface ToolModelResponse {
  id: number;
  name: string;
  model_type: string | null;
  endpoint: string | null;
  config: string | null;
  created_at: string;
}
