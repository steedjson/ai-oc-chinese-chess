/**
 * API Service 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { 
  setTokens, 
  getAccessToken, 
  clearTokens, 
  checkOnlineStatus,
  onOffline,
  onOnline,
} from './api';

// 完全 Mock axios
vi.mock('axios', () => {
  const mockAxios: any = vi.fn((config) => Promise.resolve({ data: { success: true }, status: 200 }));
  mockAxios.create = vi.fn(() => mockAxios);
  mockAxios.interceptors = {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  };
  mockAxios.get = vi.fn(() => Promise.resolve({ data: { success: true } }));
  mockAxios.post = vi.fn(() => Promise.resolve({ data: { success: true } }));
  mockAxios.put = vi.fn(() => Promise.resolve({ data: { success: true } }));
  mockAxios.delete = vi.fn(() => Promise.resolve({ data: { success: true } }));
  
  return {
    default: mockAxios,
    isAxiosError: vi.fn((err) => err && (err.name === 'AxiosError' || err.isAxiosError)),
    AxiosError: class AxiosError extends Error {
      code?: string;
      response?: any;
      isAxiosError = true;
      constructor(message: string) {
        super(message);
        this.name = 'AxiosError';
      }
    }
  };
});

describe('API Service', () => {
  beforeEach(() => {
    localStorage.clear();
    clearTokens();
    vi.clearAllMocks();
  });

  describe('Token Management', () => {
    it('应该正确管理 Access Token', () => {
      setTokens('access_123', 'refresh_456');
      expect(getAccessToken()).toBe('access_123');
      expect(localStorage.getItem('access_token')).toBe('access_123');
      expect(localStorage.getItem('refresh_token')).toBe('refresh_456');
      
      clearTokens();
      expect(getAccessToken()).toBeNull();
      expect(localStorage.getItem('access_token')).toBeNull();
    });

    it('getAccessToken 应该在本地缓存有数据时自动加载', () => {
      localStorage.setItem('access_token', 'cached_token');
      expect(getAccessToken()).toBe('cached_token');
    });

    it('initTokens 应该正确加载', async () => {
      const { initTokens } = await import('./api');
      localStorage.setItem('access_token', 'acc');
      localStorage.setItem('refresh_token', 'ref');
      initTokens();
      expect(getAccessToken()).toBe('acc');
    });
  });

  describe('Error Codes and Messages', () => {
    it('应该覆盖各种错误状态码', async () => {
      const { apiClient, request } = await import('./api');
      const codes = [400, 401, 403, 404, 408, 409, 429, 500, 502, 503, 504, 999];
      
      for (const status of codes) {
        vi.mocked(apiClient as any).mockRejectedValueOnce({
          isAxiosError: true,
          response: { status, data: { error: 'err' } }
        });
        const res = await request({ url: '/' });
        expect(res.success).toBe(false);
      }
    });

    it('应该处理非 Axios 错误', async () => {
      const { apiClient, request } = await import('./api');
      vi.mocked(apiClient as any).mockRejectedValueOnce(new Error('Generic Error'));
      const res = await request({ url: '/' });
      expect(res.success).toBe(false);
      expect(res.error?.code).toBe('UNKNOWN_ERROR');
    });
  });

  describe('HTTP Methods Expansion', () => {
    it('应该支持所有 HTTP 动词', async () => {
      const { http } = await import('./api');
      await http.post('/test', { a: 1 });
      await http.put('/test', { a: 1 });
      await http.patch('/test', { a: 1 });
      await http.delete('/test');
    });
  });

  describe('Network Status', () => {
    it('应该反映在线状态', () => {
      expect(typeof checkOnlineStatus()).toBe('boolean');
    });

    it('应该允许注册网络状态回调并能够注销', () => {
      const offlineCb = vi.fn();
      const onlineCb = vi.fn();
      
      const unregOffline = onOffline(offlineCb);
      const unregOnline = onOnline(onlineCb);
      
      expect(typeof unregOffline).toBe('function');
      expect(typeof unregOnline).toBe('function');
      
      unregOffline();
      unregOnline();
    });
  });

  describe('HTTP Methods', () => {
    it('http.get 应该能够正常返回', async () => {
      const { http } = await import('./api');
      const res = await http.get('/test');
      expect(res.success).toBe(true);
    });

    it('当 apiClient 抛出错误时，request 应该捕获并返回统一格式', async () => {
      const { apiClient, request } = await import('./api');
      
      const errorResponse = {
        name: 'AxiosError',
        message: 'Network Error',
        isAxiosError: true,
        response: {
          status: 500,
          data: { error: 'some error' }
        }
      };

      vi.mocked(apiClient as any).mockRejectedValueOnce(errorResponse);
      
      const result = await request({ url: '/error', method: 'GET' });
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('WebSocket URL', () => {
    it('应该正确生成 WebSocket URL', async () => {
      const { getWebSocketUrl } = await import('./api');
      setTokens('token123');
      const url = getWebSocketUrl('game/1');
      expect(url).toContain('ws://');
      expect(url).toContain('token=token123');
    });
  });
});
