import React, { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Input,
  Select,
  Tag,
  Modal,
  Typography,
  message,
  Tooltip,
  List,
  Divider,
} from 'antd';
import {
  SearchOutlined,
  EyeOutlined,
  StopOutlined,
  ExclamationCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { gamesApi } from '../../api/games';
import type { Game } from '../../types';
import { useHasPermission } from '../../hooks/useHasPermission';

const { Title, Text } = Typography;
const { confirm } = Modal;

const GamesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>();
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const { isSuperAdmin } = useHasPermission();

  // 获取游戏列表
  const { data, isLoading } = useQuery({
    queryKey: ['games', page, pageSize, search, statusFilter],
    queryFn: () =>
      gamesApi.getList({
        page,
        pageSize,
        search: search || undefined,
        status: statusFilter,
      }),
  });

  // 中止游戏 Mutation
  const abortMutation = useMutation({
    mutationFn: (id: string) => gamesApi.abortGame(id),
    onSuccess: () => {
      message.success('对局已中止');
      queryClient.invalidateQueries({ queryKey: ['games'] });
    },
    onError: () => {
      message.error('中止对局失败');
    },
  });

  // 清理过期等待 Mutation
  const clearExpiredMutation = useMutation({
    mutationFn: () => gamesApi.clearExpiredWaiting(),
    onSuccess: (res) => {
      message.success(`成功清理 ${res?.count || 0} 个过期等待中的对局`);
      queryClient.invalidateQueries({ queryKey: ['games'] });
    },
    onError: () => {
      message.error('清理失败');
    },
  });

  const handleAbort = (id: string) => {
    confirm({
      title: '确定要中止这场对局吗？',
      icon: <ExclamationCircleOutlined />,
      content: '中止后对局将立即结束，不可恢复。',
      okText: '确定',
      okType: 'danger',
      cancelText: '取消',
      onOk() {
        return abortMutation.mutateAsync(id);
      },
    });
  };

  const handleClearExpired = () => {
    confirm({
      title: '确定要清理过期等待吗？',
      icon: <DeleteOutlined />,
      content: '系统将取消所有超过 15 分钟无人加入的“等待中”对局。',
      okText: '确定清理',
      cancelText: '取消',
      onOk() {
        return clearExpiredMutation.mutateAsync();
      },
    });
  };

  const handleViewDetail = (game: Game) => {
    setSelectedGame(game);
    setIsDetailModalOpen(true);
  };

  const columns = [
    {
      title: '游戏 ID',
      dataIndex: 'id',
      key: 'id',
      width: 150,
      ellipsis: true,
    },
    {
      title: '红方',
      dataIndex: 'redPlayerName',
      key: 'redPlayerName',
    },
    {
      title: '黑方',
      dataIndex: 'blackPlayerName',
      key: 'blackPlayerName',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: Game) => {
        const statusConfig: Record<string, { color: string; text: string }> = {
          waiting: { color: 'processing', text: '等待中' },
          playing: { color: 'success', text: '对局中' },
          finished: { color: 'default', text: '已结束' },
          completed: { color: 'default', text: '已结束' },
          aborted: { color: 'warning', text: '已中止' },
          abandoned: { color: 'error', text: '已放弃' },
        };
        const config = statusConfig[status] || { color: 'default', text: status };
        
        // 异常提醒逻辑：开始时间超过 2 小时且状态仍为“对局中”
        const isAbnormal = 
          status === 'playing' && 
          (new Date().getTime() - new Date(record.startTime).getTime()) > 2 * 60 * 60 * 1000;

        return (
          <Space>
            <Tag color={config.color}>{config.text}</Tag>
            {isAbnormal && (
              <Tooltip title="对局时间过长（超过 2 小时），可能存在异常">
                <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
              </Tooltip>
            )}
          </Space>
        );
      },
    },
    {
      title: '胜负',
      dataIndex: 'result',
      key: 'result',
      render: (result: string) => {
        if (!result) return '-';
        const resultConfig: Record<string, { color: string; text: string }> = {
          red_win: { color: 'error', text: '红胜' },
          black_win: { color: 'blue', text: '黑胜' },
          draw: { color: 'warning', text: '和棋' },
          white_win: { color: 'error', text: '红胜' }, // 兼容 white 命名
        };
        const config = resultConfig[result] || { color: 'default', text: result };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '开始时间',
      dataIndex: 'startTime',
      key: 'startTime',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Game) => (
        <Space>
          <Button
            type="primary"
            size="small"
            ghost
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          {record.status === 'playing' && (
            <Tooltip title={!isSuperAdmin ? "权限不足" : ""}>
              <Button
                danger
                size="small"
                icon={<StopOutlined />}
                onClick={() => handleAbort(record.id)}
                loading={abortMutation.isPending && abortMutation.variables === record.id}
                disabled={!isSuperAdmin}
              >
                中止
              </Button>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          游戏管理
        </Title>
        <Button 
          icon={<DeleteOutlined />} 
          onClick={handleClearExpired}
          loading={clearExpiredMutation.isPending}
        >
          清理过期等待
        </Button>
      </div>

      {/* 搜索和筛选 */}
      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索玩家名称"
          prefix={<SearchOutlined />}
          style={{ width: 300 }}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onPressEnter={() => setPage(1)}
          allowClear
        />
        <Select
          placeholder="状态筛选"
          style={{ width: 150 }}
          value={statusFilter}
          onChange={setStatusFilter}
          allowClear
          options={[
            { value: 'waiting', label: '等待中' },
            { value: 'playing', label: '对局中' },
            { value: 'finished', label: '已结束' },
            { value: 'aborted', label: '已中止' },
          ]}
        />
      </Space>

      {/* 游戏列表 */}
      <Table
        columns={columns}
        dataSource={data?.data}
        loading={isLoading}
        rowKey="id"
        pagination={{
          current: page,
          pageSize,
          total: data?.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 局`,
          onChange: (newPage, newPageSize) => {
            setPage(newPage);
            setPageSize(newPageSize);
          },
        }}
      />

      {/* 游戏详情弹窗 */}
      <Modal
        title="游戏详情"
        open={isDetailModalOpen}
        onCancel={() => setIsDetailModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setIsDetailModalOpen(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {selectedGame && (
          <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', gap: '24px' }}>
              <div style={{ flex: 1 }}>
                <Title level={5}>基本信息</Title>
                <p><strong>游戏 ID：</strong><Text copyable>{selectedGame.id}</Text></p>
                <p><strong>对局状态：</strong>{selectedGame.status}</p>
                <p><strong>红方玩家：</strong>{selectedGame.redPlayerName || selectedGame.whitePlayer?.username}</p>
                <p><strong>黑方玩家：</strong>{selectedGame.blackPlayerName || selectedGame.blackPlayer?.username}</p>
                <p><strong>开始时间：</strong>{new Date(selectedGame.startTime || selectedGame.createdAt).toLocaleString('zh-CN')}</p>
                {(selectedGame.endTime || selectedGame.completedAt) && (
                  <p><strong>结束时间：</strong>{new Date((selectedGame.endTime || selectedGame.completedAt)!).toLocaleString('zh-CN')}</p>
                )}
                <p><strong>对局结果：</strong>{selectedGame.result || selectedGame.winner || '进行中'}</p>
                <p><strong>FEN 串：</strong><Text code>{selectedGame.fen || '暂无'}</Text></p>
                
                <Divider />
                
                <Title level={5}>棋盘预览</Title>
                <div style={{ 
                  width: '100%', 
                  aspectRatio: '9/10', 
                  backgroundColor: '#f5f5f5', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  border: '1px dashed #d9d9d9',
                  borderRadius: '4px'
                }}>
                  <Text type="secondary">棋盘预览图占位 (FEN: {selectedGame.fen?.substring(0, 10)}...)</Text>
                </div>
              </div>
              
              <div style={{ width: '300px' }}>
                <Title level={5}>对局日志 (Move History)</Title>
                <List
                  size="small"
                  bordered
                  dataSource={selectedGame.moveHistory || []}
                  locale={{ emptyText: '暂无移动记录' }}
                  renderItem={(item, index) => (
                    <List.Item>
                      <Text strong>{Math.floor(index / 2) + 1}. </Text>
                      <Text>{item.move}</Text>
                      <Text type="secondary" style={{ fontSize: '12px', float: 'right' }}>{item.time}</Text>
                    </List.Item>
                  )}
                  style={{ maxHeight: '400px', overflowY: 'auto' }}
                />
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default GamesPage;