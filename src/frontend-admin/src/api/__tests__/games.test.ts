import { describe, it, expect, beforeEach, vi } from 'vitest';
import { gamesApi } from '../games';
import apiClient from '../index';
import type { GameListParams } from '../../types';

vi.mock('../index', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('gamesApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockGameListParams: GameListParams = {
    page: 1,
    pageSize: 10,
    status: 'completed',
  };

  describe('getList', () => {
    it('should call GET /games with params', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: {
            data: [],
            total: 0,
            page: 1,
            pageSize: 10,
          },
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await gamesApi.getList(mockGameListParams);

      expect(apiClient.get).toHaveBeenCalledWith('/games', { params: mockGameListParams });
      expect(result).toEqual({
        data: [],
        total: 0,
        page: 1,
        pageSize: 10,
      });
    });
  });

  describe('getDetail', () => {
    it('should call GET /games/:id', async () => {
      const mockGame = {
        id: 'game-1',
        whitePlayer: { id: '1', username: 'player1', elo: 1200 },
        blackPlayer: { id: '2', username: 'player2', elo: 1250 },
        status: 'completed' as const,
        moveCount: 50,
        duration: 1800,
        createdAt: '2024-01-01',
        startTime: '2024-01-01',
        isAiGame: false,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockGame,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await gamesApi.getDetail('game-1');

      expect(apiClient.get).toHaveBeenCalledWith('/games/game-1');
      expect(result).toEqual(mockGame);
    });
  });

  describe('getStatistics', () => {
    it('should call GET /games/:id/statistics', async () => {
      const mockStats = {
        totalMoves: 50,
        avgMoveTime: 30,
        openingType: '中炮对屏风马',
        endgameType: '马炮残棋',
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockStats,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await gamesApi.getStatistics('game-1');

      expect(apiClient.get).toHaveBeenCalledWith('/games/game-1/statistics');
      expect(result).toEqual(mockStats);
    });
  });

  describe('abortGame', () => {
    it('should call POST /games/:id/abort', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({});

      await gamesApi.abortGame('game-1');

      expect(apiClient.post).toHaveBeenCalledWith('/games/game-1/abort');
    });
  });

  describe('clearExpiredWaiting', () => {
    it('should call POST /games/clear-expired-waiting', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: { count: 5 },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse as any);

      const result = await gamesApi.clearExpiredWaiting();

      expect(apiClient.post).toHaveBeenCalledWith('/games/clear-expired-waiting');
      expect(result).toEqual({ count: 5 });
    });
  });

  describe('getManagementList', () => {
    it('should call GET /management/games with params', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: {
            data: [],
            total: 0,
            page: 1,
            pageSize: 10,
          },
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await gamesApi.getManagementList(mockGameListParams);

      expect(apiClient.get).toHaveBeenCalledWith('/management/games', { params: mockGameListParams });
      expect(result).toEqual({
        data: [],
        total: 0,
        page: 1,
        pageSize: 10,
      });
    });
  });

  describe('getManagementDetail', () => {
    it('should call GET /management/games/:id', async () => {
      const mockGame = {
        id: 'game-1',
        status: 'completed' as const,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockGame,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await gamesApi.getManagementDetail('game-1');

      expect(apiClient.get).toHaveBeenCalledWith('/management/games/game-1');
      expect(result).toEqual(mockGame);
    });
  });

  describe('abortGameAdmin', () => {
    it('should call POST /management/games/:id/abort with reason', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({});

      await gamesApi.abortGameAdmin('game-1', 'Player disconnected');

      expect(apiClient.post).toHaveBeenCalledWith('/management/games/game-1/abort', {
        reason: 'Player disconnected',
      });
    });
  });

  describe('getAnomalies', () => {
    it('should call GET /management/games/anomalies', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: {
            data: [],
            total: 0,
          },
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await gamesApi.getAnomalies();

      expect(apiClient.get).toHaveBeenCalledWith('/management/games/anomalies');
      expect(result).toEqual({
        data: [],
        total: 0,
      });
    });
  });

  describe('markAsAbnormal', () => {
    it('should call POST /management/games/:id/mark_abnormal with reason', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({});

      await gamesApi.markAsAbnormal('game-1', 'Suspicious moves detected');

      expect(apiClient.post).toHaveBeenCalledWith('/management/games/game-1/mark_abnormal', {
        reason: 'Suspicious moves detected',
      });
    });
  });

  describe('getGameLogs', () => {
    it('should call GET /management/games/:id/logs with params', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: {
            data: [],
            total: 0,
            page: 1,
            page_size: 10,
          },
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await gamesApi.getGameLogs('game-1', { page: 1, page_size: 10 });

      expect(apiClient.get).toHaveBeenCalledWith('/management/games/game-1/logs', {
        params: { page: 1, page_size: 10 },
      });
      expect(result).toEqual({
        data: [],
        total: 0,
        page: 1,
        page_size: 10,
      });
    });
  });

  describe('exportGameLogs', () => {
    it('should call GET /management/games/:id/logs/export with blob response type', async () => {
      const mockBlob = new Blob(['csv data'], { type: 'text/csv' });
      
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        data: mockBlob,
      } as any);

      const result = await gamesApi.exportGameLogs('game-1');

      expect(apiClient.get).toHaveBeenCalledWith('/management/games/game-1/logs/export', {
        responseType: 'blob',
      });
      expect(result).toBeInstanceOf(Blob);
    });
  });
});
