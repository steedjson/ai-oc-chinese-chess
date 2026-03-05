import { http } from './api';
import type { 
  ApiResponse, 
  Game, 
  MakeMoveRequest, 
  GameResult,
  PaginatedResponse,
  Move
} from '@/types';

const GAMES_BASE = '/games';

export const gameService = {
  /**
   * 创建游戏对局
   */
  async createGame(gameType: 'online' | 'ai' | 'friend', aiLevel?: number): Promise<ApiResponse<Game>> {
    return await http.post<Game>(GAMES_BASE, {
      game_type: gameType,
      ai_level: aiLevel,
    });
  },

  /**
   * 获取对局详情
   */
  async getGame(gameId: string): Promise<ApiResponse<Game>> {
    return await http.get<Game>(`${GAMES_BASE}/${gameId}/`);
  },

  /**
   * 执行走棋
   */
  async makeMove(gameId: string, move: MakeMoveRequest): Promise<ApiResponse<{ move: Move; game: Game }>> {
    return await http.post(`${GAMES_BASE}/${gameId}/move/`, move);
  },

  /**
   * 投降
   */
  async resign(gameId: string): Promise<ApiResponse<GameResult>> {
    return await http.post(`${GAMES_BASE}/${gameId}/resign/`);
  },

  /**
   * 提议和棋
   */
  async offerDraw(gameId: string): Promise<ApiResponse<{ accepted: boolean }>> {
    return await http.post(`${GAMES_BASE}/${gameId}/draw/`);
  },

  /**
   * 接受和棋
   */
  async acceptDraw(gameId: string): Promise<ApiResponse<GameResult>> {
    return await http.post(`${GAMES_BASE}/${gameId}/draw/accept/`);
  },

  /**
   * 拒绝和棋
   */
  async rejectDraw(gameId: string): Promise<ApiResponse<void>> {
    return await http.post(`${GAMES_BASE}/${gameId}/draw/reject/`);
  },

  /**
   * 获取对局历史
   */
  async getGameHistory(
    page: number = 1,
    pageSize: number = 20,
    status?: string
  ): Promise<ApiResponse<PaginatedResponse<Game>>> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (status) {
      params.append('status', status);
    }
    return await http.get(`${GAMES_BASE}/history/?${params.toString()}`);
  },

  /**
   * 获取用户的所有对局
   */
  async getUserGames(
    userId: number,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApiResponse<PaginatedResponse<Game>>> {
    return await http.get(`/users/${userId}/games/?page=${page}&page_size=${pageSize}`);
  },

  /**
   * 获取对局回放
   */
  async getGameReplay(gameId: string): Promise<ApiResponse<{ moves: Move[]; game: Game }>> {
    return await http.get(`${GAMES_BASE}/${gameId}/replay/`);
  },

  /**
   * 获取合法走法提示
   */
  async getValidMoves(gameId: string, position: string): Promise<ApiResponse<{ positions: string[] }>> {
    return await http.get(`${GAMES_BASE}/${gameId}/valid-moves/?position=${position}`);
  },
};

export default gameService;
