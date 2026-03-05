import axios, { AxiosError } from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type { ApiResponse } from '../types';

// API 基础配置
const API_BASE_URL = '/api/v1/admin';

// 创建 Axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证 token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('admin_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ApiResponse<unknown>>) => {
    if (error.response) {
      const { status } = error.response;
      
      // 401 - 未授权，跳转到登录页
      if (status === 401) {
        localStorage.removeItem('admin_token');
        window.location.href = '/admin/login';
      }
      
      // 403 - 禁止访问
      if (status === 403) {
        console.error('禁止访问：权限不足');
      }
      
      // 500 - 服务器错误
      if (status === 500) {
        console.error('服务器错误，请稍后重试');
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;

// 导出请求方法
export const api = {
  get: <T>(url: string, config?: object) => 
    apiClient.get<ApiResponse<T>>(url, config).then(res => res.data),
  
  post: <T>(url: string, data?: object, config?: object) => 
    apiClient.post<ApiResponse<T>>(url, data, config).then(res => res.data),
  
  put: <T>(url: string, data?: object, config?: object) => 
    apiClient.put<ApiResponse<T>>(url, data, config).then(res => res.data),
  
  delete: <T>(url: string, config?: object) => 
    apiClient.delete<ApiResponse<T>>(url, config).then(res => res.data),
};
