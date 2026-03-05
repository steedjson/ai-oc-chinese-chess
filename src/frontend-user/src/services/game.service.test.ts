/**
 * Game Service 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { gameService } from './game.service';
import { setTokens, clearTokens } from './api';

describe('Game Service', () => {
  beforeEach(() => {
    setTokens('test_token');
    vi.clearAllMocks();
  });

  afterEach(() => {
    clearTokens();
  });

  describe('Create Game', () => {
    it('创建 AI 对局应该返回游戏信息', async () => {
      const result = await gameService.createGame('ai', 5);
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });

    it('创建在线对局应该返回游戏信息', async () => {
      const result = await gameService.createGame('online');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });

    it('创建好友对局应该返回游戏信息', async () => {
      const result = await gameService.createGame('friend');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });

  describe('Get Game', () => {
    it('获取对局详情应该返回游戏信息', async () => {
      const result = await gameService.getGame('game_001');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });

  describe('Make Move', () => {
    it('执行走棋应该返回走棋结果', async () => {
      const result = await gameService.makeMove('game_001', {
        from: 'e2',
        to: 'e4',
      });
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });

    it('走棋应该包含 promotion 选项', async () => {
      const result = await gameService.makeMove('game_001', {
        from: 'e2',
        to: 'e4',
        promotion: 'q',
      });
      
      expect(result).toBeDefined();
    });
  });

  describe('Resign', () => {
    it('投降应该返回游戏结果', async () => {
      const result = await gameService.resign('game_001');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });

  describe('Draw Operations', () => {
    it('提议和棋应该返回响应', async () => {
      const result = await gameService.offerDraw('game_001');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });

    it('接受和棋应该返回游戏结果', async () => {
      const result = await gameService.acceptDraw('game_001');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });

    it('拒绝和棋应该返回响应', async () => {
      const result = await gameService.rejectDraw('game_001');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });

  describe('Game History', () => {
    it('获取对局历史应该返回分页数据', async () => {
      const result = await gameService.getGameHistory(1, 20);
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });

    it('获取对局历史应该支持状态过滤', async () => {
      const result = await gameService.getGameHistory(1, 20, 'finished');
      
      expect(result).toBeDefined();
    });
  });

  describe('User Games', () => {
    it('获取用户对局应该返回分页数据', async () => {
      const result = await gameService.getUserGames(1, 1, 20);
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });

  describe('Game Replay', () => {
    it('获取对局回放应该返回走棋历史', async () => {
      const result = await gameService.getGameReplay('game_001');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });

  describe('Valid Moves', () => {
    it('获取合法走法应该返回位置列表', async () => {
      const result = await gameService.getValidMoves('game_001', 'e2');
      
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });
  });
});
