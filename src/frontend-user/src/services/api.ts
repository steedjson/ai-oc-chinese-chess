import axios, { AxiosError } from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import type { ApiResponse } from '@/types';
import { mockRequestInterceptor, mockResponseInterceptor, isMockEnabled } from './api.mock';

// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws';

// 网络状态监听
let isOnline = navigator.onLine;
const offlineCallbacks: (() => void)[] = [];
const onlineCallbacks: (() => void)[] = [];

// 监听网络状态变化
if (typeof window !== 'undefined') {
  window.addEventListener('offline', () => {
    isOnline = false;
    offlineCallbacks.forEach(cb => cb());
    console.warn('🌐 网络已断开');
  });

  window.addEventListener('online', () => {
    isOnline = true;
    onlineCallbacks.forEach(cb => cb());
    console.info('🌐 网络已恢复');
  });
}

// 创建 Axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 网络状态管理
export function checkOnlineStatus(): boolean {
  return isOnline;
}

export function onOffline(callback: () => void): () => void {
  offlineCallbacks.push(callback);
  return () => {
    const index = offlineCallbacks.indexOf(callback);
    if (index > -1) {
      offlineCallbacks.splice(index, 1);
    }
  };
}

export function onOnline(callback: () => void): () => void {
  onlineCallbacks.push(callback);
  return () => {
    const index = onlineCallbacks.indexOf(callback);
    if (index > -1) {
      onlineCallbacks.splice(index, 1);
    }
  };
}

// Token 管理
let accessToken: string | null = null;
let refreshToken: string | null = null;

