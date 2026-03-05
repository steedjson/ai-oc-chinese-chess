/**
 * ErrorBoundary 组件测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

// 抛错组件
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('测试错误');
  }
  return <div>正常渲染</div>;
};

describe('ErrorBoundary', () => {
  it('正常情况下应该渲染子组件', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );
    
    expect(screen.getByText('正常渲染')).toBeInTheDocument();
  });

  it('捕获错误后应该渲染 ErrorFallback', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    
    expect(screen.getByText(/哎呀，出错了/)).toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });

  it('点击重置按钮应该恢复状态', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    
    // 确保错误已发生
    expect(screen.getByText(/哎呀，出错了/)).toBeInTheDocument();

    // 修改 props 使组件不再抛错
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    // 点击重置
    const resetBtn = screen.getByText('返回上一页');
    act(() => {
        fireEvent.click(resetBtn);
    });
    
    expect(screen.getByText('正常渲染')).toBeInTheDocument();
  });
});
