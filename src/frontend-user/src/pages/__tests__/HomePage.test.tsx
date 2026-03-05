/**
 * HomePage 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import HomePage from '../HomePage';
import * as stores from '@/stores';

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// 完全 Mock stores 钩子
vi.mock('@/stores', async (importOriginal) => {
  const actual = await importOriginal<typeof stores>();
  return {
    ...actual,
    useAuthStore: vi.fn(),
  };
});

describe('HomePage', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it('应该正确渲染首页', () => {
    (stores.useAuthStore as any).mockReturnValue({ isAuthenticated: false, user: null });
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    expect(screen.getAllByText(/中国象棋/).length).toBeGreaterThan(0);
    expect(screen.getByText(/在线对战平台/)).toBeInTheDocument();
  });

  it('应该显示主要功能卡片', () => {
    (stores.useAuthStore as any).mockReturnValue({ isAuthenticated: false, user: null });
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    expect(screen.getAllByText(/AI/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/匹配/).length).toBeGreaterThan(0);
  });

  it('应该显示平台数据', () => {
    (stores.useAuthStore as any).mockReturnValue({ isAuthenticated: false, user: null });
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('注册用户')).toBeInTheDocument();
    expect(screen.getByText('在线玩家')).toBeInTheDocument();
  });

  it('点击 AI 对战按钮应该导航到 AI 对局页面', () => {
    (stores.useAuthStore as any).mockReturnValue({ isAuthenticated: false, user: null });
    const { container } = render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    // Ant Design 的按钮可能有内嵌 span。我们寻找包含相应文本且最近的 button
    const buttons = container.querySelectorAll('button');
    const aiButton = Array.from(buttons).find(b => b.textContent?.replace(/\s/g, '').includes('AI对战'));
    if (aiButton) fireEvent.click(aiButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/ai-game');
  });

  it('未登录时点击匹配对战应该导航到登录页面', () => {
    (stores.useAuthStore as any).mockReturnValue({ isAuthenticated: false, user: null });
    const { container } = render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    const buttons = container.querySelectorAll('button');
    const matchButton = Array.from(buttons).find(b => b.textContent?.replace(/\s/g, '').includes('匹配对战'));
    if (matchButton) fireEvent.click(matchButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('已登录时点击匹配对战应该导航到匹配页面', () => {
    (stores.useAuthStore as any).mockReturnValue({ isAuthenticated: true, user: { username: 'test' } });
    const { container } = render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    const buttons = container.querySelectorAll('button');
    const matchButton = Array.from(buttons).find(b => b.textContent?.replace(/\s/g, '').includes('匹配对战'));
    if (matchButton) fireEvent.click(matchButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/matchmaking');
  });

  it('点击天梯排名卡片应该导航到排行榜页面', () => {
    (stores.useAuthStore as any).mockReturnValue({ isAuthenticated: false, user: null });
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    );
    
    const leaderboardCard = screen.getByText('天梯排名').closest('.ant-card');
    if (leaderboardCard) {
      fireEvent.click(leaderboardCard);
    }
    
    expect(mockNavigate).toHaveBeenCalledWith('/leaderboard');
  });
});
