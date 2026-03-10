import { describe, it, expect, beforeEach, vi } from 'vitest';
import { authApi } from '../auth';
import apiClient from '../index';
import type { LoginRequest } from '../../types';

vi.mock('../index', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('authApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('should call POST /auth/login with credentials', async () => {
      const mockCredentials: LoginRequest = {
        username: 'testuser',
        password: 'password123',
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: {
            token: 'mock-token',
            user: {
              id: '1',
              username: 'testuser',
              role: 'super_admin',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse as any);

      const result = await authApi.login(mockCredentials);

      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', mockCredentials);
      expect(result).toEqual({
        token: 'mock-token',
        user: {
          id: '1',
          username: 'testuser',
          role: 'super_admin',
        },
      });
    });
  });

  describe('logout', () => {
    it('should call POST /auth/logout', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: {} });

      await authApi.logout();

      expect(apiClient.post).toHaveBeenCalledWith('/auth/logout');
    });
  });

  describe('getCurrentUser', () => {
    it('should call GET /auth/me and return user info', async () => {
      const mockUser = {
        id: '1',
        username: 'admin',
        role: 'super_admin' as const,
        permissions: ['read', 'write', 'delete'],
      };

      const mockResponse = {
        data: {
          code: 200,
          message: 'Success',
          data: mockUser,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse as any);

      const result = await authApi.getCurrentUser();

      expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(mockUser);
    });
  });
});
