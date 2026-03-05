import React, { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Typography,
  Card,
  Row,
  Col,
  Statistic,
  Badge,
  message,
  Tooltip,
  Modal,
  Empty,
} from 'antd';
import {
  SyncOutlined,
  UserOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InteractionOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { matchmakingApi } from '../../api/matchmaking';
import type { MatchmakingRecord } from '../../types';

const { Title, Text } = Typography;

const MatchmakingPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>();
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const queryClient = useQueryClient();

  // 获取匹配列表
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['matchmaking', page, pageSize, statusFilter],
    queryFn: () =>
      matchmakingApi.getList({
        page,
        pageSize,
        status: statusFilter,
      }),
    refetchInterval: 5000, // 每5秒轮询一次
  });

  // 获取匹配统计
  const { data: stats } = useQuery({
    queryKey: ['matchmaking-stats'],
    queryFn: () => matchmakingApi.getStatistics(),
    refetchInterval: 5000,
  });

  // 手动干预匹配
  const manualMatchMutation = useMutation({
    mutationFn: (playerIds: string[]) => matchmakingApi.manualMatch(playerIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matchmaking'] });
      setSelectedRowKeys([]);
      message.success('手动匹配指令已发送');
    },
    onError: () => {
      message.error('手动匹配指令发送失败');
    },
  });

  // 取消匹配
  const cancelMatchMutation = useMutation({
    mutationFn: (id: string) => matchmakingApi.cancelMatch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matchmaking'] });
      message.success('已取消该匹配请求');
    },
    onError: () => {
      message.error('取消匹配失败');
    },
  });

  const handleManualMatch = () => {
    if (selectedRowKeys.length !== 2) {
      message.warning('请选择恰好两名玩家进行匹配');
      return;
    }
    
    Modal.confirm({
      title: '手动干预匹配',
      content: '确定要将选中的两名玩家强制进行对局匹配吗？',
      onOk: () => {
        const playerIds = selectedRowKeys.map(key => {
          const record = data?.data.find(r => r.id === key);
          return record?.playerId || '';
        }).filter(id => !!id);
        manualMatchMutation.mutate(playerIds);
      },
    });
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      ellipsis: true,
      render: (id: string) => <Text copyable={{ text: id }}>{id.slice(0, 8)}</Text>,
    },
    {
      title: '玩家 ID',
      dataIndex: 'playerId',
      key: 'playerId',
      render: (id: string) => (
        <Space>
          <UserOutlined />
          <Text strong>{id}</Text>
        </Space>
      ),
    },
    {
      title: '对手 ID',
      dataIndex: 'opponentId',
      key: 'opponentId',
      render: (id: string) => id ? (
        <Space>
          <UserOutlined />
          <Text>{id}</Text>
        </Space>
      ) : <Text type="secondary">-</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const config: Record<string, { color: string; text: string; icon: any }> = {
          pending: { color: 'processing', text: '等待中', icon: <SyncOutlined spin /> },
          matched: { color: 'success', text: '已匹配', icon: <CheckCircleOutlined /> },
          completed: { color: 'blue', text: '已完成', icon: <CheckCircleOutlined /> },
          cancelled: { color: 'default', text: '已取消', icon: <CloseCircleOutlined /> },
        };
        const item = config[status] || config.pending;
        return <Tag icon={item.icon} color={item.color}>{item.text}</Tag>;
      },
    },
    {
      title: '开始时间',
      dataIndex: 'matchedAt',
      key: 'matchedAt',
      render: (date: string) => (
        <Space>
          <ClockCircleOutlined />
          {new Date(date).toLocaleString()}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: MatchmakingRecord) => (
        <Space>
          {record.status === 'pending' && (
            <Button 
              type="link" 
              danger 
              size="small" 
              onClick={() => cancelMatchMutation.mutate(record.id)}
            >
              取消
            </Button>
          )}
          <Button type="link" size="small">日志</Button>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
    getCheckboxProps: (record: MatchmakingRecord) => ({
      disabled: record.status !== 'pending',
    }),
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>匹配管理</Title>
        <Space>
          <Button 
            icon={<SyncOutlined spin={isFetching} />} 
            onClick={() => queryClient.invalidateQueries({ queryKey: ['matchmaking'] })}
          >
            刷新队列
          </Button>
          <Button 
            type="primary" 
            icon={<InteractionOutlined />} 
            disabled={selectedRowKeys.length !== 2}
            onClick={handleManualMatch}
          >
            手动匹配 ({selectedRowKeys.length})
          </Button>
        </Space>
      </div>

      {/* 实时统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="当前队列人数"
              value={stats?.inQueueCount || 0}
              prefix={<UserOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="平均等待时间"
              value={stats?.avgWaitTime || 0}
              suffix="s"
              prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="今日匹配成功率"
              value={stats?.successRate ? stats.successRate * 100 : 0}
              precision={1}
              suffix="%"
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
      </Row>

      <Card bordered={false} title="实时匹配队列">
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={data?.data}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 'max-content' }}
          pagination={{
            current: page,
            pageSize,
            total: data?.total,
            onChange: (p, s) => {
              setPage(p);
              setPageSize(s);
            },
          }}
          locale={{
            emptyText: <Empty description="当前匹配队列为空" />
          }}
        />
      </Card>
    </div>
  );
};

export default MatchmakingPage;
