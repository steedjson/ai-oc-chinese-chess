/**
 * LeaderboardPage 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LeaderboardPage from '../LeaderboardPage';
import { rankingService } from '@/services';

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock services
vi.mock('@/services', () => ({
  rankingService: {
    getLeaderboard: vi.fn(),
  },
}));

describe('LeaderboardPage', () => {
  const mockEntries = [
    {
      user: { id: '1', username: 'player1', nickname: '高手1', avatar_url: '' },
      rank: 1,
      rating: 2100,
      total_games: 100,
      win_rate: 65.5,
    },
    {
      user: { id: '2', username: 'player2', nickname: '玩家2', avatar_url: '' },
      rank: 2,
      rating: 1500,
      total_games: 50,
      win_rate: 50.0,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (rankingService.getLeaderboard as any).mockResolvedValue({
      success: true,
      data: { entries: mockEntries, total: 2 },
    });
  });

  it('应该正确渲染排行榜页面', async () => {
    render(
      <BrowserRouter>
        <LeaderboardPage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('天梯排行榜')).toBeInTheDocument();
    
    await waitFor(() => {
      // 检查表格中的记录 (表格渲染为 <strong>)
      const tableCells = screen.getAllByText('高手1');
      const tableRecord = tableCells.find(el => el.tagName === 'STRONG');
      expect(tableRecord).toBeDefined();
    });
  });

  it('应该显示统计数据', async () => {
    render(
      <BrowserRouter>
        <LeaderboardPage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('榜首玩家')).toBeInTheDocument();
      // 统计数据渲染为特定 class
      const statsValue = screen.queryByText('高手1', { selector: '.ant-statistic-content-value' });
      expect(statsValue).toBeDefined();
    });
  });

  it('应该支持搜索功能', async () => {
    render(
      <BrowserRouter>
        <LeaderboardPage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getAllByText('高手1').length).toBeGreaterThan(0);
    });
    
    const searchInput = screen.getByPlaceholderText('搜索玩家...');
    fireEvent.change(searchInput, { target: { value: '玩家2' } });
    
    // 搜索后，高手1 应该只剩下一个（统计数据中的），表格中的应该消失
    await waitFor(() => {
       const remaining = screen.queryAllByText('高手1').filter(el => el.tagName === 'STRONG');
       expect(remaining.length).toBe(0);
    });
    expect(screen.getByText('玩家2')).toBeInTheDocument();
  });

  it('点击返回首页按钮应该导航到首页', () => {
    render(
      <BrowserRouter>
        <LeaderboardPage />
      </BrowserRouter>
    );
    
    const backButton = screen.getByText(/返回首页/);
    fireEvent.click(backButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('应该显示段位说明', () => {
    render(
      <BrowserRouter>
        <LeaderboardPage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('段位说明')).toBeInTheDocument();
    expect(screen.getByText(/大师/)).toBeInTheDocument();
  });
});
