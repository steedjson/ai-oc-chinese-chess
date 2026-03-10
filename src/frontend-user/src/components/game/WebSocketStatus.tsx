import React, { useEffect, useState } from 'react';
import { Badge, Tooltip, Progress, Modal, Button, Alert } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
  WifiOutlined,
} from '@ant-design/icons';
import { getWebSocketService, type ReconnectInfo } from '@/services/websocket.service';

interface WebSocketStatusProps {
  gameId?: string;
}

/**
 * WebSocket 状态显示组件
 * 
 * 功能：
 * - 显示 WebSocket 连接状态
 * - 显示重连进度
 * - 提供手动重连功能
 * - 显示详细连接信息
 */
export const WebSocketStatus: React.FC<WebSocketStatusProps> = ({ gameId }) => {
  const [reconnectInfo, setReconnectInfo] = useState<ReconnectInfo>({
    state: 'disconnected',
    attempt: 0,
    maxAttempts: 10,
  });
  const [showModal, setShowModal] = useState(false);
  const [countdown, setCountdown] = useState<number | undefined>(undefined);

  useEffect(() => {
    const wsService = getWebSocketService();
    
    // 监听重连状态变化
    const unsubscribe = wsService.onReconnectStateChange((info) => {
      setReconnectInfo(info);
      
      // 如果正在重连，启动倒计时
      if (info.state === 'reconnecting' && info.nextRetryIn) {
        setCountdown(info.nextRetryIn);
        const interval = setInterval(() => {
          setCountdown((prev) => {
            if (prev === undefined || prev <= 1000) {
              clearInterval(interval);
              return undefined;
            }
            return prev - 1000;
          });
        }, 1000);
        
        return () => clearInterval(interval);
      } else {
        setCountdown(undefined);
      }
    });

    return unsubscribe;
  }, []);

  /**
   * 获取状态图标
   */
  const getStatusIcon = () => {
    switch (reconnectInfo.state) {
      case 'connected':
        return <CheckCircleOutlined className="text-green-500 text-lg" />;
      case 'disconnected':
        return <CloseCircleOutlined className="text-gray-400 text-lg" />;
      case 'reconnecting':
        return <WifiOutlined className="text-yellow-500 text-lg animate-pulse" />;
      case 'failed':
        return <WarningOutlined className="text-red-500 text-lg" />;
      default:
        return null;
    }
  };

  /**
   * 获取状态文本
   */
  const getStatusText = () => {
    switch (reconnectInfo.state) {
      case 'connected':
        return '已连接';
      case 'disconnected':
        return '未连接';
      case 'reconnecting':
        return `重连中 (${reconnectInfo.attempt}/${reconnectInfo.maxAttempts})`;
      case 'failed':
        return '连接失败';
      default:
        return '未知';
    }
  };

  /**
   * 手动重连
   */
  const handleReconnect = () => {
    const wsService = getWebSocketService();
    wsService.reconnect();
  };

  /**
   * 渲染重连进度
   */
  const renderReconnectProgress = () => {
    if (reconnectInfo.state !== 'reconnecting') return null;

    const progress = (reconnectInfo.attempt / reconnectInfo.maxAttempts) * 100;
    const seconds = countdown !== undefined ? Math.ceil(countdown / 1000) : 0;

    return (
      <div className="mt-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span>重连进度</span>
          <span>{reconnectInfo.attempt}/{reconnectInfo.maxAttempts}</span>
        </div>
        <Progress
          percent={progress}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          showInfo={false}
        />
        {seconds > 0 && (
          <div className="text-center text-sm text-gray-500">
            {seconds} 秒后重试...
          </div>
        )}
      </div>
    );
  };

  /**
   * 渲染详情内容
   */
  const renderDetails = () => {
    return (
      <div className="space-y-4">
        {/* 游戏信息 */}
        {gameId && (
          <div className="text-sm">
            <div className="text-gray-500">游戏 ID</div>
            <div className="font-mono">{gameId}</div>
          </div>
        )}

        {/* 连接状态 */}
        <div className="flex items-center justify-between">
          <span className="font-medium">连接状态</span>
          <Badge
            status={
              reconnectInfo.state === 'connected'
                ? 'success'
                : reconnectInfo.state === 'failed'
                ? 'error'
                : reconnectInfo.state === 'reconnecting'
                ? 'warning'
                : 'default'
            }
            text={getStatusText()}
          />
        </div>

        {/* 重连信息 */}
        {reconnectInfo.state === 'reconnecting' && (
          <div>
            <div className="font-medium mb-2">重连信息</div>
            {renderReconnectProgress()}
          </div>
        )}

        {/* 失败提示 */}
        {reconnectInfo.state === 'failed' && (
          <Alert
            message="连接失败"
            description="已达到最大重连次数，请检查网络连接后手动重试。"
            type="error"
            showIcon
          />
        )}

        {/* 重连按钮 */}
        {(reconnectInfo.state === 'failed' || reconnectInfo.state === 'disconnected') && (
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={handleReconnect}
            block
          >
            手动重连
          </Button>
        )}
      </div>
    );
  };

  return (
    <>
      {/* 状态指示器 */}
      <Tooltip
        title={
          <div>
            <div>WebSocket: {getStatusText()}</div>
            {reconnectInfo.state === 'reconnecting' && (
              <div className="text-xs text-gray-400 mt-1">
                正在尝试重新连接...
              </div>
            )}
          </div>
        }
      >
        <div
          className="flex items-center gap-2 cursor-pointer hover:opacity-80"
          onClick={() => setShowModal(true)}
        >
          {getStatusIcon()}
          <span className="text-sm hidden md:inline">{getStatusText()}</span>
        </div>
      </Tooltip>

      {/* 详情弹窗 */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <WifiOutlined />
            WebSocket 连接状态
          </div>
        }
        open={showModal}
        onCancel={() => setShowModal(false)}
        footer={
          reconnectInfo.state === 'failed' || reconnectInfo.state === 'disconnected' ? (
            <Button type="primary" icon={<ReloadOutlined />} onClick={handleReconnect}>
              手动重连
            </Button>
          ) : (
            <Button onClick={() => setShowModal(false)}>关闭</Button>
          )
        }
      >
        {renderDetails()}
      </Modal>
    </>
  );
};

export default WebSocketStatus;
