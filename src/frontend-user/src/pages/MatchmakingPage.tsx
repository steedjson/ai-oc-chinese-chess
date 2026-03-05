import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Button, Typography, Progress, message, Alert, Space } from 'antd';
import { TeamOutlined, ClockCircleOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useMatchmakingStore, useGameStore, useAuthStore } from '@/stores';
import { ChessBoard, GameControls } from '@/components/game';
import { matchmakingService } from '@/services';
import { getWebSocketService } from '@/services';

const { Title, Text } = Typography;

const MatchmakingPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const {
    isMatching,
    status,
    startMatching,
    stopMatching,
    updateStatus,
    reset: resetMatchmaking,
  } = useMatchmakingStore();
  
  const {
    currentGame,
    boardState,
    isMyTurn,
    gameOver,
    resetGame,
  } = useGameStore();

  const [isSearching, setIsSearching] = useState(false);
  const [waitTime, setWaitTime] = useState(0);

  const wsService = getWebSocketService();

  // 开始匹配
  const handleStartMatching = async () => {
    if (!isAuthenticated) {
      message.warning('请先登录');
      navigate('/login');
      return;
    }

    setIsSearching(true);
    startMatching();

    try {
      const result = await matchmakingService.joinQueue();
      if (result.success && result.data) {
        updateStatus(result.data);
        message.success('已进入匹配队列');
      } else {
        message.error(result.error?.message || '匹配失败');
        setIsSearching(false);
        stopMatching();
      }
    } catch {
      console.error('Failed to join queue');
      message.error('匹配失败');
      setIsSearching(false);
      stopMatching();
    }
  };

  // 取消匹配
  const handleCancelMatching = async () => {
    try {
      await matchmakingService.cancelMatch();
      stopMatching();
      setIsSearching(false);
      message.info('已取消匹配');
    } catch {
      message.error('取消匹配失败');
    }
  };

  // 轮询匹配状态
  useEffect(() => {
    if (!isMatching) return;

    const interval = setInterval(async () => {
      try {
        const result = await matchmakingService.getStatus();
        if (result.success && result.data) {
          updateStatus(result.data);
          
          // 模拟等待时间增加
          setWaitTime(prev => prev + 1);
        }
      } catch (error) {
        console.error('Failed to get status:', error);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isMatching, updateStatus]);

  // 渲染匹配中界面
  const renderMatchmaking = () => (
    <Card className="card-chinese max-w-md mx-auto">
      <div className="text-center py-8">
        <TeamOutlined className="text-6xl text-blue-600 mb-6" />
        <Title level={3} className="font-chinese mb-4">正在匹配对手</Title>
        
        <div className="mb-8">
          <Progress
            type="circle"
            percent={Math.min(waitTime * 2, 100)}
            format={() => (
              <div className="text-center">
                <ClockCircleOutlined className="text-2xl" />
                <div className="text-sm mt-1">{waitTime}s</div>
              </div>
            )}
          />
        </div>

        <Alert
          message="寻找实力相当的对手中..."
          description={
            <div className="text-sm">
              <div>当前搜索范围：±{status?.search_range || 100}分</div>
              <div>预计等待时间：{Math.max(30 - waitTime, 0)}s</div>
            </div>
          }
          type="info"
          showIcon
          className="mb-6"
        />

        <Button
          danger
          size="large"
          onClick={handleCancelMatching}
          disabled={!isSearching}
        >
          取消匹配
        </Button>
      </div>
    </Card>
  );

  // 渲染游戏界面（匹配成功后）
  const renderGame = () => (
    <Row gutter={[24, 24]} justify="center">
      <Col xs={24} lg={12}>
        <Card className="card-chinese">
          <div className="flex justify-center">
            <ChessBoard
              boardState={boardState || { fen: INITIAL_FEN, turn: 'red', pieces: [], in_check: false, game_over: false }}
              orientation="red"
              disabled={!isMyTurn || gameOver}
            />
          </div>
        </Card>
      </Col>

      <Col xs={24} lg={6}>
        <Space direction="vertical" className="w-full" size="large">
          <Card className="card-chinese">
            <div className="text-center">
              <Text strong className="text-lg">
                {isMyTurn ? '轮到你走棋' : '对手思考中...'}
              </Text>
            </div>
          </Card>

          <GameControls
            onHome={() => {
              wsService.disconnect();
              resetGame();
              resetMatchmaking();
              navigate('/');
            }}
          />
        </Space>
      </Col>
    </Row>
  );

  // 初始界面
  const renderInitial = () => (
    <Card className="card-chinese max-w-md mx-auto">
      <div className="text-center py-8">
        <TeamOutlined className="text-6xl text-blue-600 mb-6" />
        <Title level={3} className="font-chinese mb-4">在线匹配</Title>
        <Text className="text-gray-600 mb-8 block">
          智能 Elo 匹配系统，为你找到实力相当的对手
        </Text>

        <Button
          type="primary"
          size="large"
          onClick={handleStartMatching}
          loading={isSearching}
          className="bg-gradient-to-r from-blue-600 to-purple-600 w-full"
        >
          <TeamOutlined /> 开始匹配
        </Button>

        <div className="mt-6 text-left">
          <Text strong>匹配规则：</Text>
          <ul className="text-sm text-gray-600 mt-2 space-y-1">
            <li>• 初始搜索范围：±100 分</li>
            <li>• 每 30 秒扩大 50 分</li>
            <li>• 最大搜索范围：±300 分</li>
            <li>• 超时时间：3 分钟</li>
          </ul>
        </div>

        <div className="mt-6">
          <Button onClick={() => navigate('/')}>
            <ArrowLeftOutlined /> 返回首页
          </Button>
        </div>
      </div>
    </Card>
  );

  // 根据状态渲染不同界面
  if (!isAuthenticated) {
    return renderInitial();
  }

  if (isMatching) {
    return renderMatchmaking();
  }

  if (currentGame) {
    return renderGame();
  }

  return renderInitial();
};

const INITIAL_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR';

export default MatchmakingPage;
