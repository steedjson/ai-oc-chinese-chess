import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useHasPermission } from '../useHasPermission';
import { useAuthStore } from '../../stores/auth';
import type { UserRole } from '../../types';

describe('useHasPermission', () => {
  beforeEach(() => {
    // 重置 auth store
    useAuthStore.setState({
      token: null,
      user: null,
      isAuthenticated: false,
    });
  });

  describe('when not authenticated', () => {
    it('should return false for all permission checks', () => {
      const { result } = renderHook(() => useHasPermission());

      expect(result.current.checkPermission('super_admin')).toBe(false);
      expect(result.current.checkPermission('ops')).toBe(false);
      expect(result.current.isSuperAdmin).toBe(false);
      expect(result.current.isOps).toBe(false);
      expect(result.current.role).toBeUndefined();
    });
  });

  describe('when user is super_admin', () => {
    beforeEach(() => {
      useAuthStore.setState({
        user: {
          id: '1',
          username: 'admin',
          role: 'super_admin' as UserRole,
        },
        isAuthenticated: true,
      });
    });

    it('should return true for super_admin check', () => {
      const { result } = renderHook(() => useHasPermission());

      expect(result.current.isSuperAdmin).toBe(true);
      expect(result.current.isOps).toBe(false);
      expect(result.current.role).toBe('super_admin');
    });

    it('should check single role correctly', () => {
      const { result } = renderHook(() => useHasPermission());

      expect(result.current.checkPermission('super_admin')).toBe(true);
      expect(result.current.checkPermission('ops')).toBe(false);
    });

    it('should check multiple roles correctly', () => {
      const { result } = renderHook(() => useHasPermission());

      expect(result.current.checkPermission(['super_admin'])).toBe(true);
      expect(result.current.checkPermission(['ops'])).toBe(false);
      expect(result.current.checkPermission(['super_admin', 'ops'])).toBe(true);
      expect(result.current.checkPermission(['ops', 'admin'])).toBe(false);
    });
  });

  describe('when user is ops', () => {
    beforeEach(() => {
      useAuthStore.setState({
        user: {
          id: '2',
          username: 'operator',
          role: 'ops' as UserRole,
        },
        isAuthenticated: true,
      });
    });

    it('should return true for ops check', () => {
      const { result } = renderHook(() => useHasPermission());

      expect(result.current.isSuperAdmin).toBe(false);
      expect(result.current.isOps).toBe(true);
      expect(result.current.role).toBe('ops');
    });

    it('should check single role correctly', () => {
      const { result } = renderHook(() => useHasPermission());

      expect(result.current.checkPermission('super_admin')).toBe(false);
      expect(result.current.checkPermission('ops')).toBe(true);
    });

    it('should check multiple roles correctly', () => {
      const { result } = renderHook(() => useHasPermission());

      expect(result.current.checkPermission(['ops'])).toBe(true);
      expect(result.current.checkPermission(['super_admin'])).toBe(false);
      expect(result.current.checkPermission(['super_admin', 'ops'])).toBe(true);
    });
  });

  describe('checkPermission with array of roles', () => {
    beforeEach(() => {
      useAuthStore.setState({
        user: {
          id: '1',
          username: 'admin',
          role: 'super_admin' as UserRole,
        },
        isAuthenticated: true,
      });
    });

    it('should return true if user role is in the allowed roles array', () => {
      const { result } = renderHook(() => useHasPermission());

      expect(result.current.checkPermission(['ops', 'super_admin'])).toBe(true);
    });

    it('should return false if user role is not in the allowed roles array', () => {
      const { result } = renderHook(() => useHasPermission());

      // 改变用户角色为 ops
      useAuthStore.setState({
        user: {
          id: '2',
          username: 'operator',
          role: 'ops' as UserRole,
        },
      });

      const { result: newResult } = renderHook(() => useHasPermission());
      expect(newResult.current.checkPermission(['super_admin'])).toBe(false);
    });
  });
});
