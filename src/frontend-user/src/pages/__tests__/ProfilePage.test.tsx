/**
 * ProfilePage 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProfilePage from '../ProfilePage';
import * as stores from '@/stores';
import { userService } from '@/services';

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
  };
});

// Mock services
vi.mock('@/services', () => ({
  userService: {
    getUserStats: vi.fn(),
  },
}));

describe('ProfilePage', () => {
  const mockUser = {
    id: '1',
    username: 'testuser',
    nickname: '测试昵称',
    rating: 1500,
    total_games: 100,
    wins: 60,
    losses: 30,
    draws: 10,
    avatar_url: '',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (stores.useAuthStore as any).mockReturnValue({ user: mockUser });
    (userService.getUserStats as any).mockResolvedValue({
      success: true,
      data: { win_rate: 60.0 },
    });
  });

  it('应该渲染用户资料页面', async () => {
    render(
      <BrowserRouter>
        <ProfilePage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('测试昵称')).toBeInTheDocument();
    expect(screen.getByText('testuser')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(userService.getUserStats).toHaveBeenCalled();
      expect(screen.getByText('60%')).toBeInTheDocument();
    });
  });

  it('未登录时应该显示登录提示', () => {
    (stores.useAuthStore as any).mockReturnValue({ user: null });
    
    render(
      <BrowserRouter>
        <ProfilePage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('请先登录')).toBeInTheDocument();
    const loginBtn = screen.getByText('去登录').closest('button');
    if (loginBtn) fireEvent.click(loginBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('应该正确计算胜率进度条', async () => {
    render(
      <BrowserRouter>
        <ProfilePage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      const progress = document.querySelector('.ant-progress');
      expect(progress).toBeInTheDocument();
    });
  });

  it('应该显示详细统计标签页', async () => {
    render(
      <BrowserRouter>
        <ProfilePage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('详细统计')).toBeInTheDocument();
    expect(screen.getByText('和棋')).toBeInTheDocument();
  });

  it('点击返回首页按钮应该导航到首页', () => {
    render(
      <BrowserRouter>
        <ProfilePage />
      </BrowserRouter>
    );
    
    const backButton = screen.getByText(/返回首页/).closest('button');
    if (backButton) fireEvent.click(backButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });
});
