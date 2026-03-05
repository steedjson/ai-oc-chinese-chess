/**
 * AI Service 测试
 */

import { describe, it, expect, vi } from 'vitest';
import { aiService } from './ai.service';
import { http } from './api';

// Mock http
vi.mock('./api', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('AI Service', () => {
  it('创建 AI 对局应该发送正确的请求', async () => {
    (http.post as any).mockResolvedValue({ success: true });
    
    await aiService.createAIGame(5, 'red');
    
    expect(http.post).toHaveBeenCalledWith('/ai/games/', {
      difficulty: 5,
      player_color: 'red',
    });
  });

  it('获取 AI 走棋应该发送正确的请求', async () => {
    (http.post as any).mockResolvedValue({ success: true });
    
    await aiService.getAIMove('game_001');
    
    expect(http.post).toHaveBeenCalledWith('/ai/games/game_001/move/');
  });

  it('获取走棋提示应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await aiService.getHint('game_001', 5);
    
    expect(http.get).toHaveBeenCalledWith('/ai/games/game_001/hint/?count=5');
  });

  it('分析局面应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await aiService.analyzePosition('game_001', 15);
    
    expect(http.get).toHaveBeenCalledWith('/ai/games/game_001/analyze/?depth=15');
  });

  it('获取难度等级应该发送正确的请求', async () => {
    (http.get as any).mockResolvedValue({ success: true });
    
    await aiService.getDifficultyLevels();
    
    expect(http.get).toHaveBeenCalledWith('/ai/difficulty-levels/');
  });
});
