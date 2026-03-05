import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Button, Typography, Space, Statistic, Divider } from 'antd';
import {
  RobotOutlined,
  TeamOutlined,
  TrophyOutlined,
  RightOutlined,
  FireOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores';

const { Title, Paragraph, Text } = Typography;

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12">
        <Title
          level={1}
          className="font-chinese text-4xl md:text-6xl mb-4"
        >
          <span className="text-gradient">中国象棋</span> 在线对战平台
        </Title>
        <Paragraph className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          与 AI 对弈提升棋艺，与真人匹配切磋技艺。天梯排名，见证你的成长之路。
        </Paragraph>
        
        <Space size="large" className="mt-8 flex-wrap justify-center">
          <Button
            type="primary"
            size="large"
            icon={<RobotOutlined />}
            onClick={() => navigate('/ai-game')}
            className="bg-gradient-to-r from-red-600 to-yellow-500 h-12 px-6 text-lg"
          >
            AI 对战
          </Button>
          <Button
            size="large"
            icon={<TeamOutlined />}
            onClick={() => isAuthenticated ? navigate('/matchmaking') : navigate('/login')}
            className="h-12 px-6 text-lg border-2"
          >
            匹配对战
          </Button>
        </Space>
      </div>

      {/* 功能卡片 */}
      <Row gutter={[24, 24]} className="mt-12">
        <Col xs={24} md={8}>
          <Card
            hoverable
            className="h-full card-chinese"
            cover={
              <div className="h-48 bg-gradient-to-br from-red-500 to-yellow-500 flex items-center justify-center">
                <RobotOutlined className="text-8xl text-white opacity-80" />
              </div>
            }
            onClick={() => navigate('/ai-game')}
          >
            <Card.Meta
              title={
                <div className="flex items-center gap-2">
                  <RobotOutlined className="text-red-600" />
                  <span>AI 对战</span>
                </div>
              }
              description={
                <div className="mt-4">
                  <Text className="text-gray-600 dark:text-gray-400">
                    10 个难度等级，从入门到大师，循序渐进提升棋艺。
                    随时随地，想下就下。
                  </Text>
                  <div className="mt-4 flex items-center text-red-600">
                    <span>立即开始</span>
                    <RightOutlined className="ml-1 text-sm" />
                  </div>
                </div>
              }
            />
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card
            hoverable
            className="h-full card-chinese"
            cover={
              <div className="h-48 bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                <TeamOutlined className="text-8xl text-white opacity-80" />
              </div>
            }
            onClick={() => navigate('/matchmaking')}
          >
            <Card.Meta
              title={
                <div className="flex items-center gap-2">
                  <TeamOutlined className="text-blue-600" />
                  <span>匹配对战</span>
                </div>
              }
              description={
                <div className="mt-4">
                  <Text className="text-gray-600 dark:text-gray-400">
                    智能 Elo 匹配系统，为你找到实力相当的对手。
                    在线对战，实时竞技。
                  </Text>
                  <div className="mt-4 flex items-center text-blue-600">
                    <span>加入匹配</span>
                    <RightOutlined className="ml-1 text-sm" />
                  </div>
                </div>
              }
            />
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card
            hoverable
            className="h-full card-chinese"
            cover={
              <div className="h-48 bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center">
                <TrophyOutlined className="text-8xl text-white opacity-80" />
              </div>
            }
            onClick={() => navigate('/leaderboard')}
          >
            <Card.Meta
              title={
                <div className="flex items-center gap-2">
                  <TrophyOutlined className="text-yellow-600" />
                  <span>天梯排名</span>
                </div>
              }
              description={
                <div className="mt-4">
                  <Text className="text-gray-600 dark:text-gray-400">
                    查看天梯排行榜，追踪你的排名变化。
                    冲击更高段位，证明你的实力。
                  </Text>
                  <div className="mt-4 flex items-center text-yellow-600">
                    <span>查看排名</span>
                    <RightOutlined className="ml-1 text-sm" />
                  </div>
                </div>
              }
            />
          </Card>
        </Col>
      </Row>

      {/* 统计信息 */}
      <Divider className="my-12" />
      
      <div className="text-center mb-8">
        <Title level={3} className="font-chinese">平台数据</Title>
      </div>
      
      <Row gutter={[24, 24]} className="justify-center">
        <Col xs={12} md={6}>
          <div className="text-center">
            <Statistic
              title="注册用户"
              value={10000}
              suffix="+"
              valueStyle={{ color: '#dc2626' }}
              prefix={<FireOutlined />}
            />
          </div>
        </Col>
        <Col xs={12} md={6}>
          <div className="text-center">
            <Statistic
              title="总对局数"
              value={50000}
              suffix="+"
              valueStyle={{ color: '#1677ff' }}
              prefix={<ClockCircleOutlined />}
            />
          </div>
        </Col>
        <Col xs={12} md={6}>
          <div className="text-center">
            <Statistic
              title="最高天梯分"
              value={2400}
              valueStyle={{ color: '#faad14' }}
              prefix={<TrophyOutlined />}
            />
          </div>
        </Col>
        <Col xs={12} md={6}>
          <div className="text-center">
            <Statistic
              title="在线玩家"
              value={500}
              suffix="+"
              valueStyle={{ color: '#52c41a' }}
              prefix={<TeamOutlined />}
            />
          </div>
        </Col>
      </Row>

      {/* 公告/活动 */}
      <Divider className="my-12" />
      
      <div className="text-center mb-8">
        <Title level={3} className="font-chinese">最新公告</Title>
      </div>
      
      <Row gutter={[24, 24]}>
        <Col xs={24} md={12}>
          <Card title="🎉 新版本上线" className="card-chinese">
            <Paragraph>
              中国象棋平台全新版本正式上线！新增 AI 对战、在线匹配、天梯排名等功能，
              界面全面优化，带来更佳的对弈体验。
            </Paragraph>
            <Text type="secondary" className="text-sm">2026-03-03</Text>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="🏆 首届天梯赛开启" className="card-chinese">
            <Paragraph>
              首届中国象棋天梯赛正式开启！参与比赛赢取丰厚奖励，
              冲击排行榜前 100 名即可获得限定头像框和称号。
            </Paragraph>
            <Text type="secondary" className="text-sm">2026-03-01</Text>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default HomePage;
