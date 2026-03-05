/**
 * Game Store 测试
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useGameStore } from './game.store';
import type { Game, Move, BoardState } from '@/types';

// Mock Game
const mockGame: Game = {
  id: 'game_001',
  red_player: {
    id: 1,
    username: 'test_user',
    avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=test',
    rating: 2100,
  },
  black_player: {
    id: 2,
    username: 'ai_opponent',
    avatar_url: 'https://api.dicebear.com/7.x/bottts/svg?seed=ai',
    rating: 2800,
  },
  game_type: 'ai',
  status: 'playing',
  fen_start: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
  fen_current: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
  move_history: [],
  ai_level: 5,
  is_rated: true,
  created_at: '2024-03-03T10:00:00Z',
};

// Mock Move
const mockMove: Move = {
  from: 'e2',
  to: 'e4',
  piece: 'C',
  captured: undefined,
  fen: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 2',
  timestamp: Date.now(),
  player_id: 1,
};

// Mock BoardState
const mockBoardState: BoardState = {
  fen: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
  turn: 'red',
  pieces: [],
  in_check: false,
  game_over: false,
  last_move: undefined,
};

describe('Game Store', () => {
  beforeEach(() => {
    // 重置 store 状态
    useGameStore.setState({
      currentGame: null,
      boardState: null,
      isPlaying: false,
      isMyTurn: false,
      myColor: null,
      opponentColor: null,
      selectedPosition: null,
      validMoves: [],
      lastMove: null,
      isAnimating: false,
      gameOver: false,
      winner: null,
      gameResult: null,
    });
  });

  describe('Initial State', () => {
    it('应该有正确的初始状态', () => {
      const state = useGameStore.getState();
      
      expect(state.currentGame).toBeNull();
      expect(state.boardState).toBeNull();
      expect(state.isPlaying).toBe(false);
      expect(state.isMyTurn).toBe(false);
      expect(state.myColor).toBeNull();
      expect(state.selectedPosition).toBeNull();
      expect(state.validMoves).toEqual([]);
      expect(state.gameOver).toBe(false);
    });
  });

  describe('Set Current Game', () => {
    it('设置游戏应该更新状态', () => {
      useGameStore.getState().setCurrentGame(mockGame);
      
      const state = useGameStore.getState();
      expect(state.currentGame).toEqual(mockGame);
      expect(state.isPlaying).toBe(true);
      expect(state.myColor).toBe('red');
      expect(state.opponentColor).toBe('black');
    });

    it('设置 null 游戏应该重置状态', () => {
      useGameStore.getState().setCurrentGame(mockGame);
      useGameStore.getState().setCurrentGame(null);
      
      const state = useGameStore.getState();
      expect(state.currentGame).toBeNull();
    });
  });

  describe('Set Board State', () => {
    it('设置棋盘状态应该更新 boardState', () => {
      useGameStore.getState().setBoardState(mockBoardState);
      
      const state = useGameStore.getState();
      expect(state.boardState).toEqual(mockBoardState);
    });
  });

  describe('Set My Turn', () => {
    it('设置回合状态应该更新 isMyTurn', () => {
      useGameStore.getState().setMyTurn(true);
      expect(useGameStore.getState().isMyTurn).toBe(true);
      
      useGameStore.getState().setMyTurn(false);
      expect(useGameStore.getState().isMyTurn).toBe(false);
    });
  });

  describe('Set My Color', () => {
    it('设置玩家颜色应该更新 myColor 和 opponentColor', () => {
      useGameStore.getState().setMyColor('red');
      
      const state = useGameStore.getState();
      expect(state.myColor).toBe('red');
      expect(state.opponentColor).toBe('black');
    });

    it('设置黑色应该交换对手颜色', () => {
      useGameStore.getState().setMyColor('black');
      
      const state = useGameStore.getState();
      expect(state.myColor).toBe('black');
      expect(state.opponentColor).toBe('red');
    });
  });

  describe('Selected Position', () => {
    it('设置选中位置应该更新 selectedPosition', () => {
      useGameStore.getState().setSelectedPosition('e2');
      expect(useGameStore.getState().selectedPosition).toBe('e2');
      
      useGameStore.getState().setSelectedPosition(null);
      expect(useGameStore.getState().selectedPosition).toBeNull();
    });
  });

  describe('Valid Moves', () => {
    it('设置有效走法应该更新 validMoves', () => {
      useGameStore.getState().setValidMoves(['e3', 'e4']);
      expect(useGameStore.getState().validMoves).toEqual(['e3', 'e4']);
    });
  });

  describe('Make Move', () => {
    it('走棋应该更新状态', () => {
      useGameStore.getState().setCurrentGame(mockGame);
      useGameStore.getState().makeMove(mockMove);
      
      const state = useGameStore.getState();
      expect(state.lastMove).toEqual(mockMove);
      expect(state.selectedPosition).toBeNull();
      expect(state.validMoves).toEqual([]);
      expect(state.isMyTurn).toBe(false);
      expect(state.isAnimating).toBe(true);
    });
  });

  describe('Set Game Over', () => {
    it('设置游戏结束应该更新状态', () => {
      useGameStore.getState().setGameOver('red', '将死');
      
      const state = useGameStore.getState();
      expect(state.gameOver).toBe(true);
      expect(state.winner).toBe('red');
      expect(state.gameResult).toBe('将死');
      expect(state.isPlaying).toBe(false);
    });

    it('和棋应该正确设置', () => {
      useGameStore.getState().setGameOver(null, '和棋');
      
      const state = useGameStore.getState();
      expect(state.gameOver).toBe(true);
      expect(state.winner).toBeNull();
      expect(state.gameResult).toBe('和棋');
    });
  });

  describe('Reset Game', () => {
    it('重置游戏应该恢复初始状态', () => {
      useGameStore.getState().setCurrentGame(mockGame);
      useGameStore.getState().resetGame();
      
      const state = useGameStore.getState();
      expect(state.currentGame).toBeNull();
      expect(state.isPlaying).toBe(false);
    });
  });

  describe('Update FEN', () => {
    it('更新 FEN 应该更新棋盘状态', () => {
      useGameStore.getState().setBoardState(mockBoardState);
      useGameStore.getState().updateFen('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 2');
      
      const state = useGameStore.getState();
      expect(state.boardState?.fen).toContain('b - - 0 2');
    });

    it('没有棋盘状态时更新 FEN 应该创建新状态', () => {
      useGameStore.getState().updateFen('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1');
      
      const state = useGameStore.getState();
      expect(state.boardState).toBeDefined();
    });
  });
});
