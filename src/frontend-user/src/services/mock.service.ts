/**
 * Mock 数据服务
 * 提供测试用的 Mock 数据，符合真实 API 响应格式
 */

import type { User, Game, LeaderboardEntry, Move } from '@/types';

// Mock 延迟时间（毫秒）
const MOCK_DELAY = parseInt(import.meta.env.VITE_MOCK_DELAY || '300', 10);

/**
 * 模拟异步延迟
 */
function mockDelay(): Promise<void> {
  return new Promise((resolve) => {
    const delay = MOCK_DELAY + Math.random() * 300; // 200-500ms 随机延迟
    setTimeout(resolve, delay);
  });
}

/**
 * Mock 用户数据
 */
export const mockUsers: Record<number, User> = {
  1: {
    id: 1,
    username: 'test_user',
    email: 'test@example.com',
    nickname: '测试玩家',
    avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=test',
    rating: 2100,
    total_games: 550,
    wins: 320,
    losses: 150,
    draws: 80,
    is_active: true,
    created_at: '2024-01-15T08:00:00Z',
    last_login: '2024-03-03T10:00:00Z',
  },
  2: {
    id: 2,
    username: 'ai_opponent',
    email: 'ai@chinese-chess.com',
    nickname: 'AI 对手',
    avatar_url: 'https://api.dicebear.com/7.x/bottts/svg?seed=ai',
    rating: 2800,
    total_games: 1000,
    wins: 800,
    losses: 100,
    draws: 100,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
  },
};

/**
 * Mock 游戏数据
 */
export const mockGames: Game[] = [
  {
    id: 'game_001',
    red_player: {
      id: 1,
      username: 'test_user',
      avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=test',
      rating: 2100,
    },
    black_player: {
      id: 2,
      username: 'ai_opponent',
      avatar_url: 'https://api.dicebear.com/7.x/bottts/svg?seed=ai',
      rating: 2800,
    },
    game_type: 'ai',
    status: 'finished',
    winner: 'red',
    fen_start: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
    fen_current: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 45',
    move_history: [],
    duration: 1800,
    ai_level: 8,
    is_rated: true,
    created_at: '2024-03-02T14:30:00Z',
    finished_at: '2024-03-02T15:00:00Z',
  },
  {
    id: 'game_002',
    red_player: {
      id: 1,
      username: 'test_user',
      avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=test',
      rating: 2100,
    },
    black_player: {
      id: 3,
      username: 'player_master',
      avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=master',
      rating: 2600,
    },
    game_type: 'online',
    status: 'finished',
    winner: 'black',
    fen_start: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
    fen_current: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 62',
    move_history: [],
    duration: 2400,
    is_rated: true,
    created_at: '2024-03-01T10:15:00Z',
    finished_at: '2024-03-01T10:55:00Z',
  },
];

/**
 * Mock 排行榜数据
 */
export const mockLeaderboard: LeaderboardEntry[] = [
  {
    rank: 1,
    user: mockUsers[2],
    rating: 2800,
    total_games: 1000,
    win_rate: 0.8,
  },
  {
    rank: 2,
    user: {
      id: 3,
      username: 'player_master',
      email: 'master@example.com',
      nickname: '大师级别',
      avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=master',
      rating: 2600,
      total_games: 800,
      wins: 500,
      losses: 200,
      draws: 100,
      is_active: true,
      created_at: '2024-01-10T00:00:00Z',
    },
    rating: 2600,
    total_games: 800,
    win_rate: 0.625,
  },
  {
    rank: 3,
    user: mockUsers[1],
    rating: 2100,
    total_games: 550,
    win_rate: 0.582,
  },
];

/**
 * Mock 走棋数据
 */
export const mockMove: Move = {
  from: 'e2',
  to: 'e4',
  piece: 'C',
  captured: undefined,
  fen: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 2',
  timestamp: Date.now(),
  player_id: 1,
};

/**
 * Mock API 响应工具函数
 */
export function createMockResponse<T>(data: T, success = true): Promise<{ success: boolean; data?: T; error?: { code: string; message: string } }> {
  return mockDelay().then(() => ({
    success,
    data: success ? data : undefined,
    error: success ? undefined : { code: 'MOCK_ERROR', message: '模拟错误' },
  }));
}

/**
 * Mock 认证服务数据
 */
