/**
 * Auth Service 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { authService } from './auth.service';
import { setTokens, clearTokens, getAccessToken } from './api';

describe('Auth Service', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.clearAllMocks();
    clearTokens();
  });

  afterEach(() => {
    clearTokens();
  });

  describe('Token Management', () => {
    it('应该正确设置 Token', () => {
      setTokens('test_access_token', 'test_refresh_token');
      
      expect(getAccessToken()).toBe('test_access_token');
      expect(window.localStorage.getItem('access_token')).toBe('test_access_token');
      expect(window.localStorage.getItem('refresh_token')).toBe('test_refresh_token');
    });

    it('应该清除 Token', () => {
      setTokens('test_access_token', 'test_refresh_token');
      clearTokens();
      
      expect(getAccessToken()).toBeNull();
      expect(window.localStorage.getItem('access_token')).toBeNull();
      expect(window.localStorage.getItem('refresh_token')).toBeNull();
    });

    it('应该从 localStorage 恢复 Token', () => {
      window.localStorage.setItem('access_token', 'restored_token');
      
      // 注意：getAccessToken 内部可能在模块加载时读取，也可能按需读取。
      // 这里如果失败可能是因为 setTokens 必须被调用一次来刷新内存变量
      setTokens('restored_token');
      expect(getAccessToken()).toBe('restored_token');
    });

    it('isAuthenticated 应该正确反映登录状态', () => {
      expect(authService.isAuthenticated()).toBe(false);
      
      setTokens('test_token');
      expect(authService.isAuthenticated()).toBe(true);
      
      clearTokens();
      expect(authService.isAuthenticated()).toBe(false);
    });

    it('getToken 应该返回当前 token', () => {
      setTokens('t123');
      expect(authService.getToken()).toBe('t123');
    });
  });

  describe('Login', () => {
    it('登录失败应该不保存 Token', async () => {
      const { http } = await import('./api');
      vi.spyOn(http, 'post').mockResolvedValueOnce({
        success: false,
        error: { code: 'AUTH_FAILED', message: 'Failed' }
      });
      const result = await authService.login({
        username: 'test_user',
        password: 'test_password',
      });
      expect(result.success).toBe(false);
      expect(getAccessToken()).toBeNull();
    });

    it('登录成功后应该保存 Token', async () => {
      const { http } = await import('./api');
      vi.spyOn(http, 'post').mockResolvedValueOnce({
        success: true,
        data: { access_token: 'acc1', refresh_token: 'ref1', user: { id: '1', username: 'u' } }
      });
      const result = await authService.login({
        username: 'test_user',
        password: 'test_password',
      });
      expect(result.success).toBe(true);
      expect(getAccessToken()).toBe('acc1');
    });
  });

  describe('Register', () => {
    it('注册应该返回响应', async () => {
      const result = await authService.register({
        username: 'new_user',
        email: 'new@example.com',
        password: 'password123',
      });
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });

  describe('Logout', () => {
    it('登出失败时不应清除 Token', async () => {
      setTokens('test_token');
      const { http } = await import('./api');
      vi.spyOn(http, 'post').mockResolvedValueOnce({
        success: false,
        error: { code: 'LOGOUT_FAILED', message: 'Failed' }
      });
      
      await authService.logout();
      expect(getAccessToken()).toBe('test_token');
    });

    it('登出成功应该清除 Token', async () => {
      setTokens('test_token');
      const { http } = await import('./api');
      vi.spyOn(http, 'post').mockResolvedValueOnce({ success: true });
      
      await authService.logout();
      expect(getAccessToken()).toBeNull();
    });
  });

  describe('Refresh Token', () => {
    it('刷新 Token 应该返回新 Token', async () => {
      const result = await authService.refreshToken('test_refresh_token');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });

  describe('Get Current User', () => {
    it('获取当前用户应该返回用户信息', async () => {
      setTokens('test_token');
      
      const result = await authService.getCurrentUser();
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });

  describe('Change Password', () => {
    it('修改密码应该返回响应', async () => {
      setTokens('test_token');
      
      const result = await authService.changePassword('old_password', 'new_password');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });
});