// 请求拦截器 - 添加认证 Token 和 Mock 拦截
apiClient.interceptors.request.use(
  async (config) => {
    // 检查网络状态
    if (!isOnline && !isMockEnabled()) {
      return Promise.reject({
        isNetworkError: true,
        message: '网络连接已断开，请检查网络设置',
        config,
      });
    }

    // Mock 拦截
    const mockResponse = await mockRequestInterceptor(config);
    if (mockResponse && typeof mockResponse.data !== 'undefined') {
      // 如果是 Mock 响应，抛出以便响应拦截器处理
      throw mockResponse;
    }

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理错误和 Token 刷新
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse<unknown>>) => {
    // 处理 Mock 响应
    const mockResult = mockResponseInterceptor(error);
    if (mockResult && typeof mockResult.data !== 'undefined') {
      return mockResult;
    }

    // 处理网络错误
    if (error.isNetworkError || !error.response) {
      const networkError = {
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: isOnline ? '服务器无响应，请稍后重试' : '网络连接已断开，请检查网络设置',
          details: {
            isOnline,
            timestamp: new Date().toISOString(),
          },
        },
      };
      return { data: networkError, status: 0 } as AxiosResponse;
    }

    const originalRequest = error.config;
    const status = error.response?.status;

    // 401 错误 - Token 过期
    if (status === 401 && !originalRequest?.headers?.['X-Retry-Token-Refresh']) {
      try {
        // 尝试刷新 Token
        const newToken = await refreshAccessToken();
        if (newToken && originalRequest) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          originalRequest.headers['X-Retry-Token-Refresh'] = 'true';
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // 刷新失败，清除 Token 并跳转登录
        clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    // 统一错误处理
    const apiError = {
      success: false,
      error: {
        code: getErrorCode(status),
        message: getErrorMessage(status, error.message),
        details: error.response?.data?.error as Record<string, unknown> | undefined,
      },
    };

    // 显示错误提示（开发环境）
    if (import.meta.env.DEV) {
      console.error(`🔴 API Error [${status}]:`, apiError.error);
    }

    return { data: apiError, status } as AxiosResponse;
  }
);

/**
 * 获取错误代码
 */
function getErrorCode(status?: number): string {
  switch (status) {
    case 400:
      return 'BAD_REQUEST';
    case 401:
      return 'UNAUTHORIZED';
    case 403:
      return 'FORBIDDEN';
    case 404:
      return 'NOT_FOUND';
    case 408:
      return 'REQUEST_TIMEOUT';
    case 409:
      return 'CONFLICT';
    case 429:
      return 'TOO_MANY_REQUESTS';
    case 500:
      return 'INTERNAL_SERVER_ERROR';
    case 502:
      return 'BAD_GATEWAY';
    case 503:
      return 'SERVICE_UNAVAILABLE';
    case 504:
      return 'GATEWAY_TIMEOUT';
    default:
      return 'UNKNOWN_ERROR';
  }
}

/**
 * 获取错误消息
 */
function getErrorMessage(status?: number, defaultMessage?: string): string {
  switch (status) {
    case 400:
      return '请求参数错误';
    case 401:
      return '未授权，请登录';
    case 403:
      return '拒绝访问';
    case 404:
      return '请求的资源不存在';
    case 408:
      return '请求超时';
    case 409:
      return '请求冲突';
    case 429:
      return '请求过于频繁，请稍后重试';
    case 500:
      return '服务器内部错误';
    case 502:
      return '网关错误';
    case 503:
      return '服务暂时不可用';
    case 504:
      return '网关超时';
    default:
      return defaultMessage || '未知错误';
  }
}

// Token 管理函数
export function setTokens(access: string, refresh?: string) {
  accessToken = access;
  if (refresh) {
    refreshToken = refresh;
  }
  localStorage.setItem('access_token', access);
  if (refresh) {
    localStorage.setItem('refresh_token', refresh);
  }
}

export function getAccessToken(): string | null {
  if (accessToken) return accessToken;
  const stored = localStorage.getItem('access_token');
  if (stored) {
    accessToken = stored;
  }
  return accessToken;
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export function initTokens() {
  // 从 localStorage 初始化 Token
  const storedAccess = localStorage.getItem('access_token');
  const storedRefresh = localStorage.getItem('refresh_token');
  if (storedAccess) {
    accessToken = storedAccess;
  }
  if (storedRefresh) {
    refreshToken = storedRefresh;
  }
}

// 刷新 Token
async function refreshAccessToken(): Promise<string | null> {
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await axios.post<ApiResponse<{ access_token: string; refresh_token?: string }>>(
      `${API_BASE_URL}/auth/refresh/`,
      { refresh: refreshToken }
    );

    if (response.data.success && response.data.data) {
      setTokens(response.data.data.access_token, response.data.data.refresh_token);
      return response.data.data.access_token;
    }
    return null;
  } catch (error) {
    console.error('Token refresh failed:', error);
    return null;
  }
}

// 通用请求方法
export async function request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
  try {
    const response = await apiClient<ApiResponse<T>>(config);
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      return {
        success: false,
        error: {
          code: error.code || 'NETWORK_ERROR',
          message: error.message,
          details: error.response?.data?.error as Record<string, unknown> | undefined,
        },
      };
    }
    return {
      success: false,
      error: {
        code: 'UNKNOWN_ERROR',
        message: '未知错误',
      },
    };
  }
}

// HTTP 方法封装
export const http = {
  get: <T>(url: string, config?: AxiosRequestConfig) => 
    request<T>({ ...config, method: 'GET', url }),
  
  post: <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig) => 
    request<T>({ ...config, method: 'POST', url, data }),
  
  put: <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig) => 
    request<T>({ ...config, method: 'PUT', url, data }),
  
  patch: <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig) => 
    request<T>({ ...config, method: 'PATCH', url, data }),
  
  delete: <T>(url: string, config?: AxiosRequestConfig) => 
    request<T>({ ...config, method: 'DELETE', url }),
};

// WebSocket URL 生成
export function getWebSocketUrl(endpoint: string, token?: string): string {
  const wsToken = token || getAccessToken();
  const separator = endpoint.includes('?') ? '&' : '?';
  return `${WS_BASE_URL}/${endpoint}${separator}token=${wsToken}`;
}

export { apiClient };
export default apiClient;
