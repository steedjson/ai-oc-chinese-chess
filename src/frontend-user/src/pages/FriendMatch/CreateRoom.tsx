import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Button, Typography, Form, InputNumber, Switch, Space, message, Alert, Divider } from 'antd';
import {
  PlusCircleOutlined,
  ArrowLeftOutlined,
  ShareAltOutlined,
  CopyOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores';
import { friendService } from '@/services';
import type { FriendRoom } from '@/types';
import { copyToClipboard, generateShareText } from '@/utils/share';
import { RoomStatus } from '@/components/friend/RoomStatus';

const { Title, Text } = Typography;

/**
 * 创建房间页面
 * 
 * 功能：
 * - 房间配置表单（时间控制、是否计分）
 * - 创建房间按钮
 * - 生成房间号和邀请链接
 * - 显示房间二维码（可选）
 */
const CreateRoomPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuthStore();
  const [form] = Form.useForm();
  const [isCreating, setIsCreating] = useState(false);
  const [createdRoom, setCreatedRoom] = useState<FriendRoom | null>(null);

  // 创建房间
  const handleCreateRoom = async (values: any) => {
    if (!isAuthenticated || !user) {
      message.warning('请先登录');
      navigate('/login');
      return;
    }

    setIsCreating(true);

    try {
      const result = await friendService.createRoom({
        time_control: values.time_control || 600,
        is_rated: values.is_rated || false,
      });

      if (result.success && result.data) {
        setCreatedRoom(result.data);
        message.success('房间创建成功！');
        
        // 自动复制邀请链接
        const shareText = generateShareText(result.data.room_code, result.data.invite_link);
        await copyToClipboard(shareText);
        message.success('邀请信息已复制到剪贴板');
      } else {
        message.error(result.error?.message || '创建房间失败');
      }
    } catch (error) {
      console.error('创建房间失败:', error);
      message.error('创建房间失败，请稍后重试');
    } finally {
      setIsCreating(false);
    }
  };

  // 处理分享
  const handleShare = async () => {
    if (!createdRoom) return;
    
    const shareText = generateShareText(createdRoom.room_code, createdRoom.invite_link);
    const success = await copyToClipboard(shareText);
    
    if (success) {
      message.success('分享信息已复制，可以发送给好友了');
    } else {
      message.error('复制失败');
    }
  };

  // 处理复制链接
  const handleCopyLink = async () => {
    if (!createdRoom) return;
    
    const success = await copyToClipboard(createdRoom.invite_link);
    
    if (success) {
      message.success('链接已复制');
    } else {
      message.error('复制失败');
    }
  };

  // 开始游戏（房主等待好友加入）
  const handleStartGame = () => {
    if (createdRoom) {
      navigate(`/games/friend/${createdRoom.game_id}/`);
    }
  };

  // 渲染创建表单
  const renderCreateForm = () => (
    <Card className="card-chinese max-w-md mx-auto">
      <div className="text-center py-6">
        <PlusCircleOutlined className="text-6xl text-blue-600 mb-4" />
        <Title level={3} className="font-chinese mb-2">创建好友对战</Title>
        <Text className="text-gray-600 mb-8 block">
          创建房间，邀请好友来一局
        </Text>
      </div>

      <Divider />

      <Form
        form={form}
        layout="vertical"
        onFinish={handleCreateRoom}
        initialValues={{
          time_control: 600, // 默认 10 分钟
          is_rated: false,
        }}
      >
        <Form.Item
          label="时间控制（秒）"
          name="time_control"
          rules={[
            { required: true, message: '请输入时间控制' },
            { type: 'number', min: 60, max: 7200, message: '时间范围：60-7200 秒' },
          ]}
          extra="每方基本用时，建议 600 秒（10 分钟）"
        >
          <InputNumber
            min={60}
            max={7200}
            step={60}
            className="w-full"
            addonAfter="秒"
            disabled={isCreating}
          />
        </Form.Item>

        <Form.Item
          label="计分模式"
          name="is_rated"
          valuePropName="checked"
          extra="计分对局会影响双方等级分"
        >
          <Switch disabled={isCreating} />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            block
            loading={isCreating}
            icon={<PlusCircleOutlined />}
          >
            创建房间
          </Button>
        </Form.Item>
      </Form>

      <Divider />

      <div className="text-center">
        <Button onClick={() => navigate('/')}>
          <ArrowLeftOutlined /> 返回首页
        </Button>
      </div>
    </Card>
  );

  // 渲染创建成功后的房间信息
  const renderRoomInfo = () => (
    <Row gutter={[24, 24]} justify="center">
      <Col xs={24} md={12} lg={8}>
        {createdRoom && (
          <RoomStatus
            room={createdRoom}
            onShare={handleShare}
            onStartGame={handleStartGame}
          />
        )}
      </Col>

      <Col xs={24} md={12} lg={8}>
        <Card className="card-chinese">
          <div className="text-center py-6">
            <CheckCircleOutlined className="text-6xl text-green-600 mb-4" />
            <Title level={4} className="mb-4">房间创建成功！</Title>
            
            <Alert
              message="邀请好友加入"
              description={
                <div className="text-sm text-left">
                  <p className="mb-2">1. 复制房间号或邀请链接</p>
                  <p className="mb-2">2. 发送给您的好友</p>
                  <p className="mb-2">3. 好友加入后自动开始对局</p>
                  <p>房间 24 小时后过期</p>
                </div>
              }
              type="success"
              showIcon
              className="mb-6"
            />

            <Space direction="vertical" size="small" className="w-full">
              <Button
                type="primary"
                size="large"
                block
                icon={<ShareAltOutlined />}
                onClick={handleShare}
              >
                分享邀请
              </Button>
              
              <Button
                size="large"
                block
                icon={<CopyOutlined />}
                onClick={handleCopyLink}
              >
                复制链接
              </Button>

              <Button
                size="large"
                block
                onClick={() => setCreatedRoom(null)}
              >
                创建新房间
              </Button>
            </Space>
          </div>
        </Card>
      </Col>
    </Row>
  );

  // 检查登录状态
  if (!isAuthenticated) {
    return (
      <Card className="card-chinese max-w-md mx-auto">
        <div className="text-center py-8">
          <Title level={4}>请先登录</Title>
          <Text className="text-gray-600 mb-6 block">
            登录后才能创建好友对战房间
          </Text>
          <Space>
            <Button onClick={() => navigate('/login')}>去登录</Button>
            <Button onClick={() => navigate('/')}>返回首页</Button>
          </Space>
        </div>
      </Card>
    );
  }

  // 根据状态渲染
  if (createdRoom) {
    return renderRoomInfo();
  }

  return renderCreateForm();
};

export default CreateRoomPage;
