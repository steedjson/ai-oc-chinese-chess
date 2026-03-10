import { describe, it, expect, beforeEach, vi } from 'vitest';
import { statisticsApi } from '../statistics';
import apiClient from '../index';

vi.mock('../index', () => ({
  default: {
    get: vi.fn(),
  },
}));

describe('statisticsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const dateParams = {
    startDate: '2024-01-01',
    endDate: '2024-01-31',
  };

  describe('getDailyStats', () => {
    it('should call GET /statistics/daily with date params', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: {
            daily: [],
            summary: {
              avgDau: 100,
              avgMau: 500,
              totalNewUsers: 50,
              totalGames: 1000,
            },
          },
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await statisticsApi.getDailyStats(dateParams);

      expect(apiClient.get).toHaveBeenCalledWith('/statistics/daily', { params: dateParams });
      expect(result).toEqual({
        daily: [],
        summary: {
          avgDau: 100,
          avgMau: 500,
          totalNewUsers: 50,
          totalGames: 1000,
        },
      });
    });
  });

  describe('getUserGrowth', () => {
    it('should call GET /statistics/users with date params', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: {
            data: [],
            growthRate: 10,
          },
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await statisticsApi.getUserGrowth(dateParams);

      expect(apiClient.get).toHaveBeenCalledWith('/statistics/users', { params: dateParams });
      expect(result).toEqual({
        data: [],
        growthRate: 10,
      });
    });
  });

  describe('getGameTimeStats', () => {
    it('should call GET /statistics/game-time with date params', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: {
            data: [],
            totalHours: 5000,
            avgHoursPerDay: 161,
          },
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await statisticsApi.getGameTimeStats(dateParams);

      expect(apiClient.get).toHaveBeenCalledWith('/statistics/game-time', { params: dateParams });
      expect(result).toEqual({
        data: [],
        totalHours: 5000,
        avgHoursPerDay: 161,
      });
    });
  });

  describe('getDashboard', () => {
    it('should call GET /statistics/dashboard without params', async () => {
      const mockDashboardData = {
        totalUsers: 1248,
        onlineUsers: 156,
        totalGames: 8934,
        activeGames: 24,
        dau: 523,
        mau: 1890,
        newUsersToday: 45,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockDashboardData,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await statisticsApi.getDashboard();

      expect(apiClient.get).toHaveBeenCalledWith('/statistics/dashboard');
      expect(result).toEqual(mockDashboardData);
    });
  });
});
