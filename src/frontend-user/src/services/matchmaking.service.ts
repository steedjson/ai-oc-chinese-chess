import { http } from './api';
import type { 
  ApiResponse, 
  MatchmakingStatus, 
  MatchFound 
} from '@/types';

const MATCHMAKING_BASE = '/matchmaking';

export const matchmakingService = {
  /**
   * 加入匹配队列
   */
  async joinQueue(): Promise<ApiResponse<MatchmakingStatus>> {
    return await http.post(`${MATCHMAKING_BASE}/`);
  },

  /**
   * 取消匹配
   */
  async cancelMatch(): Promise<ApiResponse<void>> {
    return await http.delete(`${MATCHMAKING_BASE}/`);
  },

  /**
   * 获取匹配状态
   */
  async getStatus(): Promise<ApiResponse<MatchmakingStatus>> {
    return await http.get(`${MATCHMAKING_BASE}/status/`);
  },

  /**
   * 接受匹配
   */
  async acceptMatch(matchId: string): Promise<ApiResponse<MatchFound>> {
    return await http.post(`${MATCHMAKING_BASE}/${matchId}/accept/`);
  },

  /**
   * 拒绝匹配
   */
  async rejectMatch(matchId: string): Promise<ApiResponse<void>> {
    return await http.post(`${MATCHMAKING_BASE}/${matchId}/reject/`);
  },
};

export default matchmakingService;
