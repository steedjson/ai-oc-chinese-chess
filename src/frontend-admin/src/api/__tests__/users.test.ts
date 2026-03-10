import { describe, it, expect, beforeEach, vi } from 'vitest';
import { usersApi } from '../users';
import apiClient from '../index';
import type { UserListParams } from '../../types';

vi.mock('../index', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('usersApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getList', () => {
    it('should call GET /users with params', async () => {
      const mockParams: UserListParams = {
        page: 1,
        pageSize: 10,
        search: 'test',
        status: 'active',
      };

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

      const result = await usersApi.getList(mockParams);

      expect(apiClient.get).toHaveBeenCalledWith('/users', { params: mockParams });
      expect(result).toEqual({
        data: [],
        total: 0,
        page: 1,
        pageSize: 10,
      });
    });
  });

  describe('getDetail', () => {
    it('should call GET /users/:id', async () => {
      const mockUser = {
        id: 'user-1',
        username: 'testuser',
        email: 'test@example.com',
        elo: 1200,
        status: 'active' as const,
        createdAt: '2024-01-01',
        totalGames: 10,
        wins: 5,
        losses: 3,
        draws: 2,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockUser,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await usersApi.getDetail('user-1');

      expect(apiClient.get).toHaveBeenCalledWith('/users/user-1');
      expect(result).toEqual(mockUser);
    });
  });

  describe('updateStatus', () => {
    it('should call PUT /users/:id/status with status', async () => {
      const mockUser = {
        id: 'user-1',
        username: 'testuser',
        status: 'banned' as const,
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockUser,
        },
      };

      vi.mocked(apiClient.put).mockResolvedValueOnce(mockResponse as any);

      const result = await usersApi.updateStatus('user-1', 'banned');

      expect(apiClient.put).toHaveBeenCalledWith('/users/user-1/status', { status: 'banned' });
      expect(result).toEqual(mockUser);
    });
  });

  describe('update', () => {
    it('should call PUT /users/:id with data', async () => {
      const mockUser = {
        id: 'user-1',
        username: 'updateduser',
        email: 'updated@example.com',
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockUser,
        },
      };

      vi.mocked(apiClient.put).mockResolvedValueOnce(mockResponse as any);

      const result = await usersApi.update('user-1', { username: 'updateduser' });

      expect(apiClient.put).toHaveBeenCalledWith('/users/user-1', { username: 'updateduser' });
      expect(result).toEqual(mockUser);
    });
  });

  describe('delete', () => {
    it('should call DELETE /users/:id', async () => {
      vi.mocked(apiClient.delete).mockResolvedValueOnce({});

      await usersApi.delete('user-1');

      expect(apiClient.delete).toHaveBeenCalledWith('/users/user-1');
    });
  });
});
