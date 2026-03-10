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
  Card,
  Statistic,
  Row,
  Col,
  Alert,
  Badge,
  Descriptions,
} from 'antd';
import {
  SearchOutlined,
  EyeOutlined,
  StopOutlined,
  ExclamationCircleOutlined,
  DeleteOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { gamesApi } from '../../api/games';
import type { Game, AnomalyData, GameLog } from '../../types';
import { useHasPermission } from '../../hooks/useHasPermission';

const { Title, Text } = Typography;
const { confirm } = Modal;

const GamesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>();
  const [abnormalFilter, setAbnormalFilter] = useState<boolean>(false);
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);
  const [abortReason, setAbortReason] = useState('');
  const [isAbortModalOpen, setIsAbortModalOpen] = useState(false);
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const { isSuperAdmin } = useHasPermission();

  // 获取游戏列表
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['games', page, pageSize, search, statusFilter, abnormalFilter],
    queryFn: () =>
      gamesApi.getManagementList({
        page,
        pageSize,
        search: search || undefined,
        status: statusFilter,
        abnormal: abnormalFilter ? 'true' : undefined,
      }),
    enabled: isSuperAdmin, // 仅超级管理员可访问
  });

  // 获取异常对局
  const { data: anomaliesData } = useQuery({
    queryKey: ['anomalies'],
    queryFn: () => gamesApi.getAnomalies(),
    enabled: isSuperAdmin,
    refetchInterval: 60000, // 每分钟刷新
  });

  // 中止游戏 Mutation（管理端）
  const abortMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      gamesApi.abortGameAdmin(id, reason),
    onSuccess: () => {
      message.success('对局已中止');
      queryClient.invalidateQueries({ queryKey: ['games'] });
      setIsAbortModalOpen(false);
      setAbortReason('');
    },
    onError: (error: any) => {
      message.error(`中止对局失败：${error.message}`);
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

  // 标记异常 Mutation
  const markAbnormalMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      gamesApi.markAsAbnormal(id, reason),
    onSuccess: () => {
      message.success('对局已标记为异常');
      queryClient.invalidateQueries({ queryKey: ['games'] });
    },
    onError: () => {
      message.error('标记失败');
    },
  });

  const handleAbort = (id: string) => {
    setSelectedGameId(id);
    setIsAbortModalOpen(true);
  };

  const confirmAbort = () => {
    if (!selectedGameId) return;
    if (!abortReason.trim()) {
      message.warning('请输入中止原因');
      return;
    }
    abortMutation.mutate({ id: selectedGameId, reason: abortReason });
  };

  const handleClearExpired = () => {
    confirm({
      title: '确定要清理过期等待吗？',
      icon: <DeleteOutlined />,
      content: '系统将取消所有超过 15 分钟无人加入的"等待中"对局。',
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

  const handleViewLogs = (game: Game) => {
    setSelectedGame(game);
    setIsLogModalOpen(true);
  };

  const handleMarkAbnormal = (game: Game) => {
    confirm({
      title: '标记对局为异常',
      content: (
        <Input.TextArea
          placeholder="请输入标记原因"
          rows={3}
          onChange={(e) => setAbortReason(e.target.value)}
          autoFocus
        />
      ),
      okText: '确定标记',
      cancelText: '取消',
      onOk() {
        if (!abortReason.trim()) {
          message.warning('请输入标记原因');
          return Promise.reject();
        }
        return markAbnormalMutation.mutateAsync({ id: game.id, reason: abortReason });
      },
      afterClose: () => setAbortReason(''),
    });
  };

  // 计算统计数据
  const stats = {
    total: data?.total || 0,
    anomalies: anomaliesData?.total || 0,
    playing: data?.data?.filter((g) => g.status === 'playing').length || 0,
    waiting: data?.data?.filter((g) => g.status === 'waiting').length || 0,
  };

  const columns = [
    {
      title: '游戏 ID',
      dataIndex: 'id',
      key: 'id',
      width: 150,
      ellipsis: true,
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: '红方',
      dataIndex: 'redPlayerName',
      key: 'redPlayerName',
      render: (_: unknown, record: Game) => record.redPlayerName || record.whitePlayer?.username || '-',
    },
    {
      title: '黑方',
      dataIndex: 'blackPlayerName',
      key: 'blackPlayerName',
      render: (_: unknown, record: Game) => record.blackPlayerName || record.blackPlayer?.username || '-',
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

        // 异常提醒逻辑：开始时间超过 2 小时且状态仍为"对局中"
        const isAbnormal =
          status === 'playing' &&
          record.startTime &&
          new Date().getTime() - new Date(record.startTime).getTime() > 2 * 60 * 60 * 1000;

        return (
          <Space>
            <Tag color={config.color}>{config.text}</Tag>
            {isAbnormal && (
              <Tooltip title="对局时间过长（超过 2 小时），可能存在异常">
                <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
              </Tooltip>
            )}
            {record.isAbnormal && (
              <Tag color="red">
                <WarningOutlined /> 异常
              </Tag>
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
          white_win: { color: 'error', text: '红胜' },
        };
        const config = resultConfig[result] || { color: 'default', text: result };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '步数',
      dataIndex: 'moveCount',
      key: 'moveCount',
      render: (count: number) => count || 0,
    },
    {
      title: '开始时间',
      dataIndex: 'startTime',
      key: 'startTime',
      render: (date: string) => (date ? new Date(date).toLocaleString('zh-CN') : '-'),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      width: 280,
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
          <Button
            size="small"
            icon={<ExportOutlined />}
            onClick={() => handleViewLogs(record)}
          >
            日志
          </Button>
          {record.status === 'playing' && (
            <Tooltip title={!isSuperAdmin ? '权限不足' : ''}>
              <Button
                danger
                size="small"
                icon={<StopOutlined />}
                onClick={() => handleAbort(record.id)}
                loading={abortMutation.isPending && abortMutation.variables?.id === record.id}
                disabled={!isSuperAdmin}
              >
                中止
              </Button>
            </Tooltip>
          )}
          {!record.isAbnormal && record.status === 'playing' && (
            <Tooltip title="标记为异常">
              <Button
                size="small"
                icon={<WarningOutlined />}
                onClick={() => handleMarkAbnormal(record)}
                loading={markAbnormalMutation.isPending && markAbnormalMutation.variables?.id === record.id}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  if (!isSuperAdmin) {
    return (
      <Alert
        message="权限不足"
        description="仅超级管理员可以访问游戏管理页面"
        type="warning"
        showIcon
      />
    );
  }

  return (
    <div>
      <Title level={2}>游戏管理</Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总对局数"
              value={stats.total}
              prefix={<Text strong>{stats.total}</Text>}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="对局中"
              value={stats.playing}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="等待中"
              value={stats.waiting}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="异常对局"
              value={stats.anomalies}
              valueStyle={{ color: '#cf1322' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 异常预警 */}
      {stats.anomalies > 0 && (
        <Alert
          message={`发现 ${stats.anomalies} 个异常对局`}
          description="请及时处理超时、可疑走棋等异常情况"
          type="warning"
          showIcon
          icon={<WarningOutlined />}
          style={{ marginBottom: 24 }}
          action={
            <Button size="small" onClick={() => setAbnormalFilter(true)}>
              查看异常对局
            </Button>
          }
        />
      )}

      {/* 操作栏 */}
      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索玩家名称或游戏 ID"
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
        <Select
          placeholder="异常筛选"
          style={{ width: 120 }}
          value={abnormalFilter ? 'true' : undefined}
          onChange={(value) => setAbnormalFilter(value === 'true')}
          allowClear
          options={[{ value: 'true', label: '仅异常' }]}
        />
        <Button
          icon={<DeleteOutlined />}
          onClick={handleClearExpired}
          loading={clearExpiredMutation.isPending}
        >
          清理过期等待
        </Button>
        <Button icon={<ExportOutlined />} onClick={() => message.info('导出功能开发中')}>
          导出列表
        </Button>
      </Space>

      {/* 游戏列表 */}
      <Table
        columns={columns}
        dataSource={data?.data}
        loading={isLoading}
        rowKey="id"
        scroll={{ x: 1200 }}
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
        width={900}
      >
        {selectedGame && (
          <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="游戏 ID">
                <Text code>{selectedGame.id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag>{selectedGame.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="红方玩家">
                {selectedGame.redPlayerName || selectedGame.whitePlayer?.username}
              </Descriptions.Item>
              <Descriptions.Item label="黑方玩家">
                {selectedGame.blackPlayerName || selectedGame.blackPlayer?.username}
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {selectedGame.startTime
                  ? new Date(selectedGame.startTime).toLocaleString('zh-CN')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="结束时间">
                {selectedGame.endTime || selectedGame.completedAt
                  ? new Date(selectedGame.endTime || selectedGame.completedAt).toLocaleString('zh-CN')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="对局结果">
                {selectedGame.result || selectedGame.winner || '进行中'}
              </Descriptions.Item>
              <Descriptions.Item label="步数">{selectedGame.moveCount || 0}</Descriptions.Item>
              <Descriptions.Item label="时长">
                {selectedGame.duration ? `${Math.floor(selectedGame.duration / 60)}分钟` : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="FEN" span={2}>
                <Text code>{selectedGame.fen || '暂无'}</Text>
              </Descriptions.Item>
            </Descriptions>

            <Divider />

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
                  <Text type="secondary" style={{ fontSize: '12px', float: 'right' }}>
                    {item.time}
                  </Text>
                </List.Item>
              )}
              style={{ maxHeight: '300px', overflowY: 'auto' }}
            />
          </div>
        )}
      </Modal>

      {/* 中止确认弹窗 */}
      <Modal
        title="中止对局"
        open={isAbortModalOpen}
        onOk={confirmAbort}
        onCancel={() => {
          setIsAbortModalOpen(false);
          setAbortReason('');
        }}
        okText="确定中止"
        cancelText="取消"
        okButtonProps={{ danger: true, loading: abortMutation.isPending }}
      >
        <Alert
          message="警告"
          description="中止后对局将立即结束，不可恢复。请谨慎操作。"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Input.TextArea
          placeholder="请输入中止原因（必填）"
          rows={4}
          value={abortReason}
          onChange={(e) => setAbortReason(e.target.value)}
          autoFocus
        />
      </Modal>

      {/* 游戏日志弹窗 */}
      <Modal
        title="对局日志"
        open={isLogModalOpen}
        onCancel={() => setIsLogModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setIsLogModalOpen(false)}>
            关闭
          </Button>,
          <Button
            key="export"
            icon={<ExportOutlined />}
            onClick={() => message.info('导出功能开发中')}
          >
            导出 CSV
          </Button>,
        ]}
        width={800}
      >
        {selectedGame && (
          <GameLogsViewer gameId={selectedGame.id} />
        )}
      </Modal>
    </div>
  );
};

// 游戏日志查看器组件
const GameLogsViewer: React.FC<{ gameId: string }> = ({ gameId }) => {
  const [logPage, setLogPage] = useState(1);
  const [logPageSize] = useState(20);

  const { data: logsData, isLoading } = useQuery({
    queryKey: ['game-logs', gameId, logPage],
    queryFn: () =>
      gamesApi.getGameLogs(gameId, { page: logPage, page_size: logPageSize }),
  });

  return (
    <div>
      {isLoading ? (
        <Text>加载中...</Text>
      ) : (
        <List
          dataSource={logsData?.data || []}
          renderItem={(log: GameLog) => (
            <List.Item>
              <List.Item.Meta
                title={
                  <Space>
                    <Text strong>{log.action_display}</Text>
                    <Tag color={
                      log.severity === 'critical' ? 'red' :
                      log.severity === 'error' ? 'orange' :
                      log.severity === 'warning' ? 'gold' : 'blue'
                    }>
                      {log.severity}
                    </Tag>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      <ClockCircleOutlined /> {new Date(log.created_at).toLocaleString('zh-CN')}
                    </Text>
                  </Space>
                }
                description={
                  <div>
                    <div><Text strong>操作者：</Text>{log.operator.username}</div>
                    {log.ip_address && (
                      <div><Text strong>IP：</Text>{log.ip_address}</div>
                    )}
                    {Object.keys(log.details).length > 0 && (
                      <div>
                        <Text strong>详情：</Text>
                        <Text code>{JSON.stringify(log.details)}</Text>
                      </div>
                    )}
                  </div>
                }
              />
            </List.Item>
          )}
          pagination={{
            current: logPage,
            pageSize: logPageSize,
            total: logsData?.total,
            onChange: setLogPage,
          }}
        />
      )}
    </div>
  );
};

export default GamesPage;
