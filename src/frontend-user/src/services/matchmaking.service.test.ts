/**
 * Matchmaking Service 测试
 */

import { describe, it, expect, vi } from 'vitest';
import { matchmakingService } from './matchmaking.service';
import { http } from './api';

// Mock http
vi.mock('./api', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Matchmaking Service', () => {
  it('加入队列应该发送 POST 请求', async () => {
    (http.post as any).mockResolvedValue({ success: true });
    await matchmakingService.joinQueue();
    expect(http.post).toHaveBeenCalledWith('/matchmaking/');
  });

  it('取消匹配应该发送 DELETE 请求', async () => {
    (http.delete as any).mockResolvedValue({ success: true });
    await matchmakingService.cancelMatch();
    expect(http.delete).toHaveBeenCalledWith('/matchmaking/');
  });

  it('获取状态应该发送 GET 请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    await matchmakingService.getStatus();
    expect(http.get).toHaveBeenCalledWith('/matchmaking/status/');
  });

  it('接受匹配应该发送 POST 请求', async () => {
    (http.post as any).mockResolvedValue({ success: true });
    await matchmakingService.acceptMatch('match_123');
    expect(http.post).toHaveBeenCalledWith('/matchmaking/match_123/accept/');
  });

  it('拒绝匹配应该发送 POST 请求', async () => {
    (http.post as any).mockResolvedValue({ success: true });
    await matchmakingService.rejectMatch('match_123');
    expect(http.post).toHaveBeenCalledWith('/matchmaking/match_123/reject/');
  });
});
