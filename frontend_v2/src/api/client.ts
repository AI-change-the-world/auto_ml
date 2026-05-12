import axios from 'axios';
import { ApiClientError, type ApiErrorPayload } from '../utils/apiError';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
});

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  (response) => {
    // 业务级别错误检查 (HTTP 200 但 success=false)
    const data = response.data as ApiErrorPayload | undefined;
    if (data && data.success === false) {
      const detail = data.detail;
      const message = typeof detail === 'string'
        ? detail
        : data.message || '请求失败';
      console.error('[API Business Error]', message);
      return Promise.reject(new ApiClientError({
        message,
        code: data.code,
        errorCode: data.error_code ?? null,
        detail,
        httpStatus: response.status,
        payload: data,
      }));
    }
    return response;
  },
  (error) => {
    const payload = error.response?.data as ApiErrorPayload | undefined;
    const detail = payload?.detail;
    const message = typeof detail === 'string'
      ? detail
      : payload?.message || error.message || '请求失败';
    console.error('[API Error]', message);
    return Promise.reject(new ApiClientError({
      message,
      code: payload?.code,
      errorCode: payload?.error_code ?? null,
      detail,
      httpStatus: error.response?.status,
      payload,
    }));
  },
);

export default apiClient;