export const mockAuth = {
  login: async (username: string, _password: string) => {
    const user = Object.values(mockUsers).find((u) => u.username === username) || mockUsers[1];
    return createMockResponse({
      access_token: 'mock_access_token_' + Date.now(),
      refresh_token: 'mock_refresh_token_' + Date.now(),
      expires_in: 3600,
      user,
    });
  },
  
  register: async (username: string, email: string) => {
    const newUser: User = {
      id: Date.now(),
      username,
      email,
      nickname: username,
      avatar_url: `https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`,
      rating: 1200,
      total_games: 0,
      wins: 0,
      losses: 0,
      draws: 0,
      is_active: true,
      created_at: new Date().toISOString(),
    };
    return createMockResponse({
      access_token: 'mock_access_token_' + Date.now(),
      refresh_token: 'mock_refresh_token_' + Date.now(),
      expires_in: 3600,
      user: newUser,
    });
  },
  
  refreshToken: async () => {
    return createMockResponse({
      access_token: 'mock_access_token_' + Date.now(),
      refresh_token: 'mock_refresh_token_' + Date.now(),
      expires_in: 3600,
    });
  },
  
  getUserInfo: async () => {
    return createMockResponse(mockUsers[1]);
  },
};

/**
 * Mock 游戏服务数据
 */
export const mockGame = {
  createAIGame: async (difficulty: number, playerColor: 'red' | 'black') => {
    const game: Game = {
      id: 'game_ai_' + Date.now(),
      red_player: playerColor === 'red' ? mockUsers[1] : mockUsers[2],
      black_player: playerColor === 'black' ? mockUsers[1] : mockUsers[2],
      game_type: 'ai',
      status: 'playing',
      fen_start: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
      fen_current: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
      move_history: [],
      ai_level: difficulty,
      is_rated: true,
      created_at: new Date().toISOString(),
    };
    return createMockResponse(game);
  },
  
  createMatchGame: async () => {
    const game: Game = {
      id: 'game_match_' + Date.now(),
      red_player: mockUsers[1],
      black_player: mockUsers[3] || {
        id: 3,
        username: 'random_player',
        avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=random',
        rating: 2000,
      },
      game_type: 'online',
      status: 'playing',
      fen_start: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
      fen_current: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
      move_history: [],
      is_rated: true,
      created_at: new Date().toISOString(),
    };
    return createMockResponse(game);
  },
  
  makeMove: async (gameId: string, move: { from: string; to: string }) => {
    return createMockResponse({
      success: true,
      move: {
        ...mockMove,
        from: move.from,
        to: move.to,
      },
      fen: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 2',
      isGameOver: false,
      result: null,
    });
  },
  
  getGameStatus: async (gameId: string) => {
    const game = mockGames.find((g) => g.id === gameId) || mockGames[0];
    return createMockResponse(game);
  },
  
  getGameRecords: async (userId: number, page = 1, limit = 10) => {
    const start = (page - 1) * limit;
    const end = start + limit;
    return createMockResponse({
      results: mockGames.slice(start, end),
      pagination: {
        page,
        page_size: limit,
        total_count: mockGames.length,
        total_pages: Math.ceil(mockGames.length / limit),
        has_next: end < mockGames.length,
        has_prev: page > 1,
      },
    });
  },
};

/**
 * Mock 排行榜服务数据
 */
export const mockRanking = {
  getLeaderboard: async (page = 1, limit = 10) => {
    const start = (page - 1) * limit;
    const end = start + limit;
    return createMockResponse({
      entries: mockLeaderboard.slice(start, end),
      total_count: mockLeaderboard.length,
      page,
      page_size: limit,
    });
  },
  
  getUserRank: async (userId: number) => {
    const userEntry = mockLeaderboard.find((e) => e.user.id === userId);
    if (userEntry) {
      return createMockResponse(userEntry);
    }
    return createMockResponse(null, false);
  },
};

/**
 * Mock 用户服务数据
 */
export const mockUser = {
  getProfile: async (userId: number) => {
    const user = mockUsers[userId] || mockUsers[1];
    return createMockResponse(user);
  },
  
  getStats: async (userId: number) => {
    const user = mockUsers[userId] || mockUsers[1];
    return createMockResponse({
      user,
      stats: {
        total_games: user.total_games,
        wins: user.wins,
        losses: user.losses,
        draws: user.draws,
        win_rate: user.total_games > 0 ? user.wins / user.total_games : 0,
        rating: user.rating,
      },
    });
  },
  
  updateProfile: async (userId: number, data: Partial<User>) => {
    const user = mockUsers[userId] || mockUsers[1];
    const updatedUser = { ...user, ...data };
    return createMockResponse(updatedUser);
  },
};

/**
 * 获取 Mock 数据（按类型）
 */
export function getMockData(type: string) {
  switch (type) {
    case 'users':
      return mockUsers;
    case 'games':
      return mockGames;
    case 'leaderboard':
      return mockLeaderboard;
    default:
      return null;
  }
}

export default {
  mockUsers,
  mockGames,
  mockLeaderboard,
  mockAuth,
  mockGame,
  mockRanking,
  mockUser,
  createMockResponse,
  getMockData,
};
