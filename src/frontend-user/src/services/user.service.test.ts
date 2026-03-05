/**
 * User Service 测试
 */

import { describe, it, expect, vi } from 'vitest';
import { userService } from './user.service';
import { http } from './api';

// Mock http
vi.mock('./api', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

describe('User Service', () => {
  it('获取用户详情应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    await userService.getUser(123);
    expect(http.get).toHaveBeenCalledWith('/users/123/');
  });

  it('获取当前资料应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    await userService.getProfile();
    expect(http.get).toHaveBeenCalledWith('/users/profile/');
  });

  it('更新资料应该发送正确的请求', async () => {
    (http.put as any).mockResolvedValue({ success: true });
    const profile = { nickname: 'new name' };
    await userService.updateProfile(profile);
    expect(http.put).toHaveBeenCalledWith('/users/profile/', profile);
  });

  it('上传头像应该发送正确的 FormData', async () => {
    (http.post as any).mockResolvedValue({ success: true });
    const file = new File([''], 'avatar.png', { type: 'image/png' });
    await userService.uploadAvatar(file);
    
    expect(http.post).toHaveBeenCalledWith('/users/profile/avatar/', expect.any(FormData), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  });

  it('获取用户对局应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    await userService.getUserGames(123, 2, 10);
    expect(http.get).toHaveBeenCalledWith('/users/123/games/?page=2&page_size=10');
  });

  it('获取用户统计应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    await userService.getUserStats();
    expect(http.get).toHaveBeenCalledWith('/users/me/stats/');
    
    await userService.getUserStats(123);
    expect(http.get).toHaveBeenCalledWith('/users/123/stats/');
  });
});
