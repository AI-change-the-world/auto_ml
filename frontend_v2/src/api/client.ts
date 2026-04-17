import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
});

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  (response) => {
    // 业务级别错误检查 (HTTP 200 但 success=false)
    const data = response.data;
    if (data && data.success === false) {
      const message = data.message || '请求失败';
      console.error('[API Business Error]', message);
      return Promise.reject(new Error(message));
    }
    return response;
  },
  (error) => {
    const detail = error.response?.data?.detail;
    const message = typeof detail === 'string'
      ? detail
      : error.response?.data?.message || error.message || '请求失败';
    console.error('[API Error]', message);
    return Promise.reject(error);
  },
);

export default apiClient;
