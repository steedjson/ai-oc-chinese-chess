import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Slider, Button, Typography, Spin, message, Space } from 'antd';
import { RobotOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useGameStore, useAuthStore } from '@/stores';
import { ChessBoard, GameControls } from '@/components/game';
import { aiService, gameService } from '@/services';
import { getWebSocketService } from '@/services';
import type { BoardState, Move } from '@/types';

const { Title, Text } = Typography;

// 难度等级配置
const DIFFICULTY_LEVELS = [
  { level: 1, name: '入门', description: '适合初学者', elo: 400 },
  { level: 2, name: '新手', description: '刚入门的玩家', elo: 600 },
  { level: 3, name: '初级', description: '有一定基础', elo: 800 },
  { level: 4, name: '入门', description: '熟悉规则', elo: 1000 },
  { level: 5, name: '中级', description: '普通玩家水平', elo: 1200 },
  { level: 6, name: '中级', description: '有一定经验', elo: 1400 },
  { level: 7, name: '高级', description: '经验丰富的玩家', elo: 1600 },
  { level: 8, name: '高级', description: '高手水平', elo: 1800 },
  { level: 9, name: '大师', description: '接近大师水平', elo: 2000 },
  { level: 10, name: '大师', description: '顶级 AI 水平', elo: 2200 },
];

