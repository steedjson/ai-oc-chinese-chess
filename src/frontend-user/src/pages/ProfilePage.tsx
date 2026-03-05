import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Avatar, Typography, Statistic, Progress, Table, Tag, Button, Space, Tabs } from 'antd';
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

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user: authUser } = useAuthStore();
  const [user] = useState<User | null>(authUser);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<{ win_rate: number } | null>(null);

  const loadUserData = useCallback(async () => {
    if (!authUser) return;
    
    try {
      setLoading(true);
      
      // 获取用户统计
      const statsResult = await userService.getUserStats();
      if (statsResult.success && statsResult.data) {
        setStats(statsResult.data);
      }

      // 获取排名历史（预留）
      // const historyResult = await rankingService.getRankHistory(30);
      // if (historyResult.success && historyResult.data) {
      //   setRankHistory(historyResult.data);
      // }
    } catch {
      console.error('Failed to load user data');
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
      render: (result: string) => {
        const color = result === '胜' ? 'green' : result === '负' ? 'red' : 'gray';
        return <Tag color={color}>{result}</Tag>;
      },
    },
    {
      title: '天梯分变化',
      dataIndex: 'ratingChange',
      key: 'ratingChange',
      render: (change: number) => (
        <Text type={change > 0 ? 'success' : 'danger'}>
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

  const mockGameHistory = [
    { key: '1', opponent: '张三', result: '胜', ratingChange: 15, date: '2026-03-03' },
    { key: '2', opponent: '李四', result: '负', ratingChange: -12, date: '2026-03-02' },
    { key: '3', opponent: '王五', result: '胜', ratingChange: 18, date: '2026-03-01' },
    { key: '4', opponent: '赵六', result: '和', ratingChange: 2, date: '2026-02-28' },
    { key: '5', opponent: '钱七', result: '胜', ratingChange: 16, date: '2026-02-27' },
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
              <Table
                columns={gameHistoryColumns}
                dataSource={mockGameHistory}
                pagination={{ pageSize: 5 }}
                loading={loading}
              />
            ),
          },
        ]}
      />
    </div>
  );
};

export default ProfilePage;
