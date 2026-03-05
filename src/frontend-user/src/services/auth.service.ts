import { http, setTokens, clearTokens, getAccessToken } from './api';
import type { ApiResponse, LoginRequest, LoginResponse, RegisterRequest, User } from '@/types';

const AUTH_BASE = '/auth';

export const authService = {
  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const result = await http.post<LoginResponse>(`${AUTH_BASE}/login/`, credentials);
    if (result.success && result.data) {
      setTokens(result.data.access_token, result.data.refresh_token);
    }
    return result;
  },

  /**
   * 用户注册
   */
  async register(data: RegisterRequest): Promise<ApiResponse<{ user: User }>> {
    return await http.post(`${AUTH_BASE}/register/`, data);
  },

  /**
   * 登出
   */
  async logout(): Promise<ApiResponse<unknown>> {
    const result = await http.post(`${AUTH_BASE}/logout/`);
    if (result.success) {
      clearTokens();
    }
    return result;
  },

  /**
   * 刷新 Token
   */
  async refreshToken(refreshToken: string): Promise<ApiResponse<{ access_token: string; refresh_token?: string }>> {
    return await http.post(`${AUTH_BASE}/refresh/`, { refresh: refreshToken });
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    return await http.get<User>('/users/profile/');
  },

  /**
   * 修改密码
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<ApiResponse<void>> {
    return await http.post('/users/profile/password/', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  /**
   * 检查是否已登录
   */
  isAuthenticated(): boolean {
    return !!getAccessToken();
  },

  /**
   * 获取 Token
   */
  getToken(): string | null {
    return getAccessToken();
  },
};

export default authService;
