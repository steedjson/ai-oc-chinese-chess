import { describe, it, expect, beforeEach, vi } from 'vitest';
import { matchmakingApi } from '../matchmaking';
import apiClient from '../index';

vi.mock('../index', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('matchmakingApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getList', () => {
    it('should call GET /matchmaking with params', async () => {
      const mockParams = {
        page: 1,
        pageSize: 10,
        status: 'matched',
      };

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

      const result = await matchmakingApi.getList(mockParams);

      expect(apiClient.get).toHaveBeenCalledWith('/matchmaking', { params: mockParams });
      expect(result).toEqual({
        data: [],
        total: 0,
      });
    });
  });

  describe('getRanking', () => {
    it('should call GET /matchmaking/ranking with params', async () => {
      const mockParams = {
        limit: 10,
        offset: 0,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: {
            rankings: [],
            total: 0,
          },
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await matchmakingApi.getRanking(mockParams);

      expect(apiClient.get).toHaveBeenCalledWith('/matchmaking/ranking', { params: mockParams });
      expect(result).toEqual({
        rankings: [],
        total: 0,
      });
    });
  });

  describe('getStatistics', () => {
    it('should call GET /matchmaking/statistics', async () => {
      const mockStats = {
        totalMatches: 1000,
        avgWaitTime: 30,
        successRate: 0.95,
        inQueueCount: 5,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockStats,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await matchmakingApi.getStatistics();

      expect(apiClient.get).toHaveBeenCalledWith('/matchmaking/statistics');
      expect(result).toEqual(mockStats);
    });
  });

  describe('manualMatch', () => {
    it('should call POST /matchmaking/manual-match with playerIds', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({});

      await matchmakingApi.manualMatch(['player-1', 'player-2']);

      expect(apiClient.post).toHaveBeenCalledWith('/matchmaking/manual-match', {
        playerIds: ['player-1', 'player-2'],
      });
    });
  });

  describe('cancelMatch', () => {
    it('should call POST /matchmaking/cancel/:id', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({});

      await matchmakingApi.cancelMatch('match-1');

      expect(apiClient.post).toHaveBeenCalledWith('/matchmaking/cancel/match-1');
    });
  });
});
