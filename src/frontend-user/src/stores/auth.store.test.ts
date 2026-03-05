/**
 * Auth Store 测试
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from './auth.store';
import type { User } from '@/types';

// Mock user
const mockUser: User = {
  id: 1,
  username: 'test_user',
  email: 'test@example.com',
  nickname: '测试玩家',
  avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=test',
  rating: 2100,
  total_games: 100,
  wins: 60,
  losses: 30,
  draws: 10,
  is_active: true,
  created_at: '2024-01-15T08:00:00Z',
};

describe('Auth Store', () => {
  beforeEach(() => {
    // 重置 store 状态
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: true,
    });
  });

  describe('Initial State', () => {
    it('应该有正确的初始状态', () => {
      const state = useAuthStore.getState();
      
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(true);
    });
  });

  describe('Set User', () => {
    it('设置用户应该更新状态', () => {
      useAuthStore.getState().setUser(mockUser);
      
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
    });

    it('设置 null 用户应该登出', () => {
      useAuthStore.getState().setUser(mockUser);
      useAuthStore.getState().setUser(null);
      
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('Set Loading', () => {
    it('设置加载状态应该更新 isLoading', () => {
      useAuthStore.getState().setLoading(true);
      expect(useAuthStore.getState().isLoading).toBe(true);
      
      useAuthStore.getState().setLoading(false);
      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('Logout', () => {
    it('登出应该重置状态', () => {
      useAuthStore.getState().setUser(mockUser);
      useAuthStore.getState().logout();
      
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('Update Rating', () => {
    it('更新评分应该修改用户 rating', () => {
      useAuthStore.getState().setUser(mockUser);
      useAuthStore.getState().updateRating(2200);
      
      const state = useAuthStore.getState();
      expect(state.user?.rating).toBe(2200);
    });

    it('没有用户时更新评分应该不报错', () => {
      expect(() => {
        useAuthStore.getState().updateRating(2200);
      }).not.toThrow();
    });
  });

  describe('Update Stats', () => {
    it('更新统计数据应该修改用户信息', () => {
      useAuthStore.getState().setUser(mockUser);
      useAuthStore.getState().updateStats({
        total_games: 150,
        wins: 90,
      });
      
      const state = useAuthStore.getState();
      expect(state.user?.total_games).toBe(150);
      expect(state.user?.wins).toBe(90);
    });

    it('更新统计数据应该保留其他字段', () => {
      useAuthStore.getState().setUser(mockUser);
      useAuthStore.getState().updateStats({ wins: 90 });
      
      const state = useAuthStore.getState();
      expect(state.user?.rating).toBe(2100);
      expect(state.user?.wins).toBe(90);
    });

    it('没有用户时更新统计应该不报错', () => {
      expect(() => {
        useAuthStore.getState().updateStats({ wins: 90 });
      }).not.toThrow();
    });
  });

  describe('Persistence', () => {
    it('应该持久化用户状态', () => {
      useAuthStore.getState().setUser(mockUser);
      
      // 检查 localStorage
      const stored = localStorage.getItem('auth-storage');
      expect(stored).toBeDefined();
      
      const parsed = JSON.parse(stored!);
      expect(parsed.state.user).toEqual(mockUser);
      expect(parsed.state.isAuthenticated).toBe(true);
    });
  });
});
