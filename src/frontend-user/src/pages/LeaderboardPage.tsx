import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Table, Typography, Avatar, Tag, Input, Space, Button, Row, Col, Statistic } from 'antd';
import {
  TrophyOutlined,
  CrownOutlined,
  StarOutlined,
  SearchOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { rankingService } from '@/services';
import type { LeaderboardEntry, User } from '@/types';

const { Title, Text } = Typography;

const LeaderboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadLeaderboard();
  }, []);

  const loadLeaderboard = async () => {
    try {
      setLoading(true);
      const result = await rankingService.getLeaderboard(1, 100);
      if (result.success && result.data) {
        setLeaderboard(result.data.entries);
      }
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      render: (rank: number) => {
        if (rank === 1) {
          return (
            <div className="flex items-center gap-1">
              <CrownOutlined className="text-yellow-500 text-xl" />
              <Text strong className="text-yellow-600">1</Text>
            </div>
          );
        }
        if (rank === 2) {
          return (
            <div className="flex items-center gap-1">
              <StarOutlined className="text-gray-400 text-xl" />
              <Text strong className="text-gray-600">2</Text>
            </div>
          );
        }
        if (rank === 3) {
          return (
            <div className="flex items-center gap-1">
              <StarOutlined className="text-amber-600 text-xl" />
              <Text strong className="text-amber-600">3</Text>
            </div>
          );
        }
        return <Text className="text-gray-600">{rank}</Text>;
      },
    },
    {
      title: '玩家',
      dataIndex: 'user',
      key: 'user',
      render: (user: User) => (
        <div className="flex items-center gap-3">
          <Avatar
            src={user.avatar_url}
            icon={<CrownOutlined />}
            className="bg-gradient-to-br from-red-500 to-yellow-500"
          />
          <div>
            <Text strong>{user.nickname || user.username}</Text>
            <div className="text-xs text-gray-500">{user.username}</div>
          </div>
        </div>
      ),
    },
    {
      title: '天梯分',
      dataIndex: 'rating',
      key: 'rating',
      width: 120,
      render: (rating: number) => (
        <Text strong className="text-red-600 text-lg">{rating}</Text>
      ),
    },
    {
      title: '总对局',
      dataIndex: 'total_games',
      key: 'total_games',
      width: 100,
      render: (games: number) => <Text>{games}</Text>,
    },
    {
      title: '胜率',
      dataIndex: 'win_rate',
      key: 'win_rate',
      width: 100,
      render: (rate: number) => (
        <Tag color={rate >= 60 ? 'green' : rate >= 50 ? 'blue' : 'orange'}>
          {rate.toFixed(1)}%
        </Tag>
      ),
    },
    {
      title: '段位',
      dataIndex: 'rating',
      key: 'segment',
      width: 100,
      render: (rating: number) => {
        let segment = '初级';
        let color = 'blue';
        if (rating >= 2000) {
          segment = '大师';
          color = 'purple';
        } else if (rating >= 1600) {
          segment = '高级';
          color = 'orange';
        } else if (rating >= 1200) {
          segment = '中级';
          color = 'green';
        }
        return <Tag color={color}>{segment}</Tag>;
      },
    },
  ];

  const filteredData = leaderboard.filter(entry =>
    entry.user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    entry.user.nickname?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <Button onClick={() => navigate('/')}>
          <ArrowLeftOutlined /> 返回首页
        </Button>
        <Title level={2} className="font-chinese text-gradient mb-0">
          <TrophyOutlined className="mr-2" />
          天梯排行榜
        </Title>
        <div />
      </div>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]}>
        <Col xs={12} md={6}>
          <Card className="card-chinese text-center">
            <CrownOutlined className="text-4xl text-yellow-500 mb-2" />
            <Statistic title="榜首玩家" value={leaderboard[0]?.user.nickname || '-'} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card className="card-chinese text-center">
            <TrophyOutlined className="text-4xl text-red-500 mb-2" />
            <Statistic title="最高天梯分" value={leaderboard[0]?.rating || 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card className="card-chinese text-center">
            <StarOutlined className="text-4xl text-blue-500 mb-2" />
            <Statistic title="活跃玩家" value={leaderboard.length} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card className="card-chinese text-center">
            <SearchOutlined className="text-4xl text-green-500 mb-2" />
            <Statistic title="搜索玩家" value="-" />
          </Card>
        </Col>
      </Row>

      {/* 搜索框 */}
      <Card className="card-chinese">
        <Input
          placeholder="搜索玩家..."
          prefix={<SearchOutlined />}
          size="large"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          allowClear
        />
      </Card>

      {/* 排行榜表格 */}
      <Card className="card-chinese">
        <Table
          columns={columns}
          dataSource={filteredData}
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 位玩家`,
          }}
          rowKey={(record) => record.user.id}
          size="middle"
        />
      </Card>

      {/* 段位说明 */}
      <Card className="card-chinese">
        <Title level={5} className="font-chinese mb-4">段位说明</Title>
        <Space direction="vertical" className="w-full">
          <div className="flex items-center gap-4">
            <Tag color="purple" className="text-sm">大师</Tag>
            <Text className="text-sm">天梯分 ≥ 2000</Text>
          </div>
          <div className="flex items-center gap-4">
            <Tag color="orange" className="text-sm">高级</Tag>
            <Text className="text-sm">1600 ≤ 天梯分 &lt; 2000</Text>
          </div>
          <div className="flex items-center gap-4">
            <Tag color="green" className="text-sm">中级</Tag>
            <Text className="text-sm">1200 ≤ 天梯分 &lt; 1600</Text>
          </div>
          <div className="flex items-center gap-4">
            <Tag color="blue" className="text-sm">初级</Tag>
            <Text className="text-sm">天梯分 &lt; 1200</Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default LeaderboardPage;
