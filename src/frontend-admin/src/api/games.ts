import apiClient from './index';
import type { 
  Game, 
  GameListParams, 
  GameListResponse, 
  ApiResponse,
  GameLog,
  GameLogParams,
  AnomalyData
} from '../types';

const BASE_URL = '/games';
const MANAGEMENT_BASE_URL = '/management/games';

export const gamesApi = {
  // ========== 普通用户 API ==========
  
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

  // 中止游戏（用户端）
  abortGame: async (id: string): Promise<void> => {
    await apiClient.post(`${BASE_URL}/${id}/abort`);
  },

  // 清理过期等待中的对局
  clearExpiredWaiting: async (): Promise<{ count: number }> => {
    const response = await apiClient.post(`${BASE_URL}/clear-expired-waiting`);
    return response.data.data;
  },

  // ========== 管理端专用 API ==========

  // 获取所有游戏列表（管理端）
  getManagementList: async (params: GameListParams): Promise<GameListResponse> => {
    const response = await apiClient.get<ApiResponse<GameListResponse>>(MANAGEMENT_BASE_URL, { params });
    return response.data.data;
  },

  // 获取对局详情（管理端）
  getManagementDetail: async (id: string): Promise<Game> => {
    const response = await apiClient.get<ApiResponse<Game>>(`${MANAGEMENT_BASE_URL}/${id}`);
    return response.data.data;
  },

  // 中止对局（管理端）- 带原因
  abortGameAdmin: async (id: string, reason: string): Promise<void> => {
    await apiClient.post(`${MANAGEMENT_BASE_URL}/${id}/abort`, { reason });
  },

  // 获取异常对局列表
  getAnomalies: async (): Promise<{ data: AnomalyData[]; total: number }> => {
    const response = await apiClient.get<ApiResponse<{ data: AnomalyData[]; total: number }>>(
      `${MANAGEMENT_BASE_URL}/anomalies`
    );
    return response.data.data;
  },

  // 标记对局为异常
  markAsAbnormal: async (id: string, reason: string): Promise<void> => {
    await apiClient.post(`${MANAGEMENT_BASE_URL}/${id}/mark_abnormal`, { reason });
  },

  // 获取对局日志
  getGameLogs: async (gameId: string, params?: GameLogParams): Promise<{
    data: GameLog[];
    total: number;
    page: number;
    page_size: number;
  }> => {
    const response = await apiClient.get<ApiResponse<unknown>>(
      `${MANAGEMENT_BASE_URL}/${gameId}/logs`,
      { params }
    );
    return response.data.data as any;
  },

  // 导出对局日志（CSV）
  exportGameLogs: async (gameId: string): Promise<Blob> => {
    const response = await apiClient.get(
      `${MANAGEMENT_BASE_URL}/${gameId}/logs/export`,
      { responseType: 'blob' }
    );
    return response.data;
  },
};

export default gamesApi;
