/**
 * Mock API 拦截器
 * 使用自定义拦截器模拟 API 请求
 * 支持模拟延迟、错误场景
 */

import type { AxiosRequestConfig, AxiosResponse } from 'axios';
import {
  mockAuth,
  mockGame,
  mockRanking,
  mockUser,
  createMockResponse,
} from './mock.service';

// 是否启用 Mock 模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || 
                 import.meta.env.VITEST === 'true' ||
                 typeof window !== 'undefined' && (window as any).__TEST__;

// Mock 处理器类型
type MockHandler = (config: AxiosRequestConfig) => Promise<AxiosResponse | null>;

/**
 * Mock 请求拦截器
 */
class MockInterceptor {
  private handlers: Map<RegExp, MockHandler> = new Map();

  constructor() {
    this.registerHandlers();
  }

  /**
   * 注册所有 Mock 处理器
   */
  private registerHandlers() {
    // 认证相关
    this.handlers.set(/^POST.*\/auth\/login/, this.handleLogin.bind(this));
    this.handlers.set(/^POST.*\/auth\/register/, this.handleRegister.bind(this));
    this.handlers.set(/^POST.*\/auth\/refresh/, this.handleRefreshToken.bind(this));
    this.handlers.set(/^GET.*\/auth\/me/, this.handleGetUserInfo.bind(this));

    // 游戏相关
    this.handlers.set(/^POST.*\/games\/ai/, this.handleCreateAIGame.bind(this));
    this.handlers.set(/^POST.*\/games\/match/, this.handleCreateMatchGame.bind(this));
    this.handlers.set(/^POST.*\/games\/.*\/move/, this.handleMakeMove.bind(this));
    this.handlers.set(/^GET.*\/games\/[^/]+$/, this.handleGetGameStatus.bind(this));
    this.handlers.set(/^GET.*\/games\/records/, this.handleGetGameRecords.bind(this));

    // 排行榜相关
    this.handlers.set(/^GET.*\/ranking\/leaderboard/, this.handleGetLeaderboard.bind(this));
    this.handlers.set(/^GET.*\/ranking\/user/, this.handleGetUserRank.bind(this));

    // 用户相关
    this.handlers.set(/^GET.*\/users\/\d+$/, this.handleGetProfile.bind(this));
    this.handlers.set(/^GET.*\/users\/\d+\/stats/, this.handleGetStats.bind(this));
    this.handlers.set(/^PUT.*\/users\/\d+/, this.handleUpdateProfile.bind(this));
  }

  /**
   * 拦截请求
   */
  async intercept(config: AxiosRequestConfig): Promise<AxiosResponse | null> {
    if (!USE_MOCK) {
      return null;
    }

    const url = config.url || '';
    const method = (config.method || 'GET').toUpperCase();
    const fullPath = `${method} ${url}`;

    // 模式匹配
    for (const [pattern, handler] of this.handlers.entries()) {
      if (pattern.test(fullPath)) {
        return handler(config);
      }
    }

    return null;
  }

  /**
   * 创建 Mock 响应
   */
  private createResponse(data: any, status = 200): Promise<AxiosResponse> {
    return Promise.resolve({
      data,
      status,
      statusText: 'OK',
      headers: {},
      config: {} as AxiosRequestConfig,
    });
  }

  /**
   * 创建错误响应
   */
  private createErrorResponse(message: string, status = 400): Promise<AxiosResponse> {
    return Promise.resolve({
      data: {
        success: false,
        error: {
          code: 'MOCK_ERROR',
          message,
        },
      },
      status,
      statusText: 'Error',
      headers: {},
      config: {} as AxiosRequestConfig,
    });
  }

  // ==================== 认证相关处理器 ====================

  private async handleLogin(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const { username, password } = config.data || {};
    const result = await mockAuth.login(username, password);
    return this.createResponse(result);
  }

  private async handleRegister(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const { username, email, password } = config.data || {};
    const result = await mockAuth.register(username, email);
    return this.createResponse(result);
  }

