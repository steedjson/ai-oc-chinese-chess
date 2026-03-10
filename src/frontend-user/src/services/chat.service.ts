import { http } from '@/services/api';
import type { ApiResponse } from '@/types';
import type { ChatMessageResponse, ChatHistoryResponse, SendMessageRequest } from '@/types/chat';

/**
 * 聊天服务
 * 提供聊天相关的 REST API 调用
 */

/**
 * 发送聊天消息
 */
export async function sendChatMessage(
  gameId: string,
  data: SendMessageRequest
): Promise<ApiResponse<ChatMessageResponse>> {
  return http.post<ChatMessageResponse>(
    `/chat/games/${gameId}/send/`,
    data
  );
}

/**
 * 获取聊天历史
 */
export async function getChatHistory(
  gameId: string,
  roomType: 'game' | 'spectator' = 'game',
  limit: number = 50,
  before?: string
): Promise<ApiResponse<ChatHistoryResponse>> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    room_type: roomType,
  });

  if (before) {
    params.append('before', before);
  }

  return http.get<ChatHistoryResponse>(
    `/chat/games/${gameId}/history/?${params.toString()}`
  );
}

/**
 * 删除聊天消息
 */
export async function deleteChatMessage(
  messageId: string
): Promise<ApiResponse<{ message: string }>> {
  return http.delete<{ message: string }>(
    `/chat/messages/${messageId}/delete/`
  );
}

/**
 * 获取聊天统计
 */
export async function getChatStats(
  gameId: string
): Promise<ApiResponse<{ total_messages: number; game_messages: number; spectator_messages: number }>> {
  return http.get<{ total_messages: number; game_messages: number; spectator_messages: number }>(
    `/chat/games/${gameId}/stats/`
  );
}
