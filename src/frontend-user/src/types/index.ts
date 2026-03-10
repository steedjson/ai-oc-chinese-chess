// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  nickname?: string;
  avatar_url?: string;
  rating: number;
  total_games: number;
  wins: number;
  losses: number;
  draws: number;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface UserProfile {
  user: User;
  bio?: string;
  location?: string;
  favorite_opening?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  nickname?: string;
}

// 游戏对局相关类型
export interface Game {
  id: string;
  red_player: PlayerInfo;
  black_player: PlayerInfo;
  game_type: 'single' | 'online' | 'friend' | 'ai';
  status: 'waiting' | 'playing' | 'finished' | 'aborted';
  winner?: 'red' | 'black' | 'draw';
  fen_start: string;
  fen_current: string;
  move_history: Move[];
  duration?: number;
  ai_level?: number;
  is_rated: boolean;
  created_at: string;
  finished_at?: string;
}

export interface PlayerInfo {
  id: number;
  username: string;
  avatar_url?: string;
  rating: number;
}

export interface Move {
  from: string;
  to: string;
  piece: string;
  captured?: string;
  fen: string;
  timestamp: number;
  player_id?: number;
}

export interface MakeMoveRequest {
  from: string;
  to: string;
  promotion?: string;
}

export interface GameResult {
  winner: 'red' | 'black' | 'draw';
  reason: 'checkmate' | 'resign' | 'draw' | 'timeout';
  rating_change: {
    red: number;
    black: number;
  };
}

// AI 对局相关类型
export interface AIGameRequest {
  difficulty: number; // 1-10
  player_color: 'red' | 'black';
}

export interface AIHint {
  move: string;
  score: number;
  depth: number;
}

export interface PositionAnalysis {
  score: number;
  best_move: string;
  top_moves: AIHint[];
}

// 匹配相关类型
export interface MatchmakingRequest {
  game_type: 'online' | 'friend';
  rating_range?: number;
}

export interface MatchmakingStatus {
  is_matching: boolean;
  queue_position?: number;
  estimated_wait_time?: number;
  search_range: number;
  started_at: string;
}

export interface MatchFound {
  game_id: string;
  opponent: PlayerInfo;
  room_id: string;
  your_color: 'red' | 'black';
}

// 排行榜相关类型
export interface LeaderboardEntry {
  rank: number;
  user: User;
  rating: number;
  total_games: number;
  win_rate: number;
  rank_change?: number; // 排名变化
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  total_count: number;
  page: number;
  page_size: number;
  user_rank?: LeaderboardEntry;
}

export interface RankDistribution {
  segment: string;
  min_rating: number;
  max_rating: number;
  count: number;
  percentage: number;
}

// 棋盘相关类型
export type PieceType = 'king' | 'advisor' | 'elephant' | 'horse' | 'rook' | 'cannon' | 'pawn';
export type PieceColor = 'red' | 'black';

export interface Piece {
  type: PieceType;
  color: PieceColor;
  position: string; // e.g., "e2"
}

export interface BoardState {
  fen: string;
  turn: PieceColor;
  pieces: Piece[];
  last_move?: Move;
  in_check: boolean;
  game_over: boolean;
}

export interface MoveHint {
  position: string;
  type: 'move' | 'capture';
}

export interface BoardPosition {
  file: string; // a-i
  rank: number; // 0-9
}

// WebSocket 消息类型
export interface WSMessage {
  type: WSMessageType;
  data: unknown;
}

export type WSMessageType = 
  | 'connect'
  | 'game_state'
  | 'move'
  | 'move_invalid'
  | 'chat'
  | 'player_join'
  | 'player_leave'
  | 'game_start'
  | 'game_end'
  | 'offer_draw'
  | 'accept_draw'
  | 'resign'
  | 'timeout'
  | 'error'
  | 'reconnect'
  | 'heartbeat';

// 通用 API 响应类型
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginationParams {
  page: number;
  page_size: number;
  ordering?: string;
}

export interface PaginatedResponse<T> {
  results: T[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// 设置相关类型
export interface AppSettings {
  theme: 'light' | 'dark';
  sound_enabled: boolean;
  animation_enabled: boolean;
  show_move_hints: boolean;
  board_orientation: 'red' | 'black';
  language: 'zh' | 'en';
}

// 聊天相关类型（导出自 chat.ts）
export type {
  ChatMessage,
  ChatMessageResponse,
  SendMessageRequest,
  ChatHistoryResponse,
  UseChatReturn,
  ChatPanelProps,
  EmojiPickerProps,
  WSChatMessage,
  WSChatResponse,
} from './chat';

export { ALLOWED_EMOJIS } from './chat';

// 好友对战相关类型
export type {
  FriendRoom,
  FriendRoomStatus,
  CreateRoomRequest,
  JoinRoomRequest,
  JoinRoomResponse,
  RoomListResponse,
} from './friend';
