/**
 * Ranking Service 测试
 */

import { describe, it, expect, vi } from 'vitest';
import { rankingService } from './ranking.service';
import { http } from './api';

// Mock http
vi.mock('./api', () => ({
  http: {
    get: vi.fn(),
  },
}));

describe('Ranking Service', () => {
  it('获取排行榜应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await rankingService.getLeaderboard(2, 20, 'weekly');
    
    expect(http.get).toHaveBeenCalledWith('/rankings/leaderboard/?page=2&page_size=20&period=weekly');
  });

  it('获取用户排名应该发送正确的请求 (me)', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await rankingService.getUserRanking();
    
    expect(http.get).toHaveBeenCalledWith('/rankings/user/me/');
  });

  it('获取特定用户排名应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await rankingService.getUserRanking(123);
    
    expect(http.get).toHaveBeenCalledWith('/rankings/user/123/');
  });

  it('获取排名历史应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await rankingService.getRankHistory(undefined, 14);
    
    expect(http.get).toHaveBeenCalledWith('/rankings/history/?days=14');
  });

  it('获取特定用户排名历史应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await rankingService.getRankHistory(123, 7);
    
    expect(http.get).toHaveBeenCalledWith('/rankings/history/123/?days=7');
  });

  it('获取段位分布应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await rankingService.getRankDistribution();
    
    expect(http.get).toHaveBeenCalledWith('/rankings/distribution/');
  });

  it('搜索用户应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await rankingService.searchUsers('player', 10);
    
    expect(http.get).toHaveBeenCalledWith('/rankings/search/?q=player&limit=10');
  });
});
