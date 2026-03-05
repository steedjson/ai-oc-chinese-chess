import { http } from './api';
import type { ApiResponse, Game, PositionAnalysis, AIHint } from '@/types';

const AI_BASE = '/ai';

export const aiService = {
  /**
   * 创建 AI 对局
   */
  async createAIGame(difficulty: number, playerColor: 'red' | 'black' = 'red'): Promise<ApiResponse<Game>> {
    return await http.post<Game>(`${AI_BASE}/games/`, {
      difficulty,
      player_color: playerColor,
    });
  },

  /**
   * 请求 AI 走棋
   */
  async getAIMove(gameId: string): Promise<ApiResponse<{ move: string }>> {
    return await http.post(`${AI_BASE}/games/${gameId}/move/`);
  },

  /**
   * 获取走棋提示
   */
  async getHint(gameId: string, count: number = 3): Promise<ApiResponse<{ hints: AIHint[] }>> {
    return await http.get(`${AI_BASE}/games/${gameId}/hint/?count=${count}`);
  },

  /**
   * 分析当前局面
   */
  async analyzePosition(gameId: string, depth: number = 10): Promise<ApiResponse<PositionAnalysis>> {
    return await http.get(`${AI_BASE}/games/${gameId}/analyze/?depth=${depth}`);
  },

  /**
   * 获取难度等级说明
   */
  async getDifficultyLevels(): Promise<ApiResponse<Array<{
    level: number;
    name: string;
    description: string;
    elo_estimate: number;
  }>>> {
    return await http.get(`${AI_BASE}/difficulty-levels/`);
  },
};

export default aiService;
