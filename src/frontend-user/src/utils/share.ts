/**
 * 分享工具函数
 * 
 * 提供复制链接、生成分享图片、社交媒体分享等功能
 */

/**
 * 复制文本到剪贴板
 * 
 * @param text 要复制的文本
 * @returns 是否成功
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      // 现代浏览器 API（HTTPS 环境）
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // 降级方案（HTTP 环境或旧浏览器）
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const success = document.execCommand('copy');
      document.body.removeChild(textArea);
      return success;
    }
  } catch (error) {
    console.error('复制失败:', error);
    return false;
  }
}

/**
 * 生成分享文本
 * 
 * @param roomCode 房间号
 * @param inviteLink 邀请链接
 * @returns 分享文本
 */
export function generateShareText(roomCode: string, inviteLink: string): string {
  return `🎮 中国象棋 - 好友对战\n\n` +
    `房间号：${roomCode}\n\n` +
    `点击链接加入对局：\n${inviteLink}\n\n` +
    `快来和我下一盘棋吧！♟️`;
}

/**
 * 生成分享图片（可选功能）
 * 
 * @param roomCode 房间号
 * @returns 图片数据 URL（如果支持）
 */
export async function generateShareImage(roomCode: string): Promise<string | null> {
  try {
    // 创建 canvas
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      return null;
    }

    // 设置画布大小
    canvas.width = 600;
    canvas.height = 400;

    // 背景渐变
    const gradient = ctx.createLinearGradient(0, 0, 600, 400);
    gradient.addColorStop(0, '#1a1a2e');
    gradient.addColorStop(1, '#16213e');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 600, 400);

    // 标题
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 36px Arial, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('🎮 中国象棋', 300, 80);

    // 副标题
    ctx.font = '24px Arial, sans-serif';
    ctx.fillStyle = '#e94560';
    ctx.fillText('好友对战', 300, 130);

    // 房间号
    ctx.font = 'bold 48px monospace';
    ctx.fillStyle = '#0f3460';
    ctx.fillRect(150, 160, 300, 80);
    ctx.fillStyle = '#ffffff';
    ctx.fillText(roomCode, 300, 215);

    // 提示文字
    ctx.font = '18px Arial, sans-serif';
    ctx.fillStyle = '#a0a0a0';
    ctx.fillText('扫描二维码或点击链接加入', 300, 280);

    // 底部装饰
    ctx.font = '14px Arial, sans-serif';
    ctx.fillStyle = '#666666';
    ctx.fillText('♟️ 以棋会友 · 乐在棋中', 300, 350);

    return canvas.toDataURL('image/png');
  } catch (error) {
    console.error('生成分享图片失败:', error);
    return null;
  }
}

/**
 * 分享到社交媒体
 * 
 * @param text 分享文本
 * @param url 分享链接
 * @param platform 平台类型
 */
export function shareToSocial(
  text: string,
  url: string,
  platform: 'wechat' | 'weibo' | 'qq' | 'twitter'
): void {
  const encodedText = encodeURIComponent(text);
  const encodedUrl = encodeURIComponent(url);

  let shareUrl = '';

  switch (platform) {
    case 'wechat':
      // 微信需要用户手动复制链接
      alert('请长按复制链接，然后打开微信分享');
      break;
    case 'weibo':
      shareUrl = `https://service.weibo.com/share/share.php?title=${encodedText}&url=${encodedUrl}`;
      break;
    case 'qq':
      shareUrl = `https://connect.qq.com/widget/shareqq/index.html?url=${encodedUrl}&title=${encodedText}`;
      break;
    case 'twitter':
      shareUrl = `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`;
      break;
  }

  if (shareUrl) {
    window.open(shareUrl, '_blank', 'width=600,height=400');
  }
}

/**
 * 使用系统分享 API（如果支持）
 * 
 * @param title 分享标题
 * @param text 分享文本
 * @param url 分享链接
 * @returns 是否成功
 */
export async function nativeShare(
  title: string,
  text: string,
  url: string
): Promise<boolean> {
  try {
    if (navigator.share) {
      await navigator.share({
        title,
        text,
        url,
      });
      return true;
    }
    return false;
  } catch (error) {
    console.error('系统分享失败:', error);
    return false;
  }
}

/**
 * 生成二维码 Canvas（可选功能）
 * 
 * @param text 要编码的文本
 * @returns Canvas 元素
 */
export async function generateQRCode(text: string): Promise<HTMLCanvasElement | null> {
  try {
    // 使用第三方库（如 qrcode）可以生成真正的二维码
    // 这里提供一个简单的占位实现
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 200;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      return null;
    }

    // 简单绘制一个占位二维码
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 200, 200);
    ctx.fillStyle = '#000000';
    
    // 绘制随机方块模拟二维码
    for (let i = 0; i < 100; i++) {
      const x = Math.floor(Math.random() * 20) * 10;
      const y = Math.floor(Math.random() * 20) * 10;
      ctx.fillRect(x, y, 8, 8);
    }

    return canvas;
  } catch (error) {
    console.error('生成二维码失败:', error);
    return null;
  }
}

export default {
  copyToClipboard,
  generateShareText,
  generateShareImage,
  shareToSocial,
  nativeShare,
  generateQRCode,
};
