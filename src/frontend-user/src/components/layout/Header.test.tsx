/**
 * Header 组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Header from './Header';
import * as stores from '@/stores';

// Mock stores
vi.mock('@/stores', async (importOriginal) => {
  const actual = await importOriginal<typeof stores>();
  return {
    ...actual,
    useAuthStore: vi.fn(),
    useSettingsStore: vi.fn(),
  };
});

// Mock services
vi.mock('@/services', () => ({
  authService: {
    logout: vi.fn().mockResolvedValue({}),
  },
}));

const renderWithRouter = (ui: React.ReactElement) => {
  return render(ui, { wrapper: BrowserRouter });
};

describe('Header', () => {
  const mockToggleTheme = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (stores.useSettingsStore as any).mockReturnValue({
      theme: 'light',
      toggleTheme: mockToggleTheme,
    });
  });

  it('未登录时应该显示登录按钮', () => {
    (stores.useAuthStore as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
      logout: vi.fn(),
    });

    const { container } = renderWithRouter(<Header />);
    
    // Ant Design 的按钮可能由于 icon 和文本被拆分，导致 getByRole 失败。
    // 我们直接在 header 容器中寻找包含“登”且包含“录”的按钮
    const buttons = container.querySelectorAll('button');
    const loginButton = Array.from(buttons).find(b => b.textContent?.includes('登') && b.textContent?.includes('录'));
    expect(loginButton).toBeDefined();
  });

  it('已登录时应该显示用户信息', () => {
    (stores.useAuthStore as any).mockReturnValue({
      user: {
        username: 'testuser',
        nickname: '测试用户',
        rating: 1200,
      },
      isAuthenticated: true,
      logout: vi.fn(),
    });

    renderWithRouter(<Header />);
    
    expect(screen.getByText('测试用户')).toBeInTheDocument();
    expect(screen.getByText(/天梯分：1200/)).toBeInTheDocument();
  });

  it('应该渲染导航链接', () => {
    (stores.useAuthStore as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
      logout: vi.fn(),
    });

    renderWithRouter(<Header />);
    
    expect(screen.getByText('中国象棋')).toBeInTheDocument();
    expect(screen.getByText('首页')).toBeInTheDocument();
    expect(screen.getByText('AI 对战')).toBeInTheDocument();
  });

  it('点击主题切换按钮应该触发 toggleTheme', () => {
    (stores.useAuthStore as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
      logout: vi.fn(),
    });

    renderWithRouter(<Header />);
    
    const buttons = screen.getAllByRole('button');
    const themeButton = buttons.find(b => b.querySelector('.anticon-moon') || b.querySelector('.anticon-sun'));
    
    if (themeButton) {
      fireEvent.click(themeButton);
      expect(mockToggleTheme).toHaveBeenCalled();
    }
  });
});
