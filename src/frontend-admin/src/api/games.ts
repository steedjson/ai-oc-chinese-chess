import apiClient from './index';
import type { Game, GameListParams, GameListResponse, ApiResponse } from '../types';

const BASE_URL = '/games';

export const gamesApi = {
  // 获取游戏列表
  getList: async (params: GameListParams): Promise<GameListResponse> => {
    const response = await apiClient.get<ApiResponse<GameListResponse>>(BASE_URL, { params });
    return response.data.data;
  },

  // 获取游戏详情
  getDetail: async (id: string): Promise<Game> => {
    const response = await apiClient.get<ApiResponse<Game>>(`${BASE_URL}/${id}`);
    return response.data.data;
  },

  // 获取游戏统计数据
  getStatistics: async (gameId: string): Promise<{
    totalMoves: number;
    avgMoveTime: number;
    openingType: string;
    endgameType: string;
  }> => {
    const response = await apiClient.get<ApiResponse<unknown>>(`${BASE_URL}/${gameId}/statistics`);
    return response.data.data as any;
  },

  // 中止游戏
  abortGame: async (id: string): Promise<void> => {
    await apiClient.post(`${BASE_URL}/${id}/abort`);
  },

  // 清理过期等待中的对局
  clearExpiredWaiting: async (): Promise<{ count: number }> => {
    const response = await apiClient.post(`${BASE_URL}/clear-expired-waiting`);
    return response.data.data;
  },
};
