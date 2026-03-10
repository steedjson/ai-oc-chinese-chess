import { describe, it, expect, vi, beforeEach } from 'vitest';
import { friendService } from '../friend.service';
import { http } from '../api';

// Mock http client
vi.mock('../api', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('friendService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createRoom', () => {
    it('创建房间（默认参数）', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          room_code: 'CHESS12345',
          status: 'waiting',
          creator: 1,
          creator_username: 'testuser',
          game_id: 100,
          expires_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          invite_link: 'https://example.com/join/CHESS12345',
        },
      };

      vi.mocked(http.post).mockResolvedValue(mockResponse);

      const result = await friendService.createRoom();
      
      expect(http.post).toHaveBeenCalledWith('/games/friend/create/', {});
      expect(result).toEqual(mockResponse);
    });

    it('创建房间（自定义参数）', async () => {
      const mockResponse = { success: true, data: {} };
      vi.mocked(http.post).mockResolvedValue(mockResponse);

      await friendService.createRoom({
        time_control: 1200,
        is_rated: true,
      });
      
      expect(http.post).toHaveBeenCalledWith('/games/friend/create/', {
        time_control: 1200,
        is_rated: true,
      });
    });
  });

  describe('joinRoom', () => {
    it('加入房间', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: '加入成功',
          room: {
            id: 1,
            room_code: 'CHESS12345',
            status: 'playing',
            creator: 1,
            creator_username: 'testuser',
            game_id: 100,
            expires_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            invite_link: 'https://example.com/join/CHESS12345',
          },
          game_id: 100,
          your_color: 'black',
        },
      };

      vi.mocked(http.post).mockResolvedValue(mockResponse);

      const result = await friendService.joinRoom('CHESS12345');
      
      expect(http.post).toHaveBeenCalledWith('/games/friend/join/', {
        room_code: 'CHESS12345',
      });
      expect(result).toEqual(mockResponse);
    });

    it('房间号自动转换为大写', async () => {
      vi.mocked(http.post).mockResolvedValue({ success: true, data: {} });

      await friendService.joinRoom('chess12345');
      
      expect(http.post).toHaveBeenCalledWith('/games/friend/join/', {
        room_code: 'CHESS12345',
      });
    });
  });

  describe('getRoom', () => {
    it('获取房间详情', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 1,
          room_code: 'CHESS12345',
          status: 'waiting',
          creator: 1,
          creator_username: 'testuser',
          game_id: 100,
          expires_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          invite_link: 'https://example.com/join/CHESS12345',
        },
      };

      vi.mocked(http.get).mockResolvedValue(mockResponse);

      const result = await friendService.getRoom('CHESS12345');
      
      expect(http.get).toHaveBeenCalledWith('/games/friend/rooms/CHESS12345/');
      expect(result).toEqual(mockResponse);
    });

    it('房间号自动转换为大写', async () => {
      vi.mocked(http.get).mockResolvedValue({ success: true, data: {} });

      await friendService.getRoom('chess12345');
      
      expect(http.get).toHaveBeenCalledWith('/games/friend/rooms/CHESS12345/');
    });
  });

  describe('getMyRooms', () => {
    it('获取我创建的房间列表', async () => {
      const mockResponse = {
        success: true,
        data: [
          {
            id: 1,
            room_code: 'CHESS12345',
            status: 'waiting',
            creator: 1,
            creator_username: 'testuser',
            game_id: 100,
            expires_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            invite_link: 'https://example.com/join/CHESS12345',
          },
        ],
      };

      vi.mocked(http.get).mockResolvedValue(mockResponse);

      const result = await friendService.getMyRooms();
      
      expect(http.get).toHaveBeenCalledWith('/games/friend/my-rooms/');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getActiveRooms', () => {
    it('获取活跃房间列表', async () => {
      const mockResponse = {
        success: true,
        data: [
          {
            id: 1,
            room_code: 'CHESS12345',
            status: 'waiting',
            creator: 1,
            creator_username: 'testuser',
            game_id: 100,
            expires_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            invite_link: 'https://example.com/join/CHESS12345',
          },
        ],
      };

      vi.mocked(http.get).mockResolvedValue(mockResponse);

      const result = await friendService.getActiveRooms();
      
      expect(http.get).toHaveBeenCalledWith('/games/friend/active-rooms/');
      expect(result).toEqual(mockResponse);
    });
  });
});
