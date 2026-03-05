/**
 * ErrorFallback 组件测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorFallback from './ErrorFallback';

describe('ErrorFallback', () => {
  const mockError = new Error('Test Error');
  const mockRetry = vi.fn();
  const mockReset = vi.fn();

  it('应该渲染错误信息', () => {
    render(
      <ErrorFallback 
        error={mockError} 
        errorInfo={null} 
        onRetry={mockRetry} 
        onReset={mockReset} 
      />
    );
    
    expect(screen.getByText(/哎呀，出错了/)).toBeInTheDocument();
  });

  it('应该触发重试和重置回调', () => {
    render(
      <ErrorFallback 
        error={mockError} 
        errorInfo={null} 
        onRetry={mockRetry} 
        onReset={mockReset} 
      />
    );
    
    fireEvent.click(screen.getByText('重试'));
    expect(mockRetry).toHaveBeenCalled();
    
    fireEvent.click(screen.getByText('返回上一页'));
    expect(mockReset).toHaveBeenCalled();
  });
});