const AIGamePage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const {
    currentGame,
    boardState,
    isMyTurn,
    myColor,
    gameOver,
    setCurrentGame,
    setBoardState,
    setMyTurn,
    makeMove,
    setGameOver,
    resetGame,
    updateFen,
  } = useGameStore();

  const [difficulty, setDifficulty] = useState(5);
  const [isCreating, setIsCreating] = useState(false);
  const [gameStarted, setGameStarted] = useState(false);
  const [isAILoading, setIsAILoading] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
  const [validMoves, setValidMoves] = useState<string[]>([]);

  const wsService = getWebSocketService();

  // 初始化游戏
  const createGame = async () => {
    if (!isAuthenticated) {
      message.warning('请先登录');
      navigate('/login');
      return;
    }

    setIsCreating(true);
    try {
      const result = await aiService.createAIGame(difficulty, 'red');
      if (result.success && result.data) {
        setCurrentGame(result.data);
        setGameStarted(true);
        
        // 初始化棋盘状态
        const initialBoard: BoardState = {
          fen: result.data.fen_current,
          turn: 'red',
          pieces: [],
          in_check: false,
          game_over: false,
        };
        setBoardState(initialBoard);

        // 连接 WebSocket
        connectWebSocket(result.data.id);
        
        message.success('游戏创建成功！');
      } else {
        message.error(result.error?.message || '创建游戏失败');
      }
    } catch (error) {
      console.error('Failed to create game:', error);
      message.error('创建游戏失败');
    } finally {
      setIsCreating(false);
    }
  };

  // 连接 WebSocket
  const connectWebSocket = (gameId: string) => {
    wsService.connect(`game/${gameId}/`, {
      onMessage: (msg) => {
        console.log('[AIGame] WS Message:', msg);
        
        switch (msg.type) {
          case 'game_state':
            updateFen((msg.data as { fen: string }).fen);
            break;
            
          case 'move':
            handleOpponentMove(msg.data as Move);
            break;
            
          case 'game_end':
            handleGameEnd(msg.data as { winner: 'red' | 'black' | 'draw'; reason: string });
            break;
            
          case 'error':
            message.error((msg.data as { message: string }).message);
            break;
        }
      },
      onClose: () => {
        console.log('[AIGame] WebSocket disconnected');
      },
    });
  };

  // 请求 AI 走棋
  const requestAIMove = useCallback(async () => {
    if (!currentGame) return;

    try {
      const result = await aiService.getAIMove(currentGame.id);
      if (result.success && result.data) {
        // AI 走棋会通过 WebSocket 推送，这里不需要处理
      }
    } catch {
      console.error('Failed to get AI move');
    }
  }, [currentGame]);

  // 执行走棋
  const executeMove = useCallback(async (from: string, to: string) => {
    if (!currentGame) return;

    setIsAILoading(true);
    try {
      const result = await gameService.makeMove(currentGame.id, { from, to });
      if (result.success && result.data) {
        makeMove(result.data.move);
        updateFen(result.data.move.fen);
        setMyTurn(false);
        setSelectedPosition(null);
        setValidMoves([]);

        // 请求 AI 走棋
        setTimeout(requestAIMove, 500);
      } else {
        message.error(result.error?.message || '走棋失败');
      }
    } catch {
      console.error('Failed to make move');
      message.error('走棋失败');
    } finally {
      setIsAILoading(false);
    }
  }, [currentGame, makeMove, updateFen, setMyTurn, setSelectedPosition, setValidMoves, requestAIMove]);

  // 处理对手（AI）走棋
  const handleOpponentMove = useCallback((move: Move) => {
    makeMove(move);
    updateFen(move.fen);
    setMyTurn(true);
  }, [makeMove, updateFen, setMyTurn]);

  // 处理游戏结束
  const handleGameEnd = useCallback((result: { winner: 'red' | 'black' | 'draw'; reason: string }) => {
    setGameOver(result.winner, result.reason);
    message.info(
      result.winner === 'red' ? '恭喜你获胜！' :
      result.winner === 'black' ? 'AI 获胜' : '和棋！'
    );
  }, [setGameOver]);

  // 处理棋子点击
  const handlePieceClick = useCallback((position: string) => {
    if (!isMyTurn || gameOver) return;

    const piece = boardState?.pieces.find(p => p.position === position);
    
    // 如果点击的是己方棋子，选中它
    if (piece?.color === myColor) {
      setSelectedPosition(position);
      // TODO: 获取合法走法
      setValidMoves([]);
    } else if (selectedPosition) {
      // 如果已选中棋子，尝试移动
      if (validMoves.includes(position)) {
        executeMove(selectedPosition, position);
      }
    }
  }, [isMyTurn, gameOver, boardState, myColor, selectedPosition, validMoves, executeMove, setValidMoves]);

  // 悔棋
  const handleUndo = () => {
    message.info('AI 对战暂不支持悔棋');
  };

  // 认输
  const handleResign = async () => {
    if (!currentGame) return;
    try {
      await gameService.resign(currentGame.id);
      setGameOver('black', 'resign');
      message.info('你已认输');
    } catch {
      message.error('认输失败');
    }
  };

  // 和棋
  const handleDraw = () => {
    message.info('AI 对战暂不支持和棋');
  };

  // 返回首页
  const handleHome = () => {
    wsService.disconnect();
    resetGame();
    setGameStarted(false);
    navigate('/');
  };

  // 清理
  useEffect(() => {
    return () => {
      wsService.disconnect();
    };
  }, [wsService]);

  // 渲染难度选择
  const renderDifficultySelector = () => (
    <Card className="card-chinese max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <RobotOutlined className="text-6xl text-red-600 mb-4" />
        <Title level={2} className="font-chinese">AI 对战</Title>
        <Text className="text-gray-600">选择难度等级，与 AI 一决高下</Text>
      </div>

      <div className="mb-8">
        <div className="flex justify-between mb-2">
          <Text strong>难度等级：{difficulty}</Text>
          <Text type="secondary">{DIFFICULTY_LEVELS[difficulty - 1].name}</Text>
        </div>
        <Slider
          min={1}
          max={10}
          value={difficulty}
          onChange={setDifficulty}
          marks={{
            1: '入门',
            5: '中级',
            10: '大师',
          }}
          tooltip={{ formatter: (value) => DIFFICULTY_LEVELS[(value || 1) - 1].name }}
        />
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex justify-between items-center">
            <div>
              <Text strong>{DIFFICULTY_LEVELS[difficulty - 1].description}</Text>
              <div className="text-sm text-gray-500 mt-1">
                预估天梯分：{DIFFICULTY_LEVELS[difficulty - 1].elo}
              </div>
            </div>
            <Button
              type="primary"
              size="large"
              onClick={createGame}
              loading={isCreating}
              className="bg-gradient-to-r from-red-600 to-yellow-500"
            >
              开始游戏
            </Button>
          </div>
        </div>
      </div>

      <div className="text-center">
        <Button onClick={() => navigate('/')}>
          <ArrowLeftOutlined /> 返回首页
        </Button>
      </div>
    </Card>
  );

  // 渲染游戏界面
  const renderGame = () => (
    <Row gutter={[24, 24]} justify="center">
      {/* 棋盘 */}
      <Col xs={24} lg={12}>
        <Card className="card-chinese">
          <div className="flex justify-center">
            {isAILoading && (
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10">
                <Spin size="large" tip="AI 思考中..." />
              </div>
            )}
            <ChessBoard
              boardState={boardState || { fen: INITIAL_FEN, turn: 'red', pieces: [], in_check: false, game_over: false }}
              selectedPosition={selectedPosition}
              validMoves={validMoves}
              onPieceClick={handlePieceClick}
              onMove={executeMove}
              orientation="red"
              disabled={!isMyTurn || gameOver || isAILoading}
            />
          </div>
        </Card>
      </Col>

      {/* 控制面板 */}
      <Col xs={24} lg={6}>
        <Space direction="vertical" className="w-full" size="large">
          {/* 游戏信息 */}
          <Card className="card-chinese">
            <div className="text-center">
              <Text strong className="text-lg">
                {isMyTurn ? '轮到你走棋' : 'AI 思考中...'}
              </Text>
              <div className="mt-2">
                <Text type="secondary">
                  难度：{DIFFICULTY_LEVELS[difficulty - 1].name} (Lv.{difficulty})
                </Text>
              </div>
            </div>
          </Card>

          {/* 游戏控制 */}
          <GameControls
            onUndo={handleUndo}
            onResign={handleResign}
            onDraw={handleDraw}
            onHome={handleHome}
            disabled={!gameStarted || isAILoading}
          />
        </Space>
      </Col>
    </Row>
  );

  if (!gameStarted) {
    return renderDifficultySelector();
  }

  return renderGame();
};

// 初始 FEN
const INITIAL_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR';

export default AIGamePage;
