import apiClient from './index';
import type { MatchmakingRecord, EloRanking, ApiResponse } from '../types';

const BASE_URL = '/matchmaking';

export const matchmakingApi = {
  // 获取匹配记录列表
  getList: async (params: { page: number; pageSize: number; status?: string }): Promise<{
    data: MatchmakingRecord[];
    total: number;
  }> => {
    const response = await apiClient.get<ApiResponse<{ data: MatchmakingRecord[]; total: number }>>(BASE_URL, { params });
    return response.data.data;
  },

  // 获取 Elo 排行榜
  getRanking: async (params: { limit?: number; offset?: number }): Promise<{
    rankings: EloRanking[];
    total: number;
  }> => {
    const response = await apiClient.get<ApiResponse<{ rankings: EloRanking[]; total: number }>>(`${BASE_URL}/ranking`, { params });
    return response.data.data;
  },

  // 获取匹配统计
  getStatistics: async (): Promise<{
    totalMatches: number;
    avgWaitTime: number;
    successRate: number;
    inQueueCount: number;
  }> => {
    const response = await apiClient.get<ApiResponse<unknown>>(`${BASE_URL}/statistics`);
    return response.data.data as any;
  },

  // 手动干预匹配
  manualMatch: async (playerIds: string[]): Promise<void> => {
    await apiClient.post(`${BASE_URL}/manual-match`, { playerIds });
  },

  // 取消队列中的匹配
  cancelMatch: async (id: string): Promise<void> => {
    await apiClient.post(`${BASE_URL}/cancel/${id}`);
  },
};
