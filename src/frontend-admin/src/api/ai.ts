import apiClient from './index';
import type { AiGameRecord, AiConfig, ApiResponse } from '../types';

const BASE_URL = '/ai';

export interface StockfishParams {
  difficulty: number;
  threads: number;
  hashSize: number;
  multiPV: number;
  skillLevel: number;
}

export const aiApi = {
  // 获取 AI 对局记录
  getGameRecords: async (params: { page: number; pageSize: number; difficulty?: number }): Promise<{
    data: AiGameRecord[];
    total: number;
  }> => {
    const response = await apiClient.get<ApiResponse<{ data: AiGameRecord[]; total: number }>>(`${BASE_URL}/games`, { params });
    return response.data.data;
  },

  // 获取 AI 配置
  getConfig: async (): Promise<AiConfig> => {
    const response = await apiClient.get<ApiResponse<AiConfig>>(`${BASE_URL}/config`);
    return response.data.data;
  },

  // 更新 AI 配置
  updateConfig: async (data: Partial<AiConfig>): Promise<AiConfig> => {
    const response = await apiClient.put<ApiResponse<AiConfig>>(`${BASE_URL}/config`, data);
    return response.data.data;
  },

  // 获取 Stockfish 引擎参数
  getEngineParams: async (): Promise<StockfishParams> => {
    const response = await apiClient.get<ApiResponse<StockfishParams>>(`${BASE_URL}/engine-params`);
    return response.data.data;
  },

  // 更新 Stockfish 引擎参数
  updateEngineParams: async (params: Partial<StockfishParams>): Promise<StockfishParams> => {
    const response = await apiClient.put<ApiResponse<StockfishParams>>(`${BASE_URL}/engine-params`, params);
    return response.data.data;
  },

  // 获取 AI 调优数据
  getTuningData: async (): Promise<{
    winRates: Record<number, number>;
    avgGameDuration: Record<number, number>;
    playerFeedback: any[];
  }> => {
    const response = await apiClient.get<ApiResponse<unknown>>(`${BASE_URL}/tuning`);
    return response.data.data as any;
  },
};
