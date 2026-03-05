import apiClient from './index';
import type { DailyStats, UserGrowthStats, GameTimeStats, ApiResponse } from '../types';

const BASE_URL = '/statistics';

export const statisticsApi = {
  // 获取日活/月活统计
  getDailyStats: async (params: { startDate: string; endDate: string }): Promise<{
    daily: DailyStats[];
    summary: {
      avgDau: number;
      avgMau: number;
      totalNewUsers: number;
      totalGames: number;
    };
  }> => {
    const response = await apiClient.get<ApiResponse<unknown>>(`${BASE_URL}/daily`, { params });
    return response.data.data as any;
  },

  // 获取用户增长曲线
  getUserGrowth: async (params: { startDate: string; endDate: string }): Promise<{
    data: UserGrowthStats[];
    growthRate: number;
  }> => {
    const response = await apiClient.get<ApiResponse<unknown>>(`${BASE_URL}/users`, { params });
    return response.data.data as any;
  },

  // 获取游戏时长统计
  getGameTimeStats: async (params: { startDate: string; endDate: string }): Promise<{
    data: GameTimeStats[];
    totalHours: number;
    avgHoursPerDay: number;
  }> => {
    const response = await apiClient.get<ApiResponse<unknown>>(`${BASE_URL}/game-time`, { params });
    return response.data.data as any;
  },

  // 获取仪表盘概览数据
  getDashboard: async (): Promise<{
    totalUsers: number;
    onlineUsers: number;
    totalGames: number;
    activeGames: number;
    dau: number;
    mau: number;
    newUsersToday: number;
  }> => {
    const response = await apiClient.get<ApiResponse<unknown>>(`${BASE_URL}/dashboard`);
    return response.data.data as any;
  },
};
