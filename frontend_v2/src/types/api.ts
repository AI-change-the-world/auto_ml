/** 统一响应格式 */
export interface Result<T = unknown> {
  success: boolean;
  code: number;
  message: string;
  data: T;
  timestamp?: string;
}

/** 分页结果 */
export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/** 分页请求参数 */
export interface PageParams {
  page?: number;
  page_size?: number;
}
