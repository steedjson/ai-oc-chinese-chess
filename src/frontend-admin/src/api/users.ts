import apiClient from './index';
import type { User, UserListParams, UserListResponse, ApiResponse } from '../types';

const BASE_URL = '/users';

export const usersApi = {
  // 获取用户列表
  getList: async (params: UserListParams): Promise<UserListResponse> => {
    const response = await apiClient.get<ApiResponse<UserListResponse>>(BASE_URL, { params });
    return response.data.data;
  },

  // 获取用户详情
  getDetail: async (id: string): Promise<User> => {
    const response = await apiClient.get<ApiResponse<User>>(`${BASE_URL}/${id}`);
    return response.data.data;
  },

  // 更新用户状态（禁用/启用）
  updateStatus: async (id: string, status: 'active' | 'inactive' | 'banned'): Promise<User> => {
    const response = await apiClient.put<ApiResponse<User>>(`${BASE_URL}/${id}/status`, { status });
    return response.data.data;
  },

  // 更新用户信息
  update: async (id: string, data: Partial<User>): Promise<User> => {
    const response = await apiClient.put<ApiResponse<User>>(`${BASE_URL}/${id}`, data);
    return response.data.data;
  },

  // 删除用户
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/${id}`);
  },
};
