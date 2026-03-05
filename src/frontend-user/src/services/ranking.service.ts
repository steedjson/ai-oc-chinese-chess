import { http } from './api';
import type { 
  ApiResponse, 
  LeaderboardResponse, 
  User,
  RankDistribution 
} from '@/types';

const RANKING_BASE = '/rankings';

export const rankingService = {
  /**
   * 获取天梯排行榜
   */
  async getLeaderboard(
    page: number = 1,
    pageSize: number = 50,
    period: 'daily' | 'weekly' | 'monthly' | 'all' = 'all'
  ): Promise<ApiResponse<LeaderboardResponse>> {
    return await http.get(`${RANKING_BASE}/leaderboard/?page=${page}&page_size=${pageSize}&period=${period}`);
  },

  /**
   * 获取用户排名
   */
  async getUserRanking(userId?: number): Promise<ApiResponse<{ 
    rank: number;
    user: User;
    rating: number;
    total_games: number;
    wins: number;
    losses: number;
    draws: number;
    win_rate: number;
  }>> {
    const url = userId ? `${RANKING_BASE}/user/${userId}/` : `${RANKING_BASE}/user/me/`;
    return await http.get(url);
  },

  /**
   * 获取排名历史
   */
  async getRankHistory(
    userId?: number,
    days: number = 30
  ): Promise<ApiResponse<Array<{ 
    date: string; 
    rating: number; 
    rank: number;
    games_played: number;
  }>>> {
    const url = userId 
      ? `${RANKING_BASE}/history/${userId}/?days=${days}`
      : `${RANKING_BASE}/history/?days=${days}`;
    return await http.get(url);
  },

  /**
   * 获取段位分布
   */
  async getRankDistribution(): Promise<ApiResponse<{ 
    distributions: RankDistribution[];
    total_players: number;
  }>> {
    return await http.get(`${RANKING_BASE}/distribution/`);
  },

  /**
   * 搜索用户
   */
  async searchUsers(query: string, limit: number = 20): Promise<ApiResponse<User[]>> {
    return await http.get(`${RANKING_BASE}/search/?q=${encodeURIComponent(query)}&limit=${limit}`);
  },
};

export default rankingService;
