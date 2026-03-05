import apiClient from './index';
import type { LoginRequest, LoginResponse, ApiResponse } from '../types';

const BASE_URL = '/auth';

export const authApi = {
  // 登录
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<ApiResponse<LoginResponse>>(`${BASE_URL}/login`, credentials);
    return response.data.data;
  },

  // 登出
  logout: async (): Promise<void> => {
    await apiClient.post(`${BASE_URL}/logout`);
  },

  // 获取当前用户信息
  getCurrentUser: async (): Promise<{
    id: string;
    username: string;
    role: 'admin' | 'super_admin';
    permissions: string[];
  }> => {
    const response = await apiClient.get<ApiResponse<unknown>>(`${BASE_URL}/me`);
    return response.data.data as any;
  },
};
