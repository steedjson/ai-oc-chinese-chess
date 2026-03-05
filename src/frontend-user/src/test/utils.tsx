/**
 * 测试工具函数
 */

import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import type { ReactElement, ReactNode } from 'react';

/**
 * 创建测试用的 QueryClient
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * 测试包装器 Props
 */
interface WrapperProps {
  children: ReactNode;
}

/**
 * 创建测试包装器
 */
export function createWrapper({
  queryClient,
  initialEntries,
}: {
  queryClient?: QueryClient;
  initialEntries?: string[];
} = {}) {
  const testQueryClient = queryClient || createTestQueryClient();

  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={testQueryClient}>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          {children}
        </BrowserRouter>
      </QueryClientProvider>
    );
  }

  return Wrapper;
}

/**
 * 自定义渲染函数
 */
export function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & {
    queryClient?: QueryClient;
    initialEntries?: string[];
  }
) {
  const wrapper = createWrapper(options);
  return render(ui, { wrapper, ...options });
}

/**
 * 重新导出 testing-library 的工具
 */
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
