import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi, beforeAll } from 'vitest';
import axios from 'axios';

// Mock axios
vi.mock('axios', async (importOriginal) => {
  const actual: any = await importOriginal();
  const mockAxiosInstance = {
    create: vi.fn(() => mockAxiosInstance),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    request: vi.fn(),
    defaults: { headers: { common: {} } },
  };
  return {
    default: {
      ...actual.default,
      create: vi.fn(() => mockAxiosInstance),
      ...mockAxiosInstance,
    },
    isAxiosError: actual.isAxiosError,
    AxiosError: actual.AxiosError,
  };
});

// Export mockApiClient for tests to use
export const mockApiClient = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  patch: vi.fn(),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  }
};

// 每个测试后清理 DOM
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Mock localStorage and sessionStorage
const storageMock = (() => {
  let store: Record<string, string> = {
    'access_token': 'mock-token-123',
    'refresh_token': 'mock-refresh-token-456'
  };
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    length: Object.keys(store).length,
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  };
})();

Object.defineProperty(window, 'localStorage', { value: storageMock });
Object.defineProperty(window, 'sessionStorage', { value: storageMock });

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock window.scrollTo
window.scrollTo = vi.fn();

// Mock navigator.onLine
Object.defineProperty(window.navigator, 'onLine', {
  writable: true,
  value: true,
});

// 启用 Mock 模式用于测试
Object.defineProperty(import.meta, 'env', {
  value: {
    DEV: true,
    PROD: false,
    VITE_USE_MOCK: 'true',
    VITE_MOCK_DELAY: '10',
    VITE_API_BASE_URL: '/api/v1',
    VITE_WS_BASE_URL: 'ws://localhost:8000/ws',
    VITEST: 'true',
  },
});

// Mock console.error 在测试中不显示警告
const originalConsoleError = console.error;
console.error = (...args: any[]) => {
  if (args[0]?.includes?.('Warning') || args[0]?.includes?.('not wrapped in act')) {
    return;
  }
  // 忽略网络错误（Mock 会处理）
  if (args[0]?.message?.includes?.('Network Error') || (typeof args[0] === 'string' && args[0].includes('Network Error'))) {
    return;
  }
  originalConsoleError(...args);
};

// 全局错误处理
beforeAll(() => {
  // Mock ResizeObserver
  class ResizeObserverMock {
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
  }
  Object.defineProperty(window, 'ResizeObserver', { value: ResizeObserverMock });

  // Mock getComputedStyle
  window.getComputedStyle = (elt) => {
    const style = {
      getPropertyValue: vi.fn((prop) => {
        if (prop === 'display') return 'block';
        return '';
      }),
      display: 'block',
      appearance: 'none',
      transitionProperty: 'none',
      transitionDuration: '0s',
      transitionDelay: '0s',
      transitionTimingFunction: 'ease',
      paddingLeft: '0',
      paddingRight: '0',
      paddingTop: '0',
      paddingBottom: '0',
      marginLeft: '0',
      marginRight: '0',
      marginTop: '0',
      marginBottom: '0',
      width: '0',
      height: '0',
      opacity: '1',
      visibility: 'visible',
      position: 'static',
      zIndex: 'auto',
      color: 'black',
      backgroundColor: 'white',
      fontSize: '14px',
      fontWeight: 'normal',
      textAlign: 'left',
      lineHeight: 'normal',
      boxSizing: 'border-box',
    } as unknown as CSSStyleDeclaration;
    
    // Add some common AntD requirements
    (style as any).removeProperty = vi.fn();
    (style as any).setProperty = vi.fn();
    
    return style;
  };

  // Mock IntersectionObserver
  class IntersectionObserverMock {
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
  }
  Object.defineProperty(window, 'IntersectionObserver', { value: IntersectionObserverMock });

  // 防止未处理的 Promise rejection 导致测试失败
  window.addEventListener('unhandledrejection', (event) => {
    event.preventDefault();
  });
});
