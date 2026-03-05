import React, { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Input,
  Select,
  Tag,
  Modal,
  message,
  Typography,
  Popconfirm,
  Card,
  Tooltip,
  Badge,
  Row,
  Col,
  Statistic,
} from 'antd';
import { SearchOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '../../api/users';
import type { User } from '../../types';
import { useHasPermission } from '../../hooks/useHasPermission';

const { Title, Text } = Typography;

const UsersPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const queryClient = useQueryClient();
  const { isSuperAdmin } = useHasPermission();

  // 获取用户列表
  const { data, isLoading } = useQuery({
    queryKey: ['users', page, pageSize, search, statusFilter],
    queryFn: () =>
      usersApi.getList({
        page,
        pageSize,
        search: search || undefined,
        status: statusFilter,
      }),
  });

  // 更新用户状态
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'active' | 'inactive' | 'banned' }) =>
      usersApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      message.success('状态更新成功');
    },
    onError: () => {
      message.error('状态更新失败');
    },
  });

  // 删除用户
  const deleteMutation = useMutation({
    mutationFn: (id: string) => usersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      message.success('用户删除成功');
    },
    onError: () => {
      message.error('用户删除失败');
    },
  });

  const handleViewDetail = (user: User) => {
    setSelectedUser(user);
    setIsDetailModalOpen(true);
  };

  const handleStatusChange = (userId: string, newStatus: 'active' | 'inactive' | 'banned') => {
    updateStatusMutation.mutate({ id: userId, status: newStatus });
  };

  const handleDelete = (userId: string) => {
    deleteMutation.mutate(userId);
  };

  const columns = [
    {
      title: '用户信息',
      key: 'userInfo',
      width: 250,
      render: (_: unknown, record: User) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.username}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.email}</Text>
        </Space>
      ),
    },
    {
      title: 'Elo 等级',
      dataIndex: 'elo',
      key: 'elo',
      sorter: (a: User, b: User) => a.elo - b.elo,
      render: (elo: number) => (
        <Tag color={elo > 1500 ? 'gold' : 'blue'}>{elo}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const textMap: Record<string, string> = {
          active: '正常',
          inactive: '未激活',
          banned: '已封禁',
        };
        const badgeStatus = status === 'active' ? 'success' : status === 'banned' ? 'error' : 'default';
        return <Badge status={badgeStatus as any} text={textMap[status]} />;
      },
    },
    {
      title: '对局概况',
      key: 'stats',
      render: (_: unknown, record: User) => {
        const winRate = record.totalGames > 0 
          ? ((record.wins / record.totalGames) * 100).toFixed(1)
          : '0';
        return (
          <Tooltip title={`胜 ${record.wins} / 平 ${record.draws} / 负 ${record.losses}`}>
            <Space split={<Text type="secondary">|</Text>}>
              <span>局数: {record.totalGames}</span>
              <span style={{ color: Number(winRate) > 50 ? '#f5222d' : 'inherit' }}>胜率: {winRate}%</span>
            </Space>
          </Tooltip>
        );
      },
    },
    {
      title: '最近活跃',
      dataIndex: 'lastLoginAt',
      key: 'lastLoginAt',
      render: (date: string) => date ? new Date(date).toLocaleDateString('zh-CN') : '从未登录',
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      width: 220,
      render: (_: unknown, record: User) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          <Tooltip title={!isSuperAdmin ? "权限不足" : ""}>
            <Select
              size="small"
              value={record.status}
              style={{ width: 90 }}
              onChange={(value) => handleStatusChange(record.id, value)}
              disabled={!isSuperAdmin}
              options={[
                { value: 'active', label: '正常' },
                { value: 'inactive', label: '未激活' },
                { value: 'banned', label: '封禁' },
              ]}
            />
          </Tooltip>
          <Tooltip title={!isSuperAdmin ? "权限不足" : ""}>
            <Popconfirm
              title="危险操作"
              description="确定要彻底删除该用户及其所有数据吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              disabled={!isSuperAdmin}
            >
              <Button type="link" size="small" danger icon={<DeleteOutlined />} disabled={!isSuperAdmin}>
                删除
              </Button>
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <Card bordered={false}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>用户管理</Title>
        <Button type="primary" icon={<PlusOutlined />}>
          新增用户
        </Button>
      </div>

      <div style={{ marginBottom: 16, display: 'flex', gap: 12 }}>
        <Input
          placeholder="搜索用户名或邮箱"
          prefix={<SearchOutlined />}
          style={{ width: 300 }}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onPressEnter={() => setPage(1)}
          allowClear
        />
        <Select
          placeholder="用户状态"
          style={{ width: 120 }}
          value={statusFilter}
          onChange={setStatusFilter}
          allowClear
          options={[
            { value: 'active', label: '正常' },
            { value: 'inactive', label: '未激活' },
            { value: 'banned', label: '已封禁' },
          ]}
        />
      </div>

      <Table
        columns={columns}
        dataSource={data?.data}
        loading={isLoading}
        rowKey="id"
        scroll={{ x: 'max-content' }}
        pagination={{
          current: page,
          pageSize,
          total: data?.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 位用户`,
          onChange: (newPage, newPageSize) => {
            setPage(newPage);
            setPageSize(newPageSize);
          },
        }}
      />

      <Modal
        title="用户全量档案"
        open={isDetailModalOpen}
        onCancel={() => setIsDetailModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setIsDetailModalOpen(false)}>
            关闭
          </Button>,
        ]}
        width={600}
      >
        {selectedUser && (
          <div className="user-profile-detail">
            <Row gutter={[0, 16]}>
              <Col span={12}><Text type="secondary">账户名称：</Text>{selectedUser.username}</Col>
              <Col span={12}><Text type="secondary">电子邮箱：</Text>{selectedUser.email}</Col>
              <Col span={12}><Text type="secondary">用户昵称：</Text>{selectedUser.nickname || '-'}</Col>
              <Col span={12}><Text type="secondary">Elo 积分：</Text><Tag color="orange">{selectedUser.elo}</Tag></Col>
              <Col span={24}><hr style={{ border: 'none', borderTop: '1px solid #f0f0f0' }} /></Col>
              <Col span={8}><Statistic title="总对局" value={selectedUser.totalGames} valueStyle={{ fontSize: 18 }} /></Col>
              <Col span={16}>
                <Text type="secondary">战绩统计：</Text>
                <div style={{ marginTop: 8 }}>
                  <Tag color="green">胜: {selectedUser.wins}</Tag>
                  <Tag color="default">平: {selectedUser.draws}</Tag>
                  <Tag color="red">负: {selectedUser.losses}</Tag>
                </div>
              </Col>
              <Col span={24}><hr style={{ border: 'none', borderTop: '1px solid #f0f0f0' }} /></Col>
              <Col span={12}><Text type="secondary">注册时间：</Text>{new Date(selectedUser.createdAt).toLocaleString('zh-CN')}</Col>
              <Col span={12}><Text type="secondary">最后登录：</Text>{selectedUser.lastLoginAt ? new Date(selectedUser.lastLoginAt).toLocaleString('zh-CN') : '-'}</Col>
            </Row>
          </div>
        )}
      </Modal>
    </Card>
  );
};

export default UsersPage;
