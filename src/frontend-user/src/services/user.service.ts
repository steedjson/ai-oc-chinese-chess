import { http } from './api';
import type { ApiResponse, User, UserProfile, PaginatedResponse, Game } from '@/types';

const USERS_BASE = '/users';

export const userService = {
  /**
   * 获取用户详情
   */
  async getUser(userId: number): Promise<ApiResponse<User>> {
    return await http.get(`${USERS_BASE}/${userId}/`);
  },

  /**
   * 获取当前用户信息
   */
  async getProfile(): Promise<ApiResponse<UserProfile>> {
    return await http.get(`${USERS_BASE}/profile/`);
  },

  /**
   * 更新用户资料
   */
  async updateProfile(data: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> {
    return await http.put(`${USERS_BASE}/profile/`, data);
  },

  /**
   * 修改头像
   */
  async uploadAvatar(avatarFile: File): Promise<ApiResponse<{ avatar_url: string }>> {
    const formData = new FormData();
    formData.append('avatar', avatarFile);
    
    return await http.post(`${USERS_BASE}/profile/avatar/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * 获取用户对局历史
   */
  async getUserGames(
    userId: number,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApiResponse<PaginatedResponse<Game>>> {
    return await http.get(`${USERS_BASE}/${userId}/games/?page=${page}&page_size=${pageSize}`);
  },

  /**
   * 获取用户统计
   */
  async getUserStats(userId?: number): Promise<ApiResponse<{
    total_games: number;
    wins: number;
    losses: number;
    draws: number;
    win_rate: number;
    current_rating: number;
    highest_rating: number;
    favorite_piece?: string;
    average_game_duration?: number;
  }>> {
    const url = userId ? `${USERS_BASE}/${userId}/stats/` : `${USERS_BASE}/me/stats/`;
    return await http.get(url);
  },
};

export default userService;
