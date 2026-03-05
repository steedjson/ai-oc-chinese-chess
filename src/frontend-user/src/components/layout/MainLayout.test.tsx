/**
 * MainLayout 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import MainLayout from './MainLayout';
import * as stores from '@/stores';

// Mock stores
vi.mock('@/stores', async (importOriginal) => {
  const actual = await importOriginal<typeof stores>();
  return {
    ...actual,
    useSettingsStore: vi.fn(),
    useAuthStore: vi.fn(),
  };
});

describe('MainLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (stores.useSettingsStore as any).mockReturnValue({
      theme: 'light',
    });
    (stores.useAuthStore as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
    });
  });

  it('应该正确渲染布局和子组件', () => {
    render(
      <BrowserRouter>
        <MainLayout>
          <div data-testid="child-content">测试内容</div>
        </MainLayout>
      </BrowserRouter>
    );
    
    expect(screen.getByTestId('child-content')).toBeInTheDocument();
    // 检查 Header 和 Footer 是否存在
    expect(screen.getByText('中国象棋')).toBeInTheDocument();
    expect(screen.getByText(/关于中国象棋/)).toBeInTheDocument();
  });

  it('应该支持暗色主题', () => {
    (stores.useSettingsStore as any).mockReturnValue({
      theme: 'dark',
    });
    
    render(
      <BrowserRouter>
        <MainLayout>
          <div>暗色内容</div>
        </MainLayout>
      </BrowserRouter>
    );
    
    expect(screen.getByText('暗色内容')).toBeInTheDocument();
  });
});