  private async handleRefreshToken(): Promise<AxiosResponse> {
    const result = await mockAuth.refreshToken();
    return this.createResponse(result);
  }

  private async handleGetUserInfo(): Promise<AxiosResponse> {
    const result = await mockAuth.getUserInfo();
    return this.createResponse(result);
  }

  // ==================== 游戏相关处理器 ====================

  private async handleCreateAIGame(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const { difficulty, player_color } = config.data || {};
    const result = await mockGame.createAIGame(difficulty || 5, player_color || 'red');
    return this.createResponse(result);
  }

  private async handleCreateMatchGame(): Promise<AxiosResponse> {
    const result = await mockGame.createMatchGame();
    return this.createResponse(result);
  }

  private async handleMakeMove(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const { from, to } = config.data || {};
    const gameId = config.url?.match(/\/games\/([^/]+)\/move/)?.[1] || 'unknown';
    const result = await mockGame.makeMove(gameId, { from, to });
    return this.createResponse(result);
  }

  private async handleGetGameStatus(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const gameId = config.url?.match(/\/games\/([^/]+)/)?.[1] || 'unknown';
    const result = await mockGame.getGameStatus(gameId);
    return this.createResponse(result);
  }

  private async handleGetGameRecords(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const { page, page_size } = config.params || {};
    const result = await mockGame.getGameRecords(1, page, page_size);
    return this.createResponse(result);
  }

  // ==================== 排行榜相关处理器 ====================

  private async handleGetLeaderboard(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const { page, page_size } = config.params || {};
    const result = await mockRanking.getLeaderboard(page, page_size);
    return this.createResponse(result);
  }

  private async handleGetUserRank(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const userId = parseInt(config.url?.match(/\/users\/(\d+)/)?.[1] || '1', 10);
    const result = await mockRanking.getUserRank(userId);
    return this.createResponse(result);
  }

  // ==================== 用户相关处理器 ====================

  private async handleGetProfile(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const userId = parseInt(config.url?.match(/\/users\/(\d+)/)?.[1] || '1', 10);
    const result = await mockUser.getProfile(userId);
    return this.createResponse(result);
  }

  private async handleGetStats(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const userId = parseInt(config.url?.match(/\/users\/(\d+)/)?.[1] || '1', 10);
    const result = await mockUser.getStats(userId);
    return this.createResponse(result);
  }

  private async handleUpdateProfile(config: AxiosRequestConfig): Promise<AxiosResponse> {
    const userId = parseInt(config.url?.match(/\/users\/(\d+)/)?.[1] || '1', 10);
    const result = await mockUser.updateProfile(userId, config.data);
    return this.createResponse(result);
  }
}

// 创建全局拦截器实例
export const mockInterceptor = new MockInterceptor();

/**
 * 请求拦截器函数（用于 axios）
 */
export async function mockRequestInterceptor(config: AxiosRequestConfig): Promise<AxiosRequestConfig | any> {
  if (!USE_MOCK) {
    return config;
  }

  const mockResponse = await mockInterceptor.intercept(config);
  if (mockResponse) {
    // 返回 Mock 响应，跳过实际请求
    throw mockResponse;
  }

  return config;
}

/**
 * 响应拦截器函数（用于 axios）
 * 处理 Mock 响应（从请求拦截器抛出）
 */
export function mockResponseInterceptor(error: any): any {
  if (!USE_MOCK) {
    return Promise.reject(error);
  }

  // 如果是 Mock 响应，直接返回
  if (error && typeof error.data !== 'undefined' && error.status !== undefined) {
    return error;
  }

  return Promise.reject(error);
}

/**
 * 检查是否启用 Mock 模式
 */
export function isMockEnabled(): boolean {
  return USE_MOCK;
}

/**
 * 动态切换 Mock 模式
 */
export function setMockEnabled(enabled: boolean): void {
  console.log(`Mock mode ${enabled ? 'enabled' : 'disabled'}`);
}

export default {
  mockInterceptor,
  mockRequestInterceptor,
  mockResponseInterceptor,
  isMockEnabled,
  setMockEnabled,
};
