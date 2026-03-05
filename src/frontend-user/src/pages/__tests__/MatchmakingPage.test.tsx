/**
 * MatchmakingPage 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import MatchmakingPage from '../MatchmakingPage';
import * as stores from '@/stores';
import { matchmakingService } from '@/services';

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
    useMatchmakingStore: vi.fn(),
    useGameStore: vi.fn(),
  };
});

// Mock services
vi.mock('@/services', () => ({
  matchmakingService: {
    joinQueue: vi.fn(),
    cancelMatch: vi.fn(),
    getStatus: vi.fn(),
  },
  gameService: {
    makeMove: vi.fn(),
    resign: vi.fn(),
  },
  getWebSocketService: () => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
  }),
}));

describe('MatchmakingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // 默认已登录
    (stores.useAuthStore as any).mockReturnValue({ isAuthenticated: true });
    // 默认未匹配中
    (stores.useMatchmakingStore as any).mockReturnValue({
      isMatching: false,
      status: null,
      startMatching: vi.fn(),
      stopMatching: vi.fn(),
      updateStatus: vi.fn(),
      reset: vi.fn(),
    });
    // 默认无游戏
    (stores.useGameStore as any).mockReturnValue({
      currentGame: null,
      boardState: null,
      isMyTurn: false,
      myColor: 'red',
      gameOver: false,
      resetGame: vi.fn(),
      makeMove: vi.fn(),
      setGameOver: vi.fn(),
      updateFen: vi.fn(),
      setBoardState: vi.fn(),
      setCurrentGame: vi.fn(),
      setMyTurn: vi.fn(),
    });
  });

  it('应该渲染初始匹配界面', () => {
    render(
      <BrowserRouter>
        <MatchmakingPage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('在线匹配')).toBeInTheDocument();
    expect(screen.getByText(/开始匹配/)).toBeInTheDocument();
  });

  it('点击开始匹配应该调用 joinQueue', async () => {
    (matchmakingService.joinQueue as any).mockResolvedValue({ success: true, data: {} });
    const { container } = render(
      <BrowserRouter>
        <MatchmakingPage />
      </BrowserRouter>
    );
    
    const startButton = Array.from(container.querySelectorAll('button')).find(b => b.textContent?.includes('开始匹配'));
    if (startButton) fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(matchmakingService.joinQueue).toHaveBeenCalled();
    });
  });

  it('应该渲染正在匹配界面', () => {
    (stores.useMatchmakingStore as any).mockReturnValue({
      isMatching: true,
      status: { search_range: 100 },
      startMatching: vi.fn(),
      stopMatching: vi.fn(),
      updateStatus: vi.fn(),
      reset: vi.fn(),
    });

    render(
      <BrowserRouter>
        <MatchmakingPage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('正在匹配对手')).toBeInTheDocument();
    expect(screen.getByText(/取消匹配/)).toBeInTheDocument();
  });

  it('匹配成功并有 currentGame 时应该渲染游戏界面', () => {
    (stores.useGameStore as any).mockReturnValue({
      currentGame: { id: 'game_1' },
      boardState: { fen: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR', turn: 'red', pieces: [] },
      isMyTurn: true,
      myColor: 'red',
      gameOver: false,
      resetGame: vi.fn(),
      makeMove: vi.fn(),
      setGameOver: vi.fn(),
      updateFen: vi.fn(),
      setBoardState: vi.fn(),
      setCurrentGame: vi.fn(),
      setMyTurn: vi.fn(),
    });

    render(
      <BrowserRouter>
        <MatchmakingPage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('轮到你走棋')).toBeInTheDocument();
    // 检查 ChessBoard 容器
    expect(document.querySelector('.chess-board')).toBeInTheDocument();
  });
});
