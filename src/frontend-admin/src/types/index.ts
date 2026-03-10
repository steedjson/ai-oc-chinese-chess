// 用户类型
export interface User {
  id: string;
  username: string;
  email: string;
  nickname?: string;
  avatar?: string;
  elo: number;
  status: 'active' | 'inactive' | 'banned';
  createdAt: string;
  lastLoginAt?: string;
  totalGames: number;
  wins: number;
  losses: number;
  draws: number;
}

export interface UserListParams {
  page: number;
  pageSize: number;
  search?: string;
  status?: string;
}

export interface UserListResponse {
  data: User[];
  total: number;
  page: number;
  pageSize: number;
}

// 游戏类型
export interface Game {
  id: string;
  redPlayerName?: string;
  blackPlayerName?: string;
  whitePlayer: PlayerInfo;
  blackPlayer: PlayerInfo;
  winner?: 'white' | 'black' | 'draw' | 'red_win' | 'black_win';
  result?: string;
  status: 'playing' | 'completed' | 'abandoned' | 'waiting' | 'finished' | 'aborted';
  moveCount: number;
  duration: number;
  createdAt: string;
  startTime: string;
  endTime?: string;
  completedAt?: string;
  isAiGame: boolean;
  aiDifficulty?: number;
  fen?: string;
  moveHistory?: MoveHistoryItem[];
}

export interface MoveHistoryItem {
  move: string;
  time: string;
  fen: string;
}

export interface PlayerInfo {
  id: string;
  username: string;
  elo: number;
  isAi?: boolean;
}

export interface GameListParams {
  page: number;
  pageSize: number;
  status?: string;
  playerId?: string;
  isAiGame?: boolean;
  search?: string;
}

export interface GameListResponse {
  data: Game[];
  total: number;
  page: number;
  pageSize: number;
}

// 匹配类型
export interface MatchmakingRecord {
  id: string;
  playerId: string;
  opponentId?: string;
  eloChange: number;
  matchedAt: string;
  completedAt?: string;
  status: 'pending' | 'matched' | 'completed' | 'cancelled';
}

export interface EloRanking {
  rank: number;
  userId: string;
  username: string;
  elo: number;
  totalGames: number;
  wins: number;
  winRate: number;
}

// AI 类型
export interface AiGameRecord {
  id: string;
  playerId: string;
  aiDifficulty: number;
  winner: 'player' | 'ai' | 'draw';
  moveCount: number;
  duration: number;
  createdAt: string;
}

export interface AiConfig {
  id: string;
  difficulty: number;
  enabled: boolean;
  eloBase: number;
  createdAt: string;
  updatedAt: string;
}

// 统计类型
export interface DailyStats {
  date: string;
  dau: number;
  mau: number;
  newUsers: number;
  totalGames: number;
  avgGameDuration: number;
}

export interface UserGrowthStats {
  date: string;
  totalUsers: number;
  newUsers: number;
  activeUsers: number;
}

export interface GameTimeStats {
  date: string;
  totalHours: number;
  avgHoursPerUser: number;
  peakConcurrent: number;
}

// API 响应类型
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export type UserRole = 'super_admin' | 'ops';

export interface LoginResponse {
  token: string;
  user: {
    id: string;
    username: string;
    role: UserRole;
  };
}

// ========== 游戏管理扩展类型 ==========

// 游戏日志
export interface GameLog {
  id: string;
  game_id: string;
  operator: {
    id: string;
    username: string;
  };
  action: string;
  action_display: string;
  details: Record<string, any>;
  severity: 'info' | 'warning' | 'error' | 'critical';
  created_at: string;
  ip_address?: string;
}

export interface GameLogParams {
  page?: number;
  page_size?: number;
  action?: string;
  severity?: string;
}

// 异常数据
export interface AnomalyData {
  game_id: string;
  game: {
    id: string;
    red_player: string;
    black_player: string;
    status: string;
    started_at: string;
  };
  anomaly_type: 'timeout' | 'suspicious_moves' | 'idle';
  severity: 'high' | 'medium' | 'low';
  description: string;
  details: Record<string, any>;
  detected_at: string;
}

// 游戏统计
export interface GameStatistics {
  totalGames: number;
  playingGames: number;
  waitingGames: number;
  completedToday: number;
  avgGameDuration: number;
  totalAnomalies: number;
}
