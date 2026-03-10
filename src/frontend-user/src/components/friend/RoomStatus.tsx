import React, { useState, useEffect } from 'react';
import { Card, Typography, Space, Tag, Button, Progress, Tooltip, message } from 'antd';
import {
  UserOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ShareAltOutlined,
  CopyOutlined,
  QrcodeOutlined,
} from '@ant-design/icons';
import type { FriendRoom, FriendRoomStatus } from '@/types';
import { copyToClipboard, generateShareText } from '@/utils/share';

const { Title, Text } = Typography;

export interface RoomStatusProps {
  room: FriendRoom;
  onShare?: () => void;
  onJoin?: () => void;
  onStartGame?: () => void;
}

/**
 * 房间状态显示组件
 * 
 * 显示房间状态、房主、加入者、倒计时等信息
 */
export const RoomStatus: React.FC<RoomStatusProps> = ({
  room,
  onShare,
  onJoin,
  onStartGame,
}) => {
  const [timeLeft, setTimeLeft] = useState<number>(0);

  // 计算剩余时间
  useEffect(() => {
    const calculateTimeLeft = () => {
      const expiresAt = new Date(room.expires_at).getTime();
      const now = Date.now();
      const diff = expiresAt - now;
      return Math.max(0, diff);
    };

    setTimeLeft(calculateTimeLeft());

    const timer = setInterval(() => {
      const remaining = calculateTimeLeft();
      setTimeLeft(remaining);

      if (remaining === 0) {
        clearInterval(timer);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [room.expires_at]);

  // 格式化剩余时间
  const formatTimeLeft = (ms: number) => {
    const hours = Math.floor(ms / (1000 * 60 * 60));
    const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((ms % (1000 * 60)) / 1000);

    if (hours > 0) {
      return `${hours}小时${minutes}分钟`;
    } else if (minutes > 0) {
      return `${minutes}分钟${seconds}秒`;
    } else {
      return `${seconds}秒`;
    }
  };

  // 获取状态标签
  const getStatusTag = (status: FriendRoomStatus) => {
    const tagConfig = {
      waiting: { color: 'blue', icon: <ClockCircleOutlined />, text: '等待中' },
      playing: { color: 'green', icon: <PlayCircleOutlined />, text: '对局中' },
      finished: { color: 'success', icon: <CheckCircleOutlined />, text: '已结束' },
      expired: { color: 'default', icon: <CloseCircleOutlined />, text: '已过期' },
    };

    const config = tagConfig[status];
    return (
      <Tag icon={config.icon} color={config.color}>
        {config.text}
      </Tag>
    );
  };

  // 处理复制链接
  const handleCopyLink = async () => {
    const success = await copyToClipboard(room.invite_link);
    if (success) {
      message.success('链接已复制');
    } else {
      message.error('复制失败');
    }
  };

  // 处理分享
  const handleShare = () => {
    const shareText = generateShareText(room.room_code, room.invite_link);
    copyToClipboard(shareText);
    message.success('分享信息已复制');
    onShare?.();
  };

  // 计算过期进度
  const getExpireProgress = () => {
    const createdAt = new Date(room.created_at).getTime();
    const expiresAt = new Date(room.expires_at).getTime();
    const now = Date.now();
    const total = expiresAt - createdAt;
    const elapsed = now - createdAt;
    return Math.min(100, Math.max(0, (elapsed / total) * 100));
  };

  return (
    <Card className="card-chinese">
      <div className="text-center py-4">
        {/* 房间号 */}
        <div className="mb-6">
          <Text className="text-gray-500 text-sm">房间号</Text>
          <div className="text-3xl font-bold font-mono text-blue-600 my-2">
            {room.room_code}
          </div>
          {getStatusTag(room.status)}
        </div>

        {/* 房主信息 */}
        <div className="mb-6">
          <Space direction="vertical" size="small" className="w-full">
            <div className="flex items-center justify-center">
              <UserOutlined className="text-gray-400 mr-2" />
              <Text strong>房主：{room.creator_username}</Text>
            </div>
          </Space>
        </div>

        {/* 倒计时 */}
        {room.status === 'waiting' && (
          <div className="mb-6">
            <div className="flex items-center justify-center mb-2">
              <ClockCircleOutlined className="text-gray-400 mr-2" />
              <Text className="text-gray-600">房间过期倒计时</Text>
            </div>
            <Progress
              type="circle"
              percent={100 - getExpireProgress()}
              format={() => (
                <div className="text-center">
                  <Text className="text-lg font-mono">{formatTimeLeft(timeLeft)}</Text>
                </div>
              )}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
          </div>
        )}

        {/* 游戏信息 */}
        {room.game_id && (
          <div className="mb-6">
            <Text className="text-gray-500 text-sm">游戏 ID</Text>
            <div className="text-lg font-mono text-gray-700">#{room.game_id}</div>
          </div>
        )}

        {/* 操作按钮 */}
        <Space direction="vertical" size="small" className="w-full">
          {room.status === 'waiting' && (
            <>
              <Button
                type="primary"
                size="large"
                block
                icon={<ShareAltOutlined />}
                onClick={handleShare}
              >
                分享房间
              </Button>
              <Button
                size="large"
                block
                icon={<CopyOutlined />}
                onClick={handleCopyLink}
              >
                复制链接
              </Button>
              {onStartGame && (
                <Button
                  size="large"
                  block
                  icon={<PlayCircleOutlined />}
                  onClick={onStartGame}
                >
                  开始游戏
                </Button>
              )}
              {onJoin && (
                <Button
                  type="primary"
                  size="large"
                  block
                  icon={<PlayCircleOutlined />}
                  onClick={onJoin}
                >
                  加入房间
                </Button>
              )}
            </>
          )}

          {room.status === 'playing' && (
            <Button
              type="primary"
              size="large"
              block
              icon={<PlayCircleOutlined />}
              onClick={onStartGame}
            >
              进入对局
            </Button>
          )}

          {(room.status === 'finished' || room.status === 'expired') && (
            <Tag color="default">此房间已结束</Tag>
          )}
        </Space>

        {/* 二维码（可选） */}
        <Tooltip title="生成二维码" placement="top">
          <Button
            type="text"
            icon={<QrcodeOutlined />}
            className="mt-4"
            onClick={() => message.info('二维码功能开发中')}
          />
        </Tooltip>
      </div>
    </Card>
  );
};

export default RoomStatus;
