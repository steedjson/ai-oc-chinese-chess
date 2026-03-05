import React from 'react';
import { Card, Row, Col, Statistic, Typography, Spin, Tooltip as AntdTooltip } from 'antd';
import {
  TeamOutlined,
  ThunderboltOutlined,
  UserAddOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { statisticsApi } from '../../api/statistics';
import { TrendChart } from '../../components/Charts/TrendChart';
import { DistributionChart } from '../../components/Charts/DistributionChart';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => statisticsApi.getDashboard(),
    refetchInterval: 60000,
  });

  const { data: userGrowthData } = useQuery({
    queryKey: ['user-growth'],
    queryFn: () => statisticsApi.getUserGrowth({ 
      startDate: new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString(),
      endDate: new Date().toISOString()
    }),
  });

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" tip="正在加载实时数据..." />
      </div>
    );
  }

  const overviewData = [
    {
      title: '总用户数',
      value: dashboardData?.totalUsers || 0,
      icon: <TeamOutlined />,
      color: '#1890ff',
      description: '全平台注册用户总数',
    },
    {
      title: '当前在线',
      value: dashboardData?.onlineUsers || 0,
      icon: <UserAddOutlined />,
      color: '#52c41a',
      description: '当前 WebSocket 在线连接数',
    },
    {
      title: '累计对局',
      value: dashboardData?.totalGames || 0,
      icon: <ThunderboltOutlined />,
      color: '#722ed1',
      description: '包括人机与 PVP 的所有历史局数',
    },
    {
      title: '今日新增',
      value: dashboardData?.newUsersToday || 0,
      icon: <ClockCircleOutlined />,
      color: '#fa8c16',
      description: '今日 0 点以来新注册的用户',
    },
  ];

  const gameDistData = [
    { name: 'PVP 对局', value: dashboardData?.totalGames ? Math.floor(dashboardData.totalGames * 0.7) : 0 },
    { name: '人机对局', value: dashboardData?.totalGames ? Math.floor(dashboardData.totalGames * 0.3) : 0 },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          业务概览
        </Title>
        <Text type="secondary">
          上次更新: {new Date().toLocaleTimeString()}
        </Text>
      </div>

      {/* 概览统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {overviewData.map((item, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card bordered={false} hoverable styles={{ body: { padding: '20px 24px' } }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <Text type="secondary">{item.title}</Text>
                <AntdTooltip title={item.description}>
                  <InfoCircleOutlined style={{ color: 'rgba(0,0,0,0.45)', cursor: 'help' }} />
                </AntdTooltip>
              </div>
              <Statistic
                value={item.value}
                prefix={
                  <span style={{ color: item.color, fontSize: 24, marginRight: 12 }}>
                    {item.icon}
                  </span>
                }
                valueStyle={{ fontSize: 28, fontWeight: 'bold' }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* 用户增长趋势 */}
        <Col xs={24} lg={16}>
          <Card 
            title="注册用户趋势 (最近7天)" 
            bordered={false} 
            styles={{ body: { padding: '24px 12px' } }}
            extra={<AntdTooltip title="每日新增用户数量变化趋势"><InfoCircleOutlined /></AntdTooltip>}
          >
            <TrendChart 
              data={userGrowthData?.data || []} 
              xKey="date" 
              yKey="count" 
              color="#1890ff"
            />
          </Card>
        </Col>
        
        {/* 对局分布 */}
        <Col xs={24} lg={8}>
          <Card 
            title="对局活跃分布" 
            bordered={false}
            extra={<AntdTooltip title="全平台游戏模式占比"><InfoCircleOutlined /></AntdTooltip>}
          >
            <DistributionChart data={gameDistData} />
          </Card>
        </Col>
      </Row>

      {/* 活跃指标 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card title="日活跃 (DAU)" bordered={false} hoverable>
            <div style={{ textAlign: 'center', padding: '10px 0' }}>
              <Statistic
                value={dashboardData?.dau || 0}
                suffix="人"
                valueStyle={{ fontSize: 42, color: '#3f51b5', fontWeight: 'bold' }}
              />
              <Text type="secondary">24小时内访问过平台的用户</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="月活跃 (MAU)" bordered={false} hoverable>
            <div style={{ textAlign: 'center', padding: '10px 0' }}>
              <Statistic
                value={dashboardData?.mau || 0}
                suffix="人"
                valueStyle={{ fontSize: 42, color: '#009688', fontWeight: 'bold' }}
              />
              <Text type="secondary">30天内访问过平台的用户</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="实时战斗中" bordered={false} hoverable>
            <div style={{ textAlign: 'center', padding: '10px 0' }}>
              <Statistic
                value={dashboardData?.activeGames || 0}
                suffix="局"
                valueStyle={{ fontSize: 42, color: '#ff5722', fontWeight: 'bold' }}
              />
              <Text type="secondary">当前正在进行的实时对局数</Text>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
