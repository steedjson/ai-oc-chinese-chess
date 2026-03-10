import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  copyToClipboard,
  generateShareText,
  generateShareImage,
  shareToSocial,
  nativeShare,
} from '../share';

describe('share utils', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('copyToClipboard', () => {
    it('使用现代 API 复制文本（HTTPS 环境）', async () => {
      const mockWriteText = vi.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: mockWriteText },
        writable: true,
      });

      Object.defineProperty(window, 'isSecureContext', {
        value: true,
        writable: true,
      });

      const result = await copyToClipboard('test text');
      
      expect(result).toBe(true);
      expect(mockWriteText).toHaveBeenCalledWith('test text');
    });

    it('使用降级方案复制文本（HTTP 环境）', async () => {
      Object.defineProperty(navigator, 'clipboard', {
        value: undefined,
        writable: true,
      });

      Object.defineProperty(window, 'isSecureContext', {
        value: false,
        writable: true,
      });

      const mockExecCommand = vi.fn().mockReturnValue(true);
      document.execCommand = mockExecCommand;

      const result = await copyToClipboard('test text');
      
      expect(result).toBe(true);
      expect(mockExecCommand).toHaveBeenCalledWith('copy');
    });

    it('复制失败时返回 false', async () => {
      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: vi.fn().mockRejectedValue(new Error('Failed')),
        },
        writable: true,
      });

      Object.defineProperty(window, 'isSecureContext', {
        value: true,
        writable: true,
      });

      const result = await copyToClipboard('test text');
      
      expect(result).toBe(false);
    });
  });

  describe('generateShareText', () => {
    it('生成正确的分享文本', () => {
      const text = generateShareText('CHESS12345', 'https://example.com/join/CHESS12345');
      
      expect(text).toContain('🎮 中国象棋 - 好友对战');
      expect(text).toContain('房间号：CHESS12345');
      expect(text).toContain('https://example.com/join/CHESS12345');
      expect(text).toContain('快来和我下一盘棋吧！♟️');
    });
  });

  describe('generateShareImage', () => {
    it('生成分享图片', async () => {
      // Mock canvas
      const mockCanvas = {
        width: 0,
        height: 0,
        getContext: vi.fn().mockReturnValue({
          createLinearGradient: vi.fn().mockReturnValue({
            addColorStop: vi.fn(),
          }),
          fillStyle: '',
          fillRect: vi.fn(),
          font: '',
          textAlign: '',
          fillText: vi.fn(),
        }),
        toDataURL: vi.fn().mockReturnValue('data:image/png;base64,test'),
      };

      const createElementSpy = vi.spyOn(document, 'createElement');
      createElementSpy.mockReturnValue(mockCanvas as any);

      const result = await generateShareImage('CHESS12345');
      
      expect(result).toBe('data:image/png;base64,test');
      expect(mockCanvas.toDataURL).toHaveBeenCalledWith('image/png');
    });

    it('获取 context 失败时返回 null', async () => {
      const mockCanvas = {
        width: 0,
        height: 0,
        getContext: vi.fn().mockReturnValue(null),
      };

      const createElementSpy = vi.spyOn(document, 'createElement');
      createElementSpy.mockReturnValue(mockCanvas as any);

      const result = await generateShareImage('CHESS12345');
      
      expect(result).toBe(null);
    });
  });

  describe('shareToSocial', () => {
    const mockOpen = vi.fn();
    let originalOpen: any;

    beforeEach(() => {
      originalOpen = window.open;
      window.open = mockOpen;
    });

    afterEach(() => {
      window.open = originalOpen;
    });

    it('分享到微博', () => {
      shareToSocial('test text', 'https://example.com', 'weibo');
      
      expect(mockOpen).toHaveBeenCalledWith(
        expect.stringContaining('service.weibo.com'),
        '_blank',
        'width=600,height=400'
      );
    });

    it('分享到 QQ', () => {
      shareToSocial('test text', 'https://example.com', 'qq');
      
      expect(mockOpen).toHaveBeenCalledWith(
        expect.stringContaining('connect.qq.com'),
        '_blank',
        'width=600,height=400'
      );
    });

    it('分享到 Twitter', () => {
      shareToSocial('test text', 'https://example.com', 'twitter');
      
      expect(mockOpen).toHaveBeenCalledWith(
        expect.stringContaining('twitter.com'),
        '_blank',
        'width=600,height=400'
      );
    });

    it('微信分享显示提示', () => {
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
      
      shareToSocial('test text', 'https://example.com', 'wechat');
      
      expect(alertSpy).toHaveBeenCalledWith('请长按复制链接，然后打开微信分享');
    });
  });

  describe('nativeShare', () => {
    it('使用系统分享 API（如果支持）', async () => {
      const mockShare = vi.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, 'share', {
        value: mockShare,
        writable: true,
      });

      const result = await nativeShare('title', 'text', 'https://example.com');
      
      expect(result).toBe(true);
      expect(mockShare).toHaveBeenCalledWith({
        title: 'title',
        text: 'text',
        url: 'https://example.com',
      });
    });

    it('不支持系统分享时返回 false', async () => {
      Object.defineProperty(navigator, 'share', {
        value: undefined,
        writable: true,
      });

      const result = await nativeShare('title', 'text', 'https://example.com');
      
      expect(result).toBe(false);
    });

    it('系统分享失败时返回 false', async () => {
      const mockShare = vi.fn().mockRejectedValue(new Error('Failed'));
      Object.defineProperty(navigator, 'share', {
        value: mockShare,
        writable: true,
      });

      const result = await nativeShare('title', 'text', 'https://example.com');
      
      expect(result).toBe(false);
    });
  });
});
