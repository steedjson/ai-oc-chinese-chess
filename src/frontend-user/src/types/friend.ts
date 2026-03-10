/**
 * 好友对战相关类型定义
 */

/**
 * 好友房间状态
 */
export type FriendRoomStatus = 'waiting' | 'playing' | 'finished' | 'expired';

/**
 * 好友房间详情
 */
export interface FriendRoom {
  id: number;
  room_code: string;
  status: FriendRoomStatus;
  creator: number;
  creator_username: string;
  game_id: number;
  expires_at: string;
  started_at?: string;
  finished_at?: string;
  created_at: string;
  updated_at: string;
  invite_link: string;
}

/**
 * 创建房间请求
 */
export interface CreateRoomRequest {
  time_control?: number; // 秒，默认 600（10 分钟）
  is_rated?: boolean;    // 是否计分，默认 false
}

/**
 * 加入房间请求
 */
export interface JoinRoomRequest {
  room_code: string;
}

/**
 * 加入房间响应
 */
export interface JoinRoomResponse {
  message: string;
  room: FriendRoom;
  game_id: number;
  your_color: 'black';
}

/**
 * 房间列表响应
 */
export interface RoomListResponse {
  rooms: FriendRoom[];
}
