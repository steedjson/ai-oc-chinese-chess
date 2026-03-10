import { describe, it, expect, beforeEach, vi } from 'vitest';
import { aiApi } from '../ai';
import apiClient from '../index';

vi.mock('../index', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

describe('aiApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getGameRecords', () => {
    it('should call GET /ai/games with params', async () => {
      const mockParams = {
        page: 1,
        pageSize: 10,
        difficulty: 5,
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

      const result = await aiApi.getGameRecords(mockParams);

      expect(apiClient.get).toHaveBeenCalledWith('/ai/games', { params: mockParams });
      expect(result).toEqual({
        data: [],
        total: 0,
      });
    });
  });

  describe('getConfig', () => {
    it('should call GET /ai/config', async () => {
      const mockConfig = {
        id: 'config-1',
        difficulty: 5,
        enabled: true,
        eloBase: 1500,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-15',
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockConfig,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await aiApi.getConfig();

      expect(apiClient.get).toHaveBeenCalledWith('/ai/config');
      expect(result).toEqual(mockConfig);
    });
  });

  describe('updateConfig', () => {
    it('should call PUT /ai/config with data', async () => {
      const mockConfig = {
        id: 'config-1',
        difficulty: 6,
        enabled: true,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockConfig,
        },
      };

      vi.mocked(apiClient.put).mockResolvedValueOnce(mockResponse as any);

      const result = await aiApi.updateConfig({ difficulty: 6 });

      expect(apiClient.put).toHaveBeenCalledWith('/ai/config', { difficulty: 6 });
      expect(result).toEqual(mockConfig);
    });
  });

  describe('getEngineParams', () => {
    it('should call GET /ai/engine-params', async () => {
      const mockParams = {
        difficulty: 5,
        threads: 4,
        hashSize: 128,
        multiPV: 1,
        skillLevel: 10,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockParams,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await aiApi.getEngineParams();

      expect(apiClient.get).toHaveBeenCalledWith('/ai/engine-params');
      expect(result).toEqual(mockParams);
    });
  });

  describe('updateEngineParams', () => {
    it('should call PUT /ai/engine-params with params', async () => {
      const mockParams = {
        difficulty: 6,
        threads: 8,
        hashSize: 256,
        multiPV: 1,
        skillLevel: 15,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockParams,
        },
      };

      vi.mocked(apiClient.put).mockResolvedValueOnce(mockResponse as any);

      const result = await aiApi.updateEngineParams({ threads: 8 });

      expect(apiClient.put).toHaveBeenCalledWith('/ai/engine-params', { threads: 8 });
      expect(result).toEqual(mockParams);
    });
  });

  describe('getTuningData', () => {
    it('should call GET /ai/tuning', async () => {
      const mockTuningData = {
        winRates: { 1: 0.1, 2: 0.2, 3: 0.3 },
        avgGameDuration: { 1: 300, 2: 600, 3: 900 },
        playerFeedback: [],
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockTuningData,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await aiApi.getTuningData();

      expect(apiClient.get).toHaveBeenCalledWith('/ai/tuning');
      expect(result).toEqual(mockTuningData);
    });
  });
});
