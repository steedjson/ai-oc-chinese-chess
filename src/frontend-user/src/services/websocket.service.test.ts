/**
 * WebSocket Service 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WebSocketService } from './websocket.service';

// Mock getAccessToken
vi.mock('./api', () => ({
  getAccessToken: vi.fn(() => 'mock-token'),
}));

describe('WebSocketService', () => {
  let service: WebSocketService;
  let mockWebSocket: any;

  beforeEach(() => {
    vi.clearAllMocks();
    service = new WebSocketService();
    
    // Mock global WebSocket
    mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      readyState: 1, // OPEN
      onopen: null,
      onclose: null,
      onerror: null,
      onmessage: null,
    };
    
    global.WebSocket = vi.fn().mockImplementation(() => mockWebSocket) as any;
    // @ts-ignore
    global.WebSocket.OPEN = 1;
    // @ts-ignore
    global.WebSocket.CLOSED = 3;
    // @ts-ignore
    global.WebSocket.CONNECTING = 0;
    // @ts-ignore
    global.WebSocket.CLOSING = 2;
  });

  afterEach(() => {
    service.disconnect();
  });

  it('connect 应该创建 WebSocket 实例', () => {
    service.connect('game/123');
    expect(global.WebSocket).toHaveBeenCalled();
  });

  it('send 应该在连接时发送消息', () => {
    service.connect('test');
    service.send('move', { from: 'e2', to: 'e4' });
    expect(mockWebSocket.send).toHaveBeenCalled();
  });

  it('sendMove 应该发送正确的走棋消息', () => {
    service.connect('test');
    service.sendMove('e2', 'e4');
    expect(mockWebSocket.send).toHaveBeenCalledWith(expect.stringContaining('"type":"move"'));
  });

  it('disconnect 应该关闭连接', () => {
    service.connect('test');
    service.disconnect();
    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  it('isConnected 应该返回正确状态', () => {
    // 初始状态 service.ws 为 null，所以 isConnected() 返回 undefined === WebSocket.OPEN (false)
    expect(service.isConnected()).toBe(false);
    
    service.connect('test');
    expect(service.isConnected()).toBe(true);
    
    mockWebSocket.readyState = 3; // CLOSED
    expect(service.isConnected()).toBe(false);
  });

  it('应该能处理收到无效 JSON 消息的情况', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    service.connect('test');
    
    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage({ data: 'invalid-json' });
    }
    
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Failed to parse message'), expect.anything());
    consoleSpy.mockRestore();
  });

  it('应该能处理 WebSocket 连接错误', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const onError = vi.fn();
    service.connect('test', { onError });
    
    if (mockWebSocket.onerror) {
      mockWebSocket.onerror({ message: 'Error event' });
    }
    
    expect(onError).toHaveBeenCalled();
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it('重连逻辑测试', () => {
    vi.useFakeTimers();
    service.connect('test');
    
    // 触发关闭
    if (mockWebSocket.onclose) {
      mockWebSocket.onclose({ code: 1006, reason: 'Abnormal' });
    }
    
    // 应该在一段时间后重试
    vi.runAllTimers();
    expect(global.WebSocket).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });

  it('手动关闭不应重连', () => {
    vi.useFakeTimers();
    service.connect('test');
    service.disconnect();
    
    if (mockWebSocket.onclose) {
      mockWebSocket.onclose({ code: 1000, reason: 'Normal' });
    }
    
    vi.runAllTimers();
    expect(global.WebSocket).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });

  it('发送各种游戏命令', () => {
    service.connect('test');
    
    service.sendChat('hello');
    expect(mockWebSocket.send).toHaveBeenCalledWith(expect.stringContaining('\"type\":\"chat\"'));
    
    service.sendResign();
    expect(mockWebSocket.send).toHaveBeenCalledWith(expect.stringContaining('\"type\":\"resign\"'));
    
    service.sendOfferDraw();
    expect(mockWebSocket.send).toHaveBeenCalledWith(expect.stringContaining('\"type\":\"offer_draw\"'));
    
    service.sendAcceptDraw();
    expect(mockWebSocket.send).toHaveBeenCalledWith(expect.stringContaining('\"type\":\"accept_draw\"'));
    
    service.sendReconnect('game1');
    expect(mockWebSocket.send).toHaveBeenCalledWith(expect.stringContaining('\"type\":\"reconnect\"'));
  });
});
