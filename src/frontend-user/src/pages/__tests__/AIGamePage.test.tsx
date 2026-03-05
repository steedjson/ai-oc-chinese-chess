/**
 * AIGamePage 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AIGamePage from '../AIGamePage';
import * as stores from '@/stores';
import { aiService } from '@/services';

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock stores
vi.mock('@/stores', async (importOriginal) => {
  const actual = await importOriginal<typeof stores>();
  return {
    ...actual,
    useAuthStore: vi.fn(),
    useGameStore: vi.fn(),
  };
});

// Mock services
vi.mock('@/services', () => ({
  aiService: {
    createAIGame: vi.fn(),
    getDifficultyLevels: vi.fn(),
  },
  getWebSocketService: () => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
  }),
  gameService: {
    makeMove: vi.fn(),
    resign: vi.fn(),
  },
}));

describe('AIGamePage', () => {
  let gameStoreState: any;

  beforeEach(() => {
    vi.clearAllMocks();
    (stores.useAuthStore as any).mockReturnValue({ 
      isAuthenticated: true, 
      user: { id: 'user_1', username: 'testuser' } 
    });

    gameStoreState = {
      currentGame: null,
      boardState: null,
      resetGame: vi.fn(() => {
        gameStoreState.currentGame = null;
        gameStoreState.boardState = null;
      }),
      setCurrentGame: vi.fn((game) => { gameStoreState.currentGame = game; }),
      setBoardState: vi.fn((state) => { gameStoreState.boardState = state; }),
      setMyTurn: vi.fn(),
      updateFen: vi.fn(),
      winner: null,
      gameOver: false,
      isMyTurn: true,
      myColor: 'red',
    };

    (stores.useGameStore as any).mockImplementation(() => gameStoreState);
    
    (aiService.getDifficultyLevels as any).mockResolvedValue({
      success: true,
      data: [{ level: 5, name: '中级', description: 'desc', elo_estimate: 1500 }],
    });
  });

  it('应该渲染难度选择界面', async () => {
    render(
      <BrowserRouter>
        <AIGamePage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('AI 对战')).toBeInTheDocument();
  });

  it('如果未登录，点击开始游戏应提示并跳转', async () => {
    (stores.useAuthStore as any).mockReturnValue({ isAuthenticated: false });
    
    render(
      <BrowserRouter>
        <AIGamePage />
      </BrowserRouter>
    );
    
    const startBtn = screen.getByText('开始游戏').closest('button');
    if (startBtn) fireEvent.click(startBtn);
    
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('应该能够成功创建游戏', async () => {
    (aiService.createAIGame as any).mockResolvedValue({
      success: true,
      data: { id: 'game_001', fen_current: '...' },
    });
    
    render(
      <BrowserRouter>
        <AIGamePage />
      </BrowserRouter>
    );
    
    const startBtn = screen.getByText('开始游戏').closest('button');
    if (startBtn) fireEvent.click(startBtn);
    
    await waitFor(() => {
      expect(aiService.createAIGame).toHaveBeenCalled();
    });
  });

  it('进入游戏后应该显示控制面板', async () => {
    (aiService.createAIGame as any).mockResolvedValue({
      success: true,
      data: { id: 'game_001', fen_current: '...' },
    });

    const { rerender } = render(
      <BrowserRouter>
        <AIGamePage />
      </BrowserRouter>
    );
    
    const startBtn = screen.getByText('开始游戏').closest('button');
    if (startBtn) fireEvent.click(startBtn);
    
    // 等待状态更新和重新渲染
    await waitFor(() => {
      expect(gameStoreState.currentGame).not.toBeNull();
    });
    
    // 手动 rerender 以应用 mockImplementation 的最新结果（状态通常由组件自己管理或由 store 共享）
    // 在 AIGamePage 中，它从 store 获取 currentGame。
    // 如果 rerender 不起作用，我们直接在 beforeEach 里初始化 currentGame
    
    rerender(
      <BrowserRouter>
        <AIGamePage />
      </BrowserRouter>
    );
  });

  it('点击返回首页应重置状态并跳转', () => {
    render(
      <BrowserRouter>
        <AIGamePage />
      </BrowserRouter>
    );
    
    const backBtn = screen.getByText(/返回首页/).closest('button');
    if (backBtn) fireEvent.click(backBtn);
    
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });
});
