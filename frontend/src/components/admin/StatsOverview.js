import React from 'react';
import { Card, Row, Col, Statistic, Progress } from 'antd';
import { UserOutlined, FundOutlined, TrophyOutlined, RiseOutlined } from '@ant-design/icons';

const StatsOverview = ({ stats }) => {
  const {
    totalPlayers = 0,
    activeGames = 0,
    aiUsageRate = 0,
    winRate = 0,
    totalGames = 0,
    playerRetention = 0
  } = stats;

  return (
    <div className="stats-overview">
      <Row gutter={[16, 16]}>
        {/* Total Players Card */}
        <Col xs={24} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="总玩家数"
              value={totalPlayers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>

        {/* Active Games Card */}
        <Col xs={24} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="活跃对局"
              value={activeGames}
              prefix={<FundOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>

        {/* Total Games Card */}
        <Col xs={24} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="总对局数"
              value={totalGames}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>

        {/* Win Rate Card */}
        <Col xs={24} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="平均胜率"
              value={winRate}
              precision={2}
              suffix="%"
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* AI Usage Rate */}
        <Col xs={24} md={12}>
          <Card title="AI 使用率">
            <div style={{ marginBottom: 16 }}>
              <span>AI 对局占比: {aiUsageRate}%</span>
              <Progress percent={aiUsageRate} strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} />
            </div>
          </Card>
        </Col>

        {/* Player Retention */}
        <Col xs={24} md={12}>
          <Card title="玩家留存率">
            <div style={{ marginBottom: 16 }}>
              <span>7日留存率: {playerRetention}%</span>
              <Progress percent={playerRetention} strokeColor={{ '0%': '#ff5500', '100%': '#52c41a' }} />
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* Game Modes Distribution */}
        <Col xs={24} md={8}>
          <Card title="游戏模式分布">
            <div style={{ padding: '10px 0' }}>
              <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span>人对人:</span>
                <span>65%</span>
              </div>
              <Progress percent={65} size="small" />
            </div>
            <div style={{ padding: '10px 0' }}>
              <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span>人对AI:</span>
                <span>35%</span>
              </div>
              <Progress percent={35} size="small" status="active" />
            </div>
          </Card>
        </Col>

        {/* Peak Hours */}
        <Col xs={24} md={8}>
          <Card title="活跃时段">
            <div style={{ padding: '10px 0' }}>
              <div style={{ marginBottom: 8 }}>晚上 7-9 点: 最高峰</div>
              <div style={{ marginBottom: 8 }}>下午 2-4 点: 次高峰</div>
              <div style={{ marginBottom: 8 }}>中午 12-1 点: 午休时段</div>
            </div>
          </Card>
        </Col>

        {/* Performance Metrics */}
        <Col xs={24} md={8}>
          <Card title="性能指标">
            <div style={{ padding: '10px 0' }}>
              <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span>响应时间:</span>
                <span>&lt;200ms</span>
              </div>
              <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span>服务器负载:</span>
                <span>正常</span>
              </div>
              <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span>错误率:</span>
                <span>&lt;0.1%</span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default StatsOverview;