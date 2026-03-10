import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Avatar, Typography, Statistic, Progress, Table, Tag, Button, Space, Tabs, Alert } from 'antd';
import {
  UserOutlined,
  TrophyOutlined,
  FireOutlined,
  ClockCircleOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores';
import { userService } from '@/services';
import type { User } from '@/types';

const { Title, Text } = Typography;

interface GameHistoryItem {
  key: string;
  opponent: string;
  result: 'win' | 'loss' | 'draw';
  ratingChange: number;
  date: string;
}

interface GameHistoryData {
  results: Array<{
    id: string;
    opponent: {
      username: string;
      rating: number;
    };
    result: 'win' | 'loss' | 'draw';
    rating_change: number;
    created_at: string;
  }>;
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
  };
}

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user: authUser } = useAuthStore();
  const [user, setUser] = useState<User | null>(authUser);
  const [stats, setStats] = useState<{
    total_games: number;
    wins: number;
    losses: number;
    draws: number;
    win_rate: number;
    current_rating: number;
  } | null>(null);
  const [gameHistory, setGameHistory] = useState<GameHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadUserData = useCallback(async () => {
    if (!authUser) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // 获取最新用户资料
      const profileResult = await userService.getProfile();
      if (profileResult.success && profileResult.data) {
        const userData = profileResult.data as unknown as User;
        setUser(userData);
      }

      // 获取用户统计
      const statsResult = await userService.getUserStats();
      if (statsResult.success && statsResult.data) {
        setStats(statsResult.data);
      }

      // 获取对局历史
      setHistoryLoading(true);
      const gamesResult = await userService.getUserGames(authUser.id);
      if (gamesResult.success && gamesResult.data) {
        const historyData = gamesResult.data as unknown as GameHistoryData;
        const formattedHistory: GameHistoryItem[] = historyData.results.map((game) => ({
          key: game.id,
          opponent: game.opponent.username,
          result: game.result,
          ratingChange: game.rating_change,
          date: new Date(game.created_at).toLocaleDateString('zh-CN'),
        }));
        setGameHistory(formattedHistory);
      }
      setHistoryLoading(false);
    } catch (err) {
      console.error('Failed to load user data:', err);
      setError('加载用户数据失败，请稍后重试');
      setHistoryLoading(false);
    } finally {
      setLoading(false);
    }
  }, [authUser]);

  useEffect(() => {
    loadUserData();
  }, [loadUserData]);

  const winRate = stats?.win_rate || 0;

  const gameHistoryColumns = [
    {
      title: '对手',
      dataIndex: 'opponent',
      key: 'opponent',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      render: (result: 'win' | 'loss' | 'draw') => {
        const colorMap = { win: 'green', loss: 'red', draw: 'gray' };
        const textMap = { win: '胜', loss: '负', draw: '和' };
        return <Tag color={colorMap[result]}>{textMap[result]}</Tag>;
      },
    },
    {
      title: '天梯分变化',
      dataIndex: 'ratingChange',
      key: 'ratingChange',
      render: (change: number) => (
        <Text type={change > 0 ? 'success' : change < 0 ? 'danger' : undefined}>
          {change > 0 ? '+' : ''}{change}
        </Text>
      ),
    },
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
    },
  ];

  if (!user) {
    return (
      <Card className="card-chinese text-center py-12">
        <UserOutlined className="text-6xl text-gray-400 mb-4" />
        <Title level={4}>请先登录</Title>
        <Button type="primary" onClick={() => navigate('/login')}>
          去登录
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* 返回按钮 */}
      <Button onClick={() => navigate('/')}>
        <ArrowLeftOutlined /> 返回首页
      </Button>

      {/* 个人信息卡片 */}
      <Card className="card-chinese">
        <Row gutter={[24, 24]} align="middle">
          <Col xs={24} md={8} className="text-center">
            <Avatar
              src={user.avatar_url}
              icon={<UserOutlined />}
              size={120}
              className="bg-gradient-to-br from-red-500 to-yellow-500"
            />
            <div className="mt-4">
              <Title level={4} className="font-chinese mb-1">
                {user.nickname || user.username}
              </Title>
              <Text type="secondary">{user.username}</Text>
            </div>
          </Col>

          <Col xs={24} md={16}>
            <Row gutter={[16, 16]}>
              <Col xs={12} md={6}>
                <Statistic
                  title="天梯分"
                  value={user.rating}
                  valueStyle={{ color: '#dc2626' }}
                  prefix={<TrophyOutlined />}
                />
              </Col>
              <Col xs={12} md={6}>
                <Statistic
                  title="总对局"
                  value={user.total_games}
                  valueStyle={{ color: '#1677ff' }}
                  prefix={<ClockCircleOutlined />}
                />
              </Col>
              <Col xs={12} md={6}>
                <Statistic
                  title="胜场"
                  value={user.wins}
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<FireOutlined />}
                />
              </Col>
              <Col xs={12} md={6}>
                <Statistic
                  title="胜率"
                  value={winRate}
                  suffix="%"
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
            </Row>

            <div className="mt-6">
              <div className="flex justify-between mb-2">
                <Text strong>胜率</Text>
                <Text>{winRate}%</Text>
              </div>
              <Progress
                percent={winRate}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                showInfo={false}
              />
            </div>

            <div className="mt-4">
              <Space>
                <Tag color="blue">
                  {user.rating >= 2000 ? '大师' : user.rating >= 1600 ? '高级' : user.rating >= 1200 ? '中级' : '初级'}
                </Tag>
                <Tag color="green">活跃玩家</Tag>
              </Space>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 详细统计 */}
      <Tabs
        items={[
          {
            key: 'stats',
            label: '详细统计',
            children: (
              <Row gutter={[24, 24]}>
                <Col xs={24} md={8}>
                  <Card className="card-chinese text-center">
                    <FireOutlined className="text-4xl text-green-600 mb-2" />
                    <Statistic title="胜场" value={user.wins} />
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card className="card-chinese text-center">
                    <ClockCircleOutlined className="text-4xl text-red-600 mb-2" />
                    <Statistic title="负场" value={user.losses} />
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card className="card-chinese text-center">
                    <UserOutlined className="text-4xl text-gray-600 mb-2" />
                    <Statistic title="和棋" value={user.draws} />
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: 'history',
            label: '对局历史',
            children: (
              <>
                {error && (
                  <Alert
                    message={error}
                    type="error"
                    showIcon
                    className="mb-4"
                    action={
                      <Button size="small" type="primary" onClick={loadUserData}>
                        重试
                      </Button>
                    }
                  />
                )}
                <Table
                  columns={gameHistoryColumns}
                  dataSource={gameHistory}
                  pagination={{ pageSize: 5 }}
                  loading={historyLoading}
                  locale={{ emptyText: '暂无对局记录' }}
                />
              </>
            ),
          },
        ]}
      />
    </div>
  );
};

export default ProfilePage;
