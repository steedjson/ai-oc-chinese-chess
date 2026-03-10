import React from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Form,
  Slider,
  InputNumber,
  Button,
  message,
  Switch,
  Divider,
  Space,
  Table,
  Tag,
  Badge,
  Tooltip,
} from 'antd';
import {
  SettingOutlined,
  DashboardOutlined,
  ThunderboltOutlined,
  InfoCircleOutlined,
  RocketOutlined,
  UndoOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiApi, type StockfishParams } from '../../api/ai';
import type { AiConfig } from '../../types';
import { useHasPermission } from '../../hooks/useHasPermission';

const { Title, Paragraph } = Typography;

const AIPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [engineForm] = Form.useForm<StockfishParams>();
  const [configForm] = Form.useForm<Partial<AiConfig>>();
  const { isSuperAdmin } = useHasPermission();

  // 获取 AI 配置
  const { data: config, isLoading: isConfigLoading } = useQuery({
    queryKey: ['ai-config'],
    queryFn: () => aiApi.getConfig(),
  });

  // 获取引擎参数
  const { data: engineParams, isLoading: isEngineLoading } = useQuery({
    queryKey: ['engine-params'],
    queryFn: () => aiApi.getEngineParams(),
  });

  // 表单数据同步
  React.useEffect(() => {
    if (config) {
      configForm.setFieldsValue(config);
    }
  }, [config, configForm]);

  React.useEffect(() => {
    if (engineParams) {
      engineForm.setFieldsValue(engineParams);
    }
  }, [engineParams, engineForm]);

  // 获取对局记录
  const { data: gameRecords, isLoading: isGamesLoading } = useQuery({
    queryKey: ['ai-games'],
    queryFn: () => aiApi.getGameRecords({ page: 1, pageSize: 10 }),
  });

  // 更新配置 Mutation
  const updateConfigMutation = useMutation({
    mutationFn: (data: Partial<AiConfig>) => aiApi.updateConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-config'] });
      message.success('通用配置已更新');
    },
    onError: () => message.error('配置更新失败'),
  });

  // 更新引擎参数 Mutation
  const updateEngineMutation = useMutation({
    mutationFn: (data: Partial<StockfishParams>) => aiApi.updateEngineParams(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['engine-params'] });
      message.success('引擎参数已同步');
    },
    onError: () => message.error('引擎参数更新失败'),
  });

  const columns = [
    {
      title: '玩家',
      dataIndex: 'playerId',
      key: 'playerId',
      render: (id: string) => <a>{id.slice(0, 8)}</a>,
    },
    {
      title: 'AI 难度',
      dataIndex: 'aiDifficulty',
      key: 'aiDifficulty',
      render: (lv: number) => <Tag color="blue">LV.{lv}</Tag>,
    },
    {
      title: '胜负',
      dataIndex: 'winner',
      key: 'winner',
      render: (winner: string) => {
        const config: Record<string, { color: string; text: string }> = {
          player: { color: 'success', text: '玩家胜' },
          ai: { color: 'error', text: 'AI 胜' },
          draw: { color: 'default', text: '和局' },
        };
        const item = config[winner] || config.draw;
        return <Badge status={item.color as any} text={item.text} />;
      },
    },
    {
      title: '步数',
      dataIndex: 'moveCount',
      key: 'moveCount',
    },
    {
      title: '时长',
      dataIndex: 'duration',
      key: 'duration',
      render: (s: number) => `${Math.floor(s / 60)}分${s % 60}秒`,
    },
    {
      title: '对局时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: string) => new Date(date).toLocaleString(),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>AI 引擎管理</Title>
        <Space>
          <Tooltip title={!isSuperAdmin ? "权限不足" : "重置所有参数为出厂默认值"}>
            <Button icon={<UndoOutlined />} disabled={!isSuperAdmin}>重置默认</Button>
          </Tooltip>
          <Tooltip title={!isSuperAdmin ? "权限不足" : ""}>
            <Button 
              type="primary" 
              icon={<RocketOutlined />} 
              onClick={() => {
                configForm.submit();
                engineForm.submit();
              }}
              disabled={!isSuperAdmin}
            >
              发布配置
            </Button>
          </Tooltip>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* 通用服务配置 */}
        <Col xs={24} lg={8}>
          <Card 
            title={<span><SettingOutlined /> 通用配置</span>} 
            bordered={false}
            loading={isConfigLoading}
          >
            <Form
              form={configForm}
              layout="vertical"
              onFinish={(values) => updateConfigMutation.mutate(values)}
            >
              <Form.Item name="enabled" label="服务状态" valuePropName="checked">
                <Switch checkedChildren="运行中" unCheckedChildren="已停止" />
              </Form.Item>
              <Form.Item name="difficulty" label="默认全局难度系数">
                <Slider min={1} max={20} marks={{ 1: '1', 10: '中等', 20: '大师' }} />
              </Form.Item>
              <Form.Item name="eloBase" label="基准 Elo 分数">
                <InputNumber style={{ width: '100%' }} min={800} max={3500} />
              </Form.Item>
              <Paragraph type="secondary" style={{ fontSize: 12 }}>
                * 基础配置决定了 AI 服务是否对全量玩家可用，以及匹配逻辑的基准参考。
              </Paragraph>
            </Form>
          </Card>
        </Col>

        {/* Stockfish 引擎微调 */}
        <Col xs={24} lg={16}>
          <Card 
            title={<span><DashboardOutlined /> Stockfish 引擎参数 (v16.1)</span>} 
            bordered={false}
            loading={isEngineLoading}
            extra={<Tooltip title="这些参数直接影响底层 WASM 引擎的性能表现"><InfoCircleOutlined /></Tooltip>}
          >
            <Form
              form={engineForm}
              layout="horizontal"
              labelCol={{ span: 6 }}
              wrapperCol={{ span: 16 }}
              onFinish={(values) => updateEngineMutation.mutate(values)}
            >
              <Form.Item 
                name="threads" 
                label="计算线程 (Threads)"
                tooltip="最大并发线程数，建议设为逻辑核心数的 75%"
              >
                <InputNumber min={1} max={16} />
              </Form.Item>
              <Form.Item 
                name="hashSize" 
                label="哈希表大小 (Hash)"
                tooltip="单位: MB。更大的哈希表能提高长局对弈的搜索速度"
              >
                <Slider min={16} max={2048} step={16} marks={{ 16: '16M', 512: '512M', 2048: '2G' }} />
              </Form.Item>
              <Form.Item 
                name="skillLevel" 
                label="技巧水平 (Skill Level)"
                tooltip="Stockfish 内置的技巧参数 (0-20)"
              >
                <Slider min={0} max={20} />
              </Form.Item>
              <Form.Item 
                name="multiPV" 
                label="并行线路 (MultiPV)"
                tooltip="同时分析的最佳走法数量"
              >
                <InputNumber min={1} max={5} />
              </Form.Item>
              <Divider />
              <div style={{ textAlign: 'right' }}>
                <Tooltip title={!isSuperAdmin ? "权限不足" : ""}>
                  <Button 
                    type="dashed" 
                    icon={<ThunderboltOutlined />} 
                    onClick={() => engineForm.submit()}
                    disabled={!isSuperAdmin}
                  >
                    应用引擎参数
                  </Button>
                </Tooltip>
              </div>
            </Form>
          </Card>
        </Col>

        {/* 性能统计 & 记录 */}
        <Col xs={24}>
          <Card 
            title={<span><HistoryOutlined /> AI 对局流水</span>} 
            bordered={false}
            styles={{ body: { padding: 0 } }}
          >
            <Table
              columns={columns}
              dataSource={gameRecords?.data}
              loading={isGamesLoading}
              rowKey="id"
              scroll={{ x: 'max-content' }}
              pagination={{ pageSize: 5 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AIPage;
