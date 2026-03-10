import { http } from './api';
import type { ApiResponse, FriendRoom, CreateRoomRequest, JoinRoomResponse } from '@/types';

const FRIEND_BASE = '/games/friend';

/**
 * 好友对战服务
 * 
 * 提供好友对战房间的创建、加入、查询等功能
 */
export const friendService = {
  /**
   * 创建好友对战房间
   * 
   * @param data 房间配置
   * @returns 创建的房间信息
   */
  async createRoom(data?: CreateRoomRequest): Promise<ApiResponse<FriendRoom>> {
    return await http.post<FriendRoom>(`${FRIEND_BASE}/create/`, data || {});
  },

  /**
   * 加入好友房间
   * 
   * @param roomCode 房间号
   * @returns 加入结果和游戏信息
   */
  async joinRoom(roomCode: string): Promise<ApiResponse<JoinRoomResponse>> {
    return await http.post<JoinRoomResponse>(`${FRIEND_BASE}/join/`, {
      room_code: roomCode.toUpperCase(),
    });
  },

  /**
   * 获取房间详情
   * 
   * @param roomCode 房间号
   * @returns 房间详情
   */
  async getRoom(roomCode: string): Promise<ApiResponse<FriendRoom>> {
    return await http.get<FriendRoom>(`${FRIEND_BASE}/rooms/${roomCode.toUpperCase()}/`);
  },

  /**
   * 获取我创建的房间列表
   * 
   * @returns 房间列表
   */
  async getMyRooms(): Promise<ApiResponse<FriendRoom[]>> {
    return await http.get<FriendRoom[]>(`${FRIEND_BASE}/my-rooms/`);
  },

  /**
   * 获取活跃房间列表
   * 
   * @returns 活跃房间列表
   */
  async getActiveRooms(): Promise<ApiResponse<FriendRoom[]>> {
    return await http.get<FriendRoom[]>(`${FRIEND_BASE}/active-rooms/`);
  },
};

export default friendService;
