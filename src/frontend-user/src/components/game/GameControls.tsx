import React from 'react';
import { Button, Space, Modal, Typography } from 'antd';
import {
  UndoOutlined,
  StopOutlined,
  CheckOutlined,
  HomeOutlined,
  SoundOutlined,
  MutedOutlined,
} from '@ant-design/icons';
import { useGameStore, useSettingsStore } from '@/stores';

const { Text } = Typography;

interface GameControlsProps {
  onUndo?: () => void;
  onResign?: () => void;
  onDraw?: () => void;
  onHome?: () => void;
  canUndo?: boolean;
  disabled?: boolean;
}

const GameControls: React.FC<GameControlsProps> = ({
  onUndo,
  onResign,
  onDraw,
  onHome,
  canUndo = false,
  disabled = false,
}) => {
  const { gameOver, winner } = useGameStore();
  const { sound_enabled, setSoundEnabled } = useSettingsStore();
  const [showResignConfirm, setShowResignConfirm] = React.useState(false);
  const [showDrawConfirm, setShowDrawConfirm] = React.useState(false);

  const handleResign = () => {
    setShowResignConfirm(false);
    onResign?.();
  };

  const handleDraw = () => {
    setShowDrawConfirm(false);
    onDraw?.();
  };

  return (
    <>
      <div className="card-chinese p-4 rounded-lg bg-white dark:bg-gray-800 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <Text strong className="text-lg font-chinese">游戏控制</Text>
          <Button
            type="text"
            icon={sound_enabled ? <SoundOutlined /> : <MutedOutlined />}
            onClick={() => setSoundEnabled(!sound_enabled)}
            size="small"
          />
        </div>

        <Space wrap className="w-full" direction="vertical">
          {/* 主要操作 */}
          <Space wrap className="w-full justify-center">
            <Button
              icon={<UndoOutlined />}
              onClick={onUndo}
              disabled={!canUndo || disabled || gameOver}
              block
            >
              悔棋
            </Button>
            <Button
              icon={<CheckOutlined />}
              onClick={() => setShowDrawConfirm(true)}
              disabled={disabled || gameOver}
              block
            >
              和棋
            </Button>
            <Button
              icon={<StopOutlined />}
              danger
              onClick={() => setShowResignConfirm(true)}
              disabled={disabled || gameOver}
              block
            >
              认输
            </Button>
          </Space>

          {/* 返回首页 */}
          <Button
            icon={<HomeOutlined />}
            onClick={onHome}
            className="w-full"
          >
            返回首页
          </Button>
        </Space>

        {/* 游戏状态提示 */}
        {gameOver && (
          <div className="mt-4 p-3 bg-gradient-to-r from-red-500 to-yellow-500 rounded-lg text-center">
            <Text strong className="text-white text-lg">
              {winner === 'red' ? '红方获胜！' : winner === 'black' ? '黑方获胜！' : '和棋！'}
            </Text>
          </div>
        )}
      </div>

      {/* 认输确认 */}
      <Modal
        title="确认认输"
        open={showResignConfirm}
        onOk={handleResign}
        onCancel={() => setShowResignConfirm(false)}
        okText="确认认输"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <p>确定要认输吗？认输后本局游戏将结束。</p>
      </Modal>

      {/* 和棋确认 */}
      <Modal
        title="提议和棋"
        open={showDrawConfirm}
        onOk={handleDraw}
        onCancel={() => setShowDrawConfirm(false)}
        okText="发送请求"
        cancelText="取消"
      >
        <p>确定要向对方提议和棋吗？对方可以选择接受或拒绝。</p>
      </Modal>
    </>
  );
};

export default GameControls;
