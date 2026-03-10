import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, Row, Col, Button, Typography, Form, Input, Space, message, Alert, Divider } from 'antd';
import {
  LoginOutlined,
  ArrowLeftOutlined,
  EnterOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores';
import { friendService } from '@/services';
import type { FriendRoom } from '@/types';
import { RoomStatus } from '@/components/friend/RoomStatus';

const { Title, Text } = Typography;

/**
 * 加入房间页面
 * 
 * 功能：
 * - 输入房间号表单
 * - 加入房间按钮
 * - 支持 URL 参数直接加入（/friend/join?room=CHESS12345）
 */
const JoinRoomPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user } = useAuthStore();
  const [form] = Form.useForm();
  const [isJoining, setIsJoining] = useState(false);
  const [room, setRoom] = useState<FriendRoom | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 从 URL 参数获取房间号
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const roomCode = params.get('room');
    
    if (roomCode) {
      form.setFieldsValue({ room_code: roomCode });
      // 自动查询房间
      fetchRoom(roomCode);
    }
  }, [location.search, form]);

  // 查询房间详情
  const fetchRoom = async (roomCode: string) => {
    if (!roomCode || roomCode.length < 5) return;

    setIsJoining(true);
    setError(null);

    try {
      const result = await friendService.getRoom(roomCode);
      
      if (result.success && result.data) {
        setRoom(result.data);
        
        // 检查房间状态
        if (result.data.status === 'expired') {
          setError('房间已过期');
        } else if (result.data.status === 'playing' || result.data.status === 'finished') {
          setError('房间已有对局进行中');
        }
      } else {
        setError(result.error?.message || '房间不存在');
      }
    } catch (error: any) {
      console.error('查询房间失败:', error);
      setError(error.response?.status === 404 ? '房间不存在' : '查询失败');
    } finally {
      setIsJoining(false);
    }
  };

  // 加入房间
  const handleJoinRoom = async (values: any) => {
    if (!isAuthenticated || !user) {
      message.warning('请先登录');
      navigate('/login');
      return;
    }

    const roomCode = values.room_code.toUpperCase().trim();
    
    if (!roomCode || roomCode.length < 5) {
      message.error('请输入有效的房间号');
      return;
    }

    setIsJoining(true);
    setError(null);

    try {
      const result = await friendService.joinRoom(roomCode);
      
      if (result.success && result.data) {
        message.success('加入成功！');
        // 跳转到游戏页面
        navigate(`/games/friend/${result.data.game_id}/`);
      } else {
        setError(result.error?.message || '加入失败');
      }
    } catch (error: any) {
      console.error('加入房间失败:', error);
      setError(error.response?.status === 404 ? '房间不存在' : '加入失败');
    } finally {
      setIsJoining(false);
    }
  };

  // 处理表单提交
  const onFinish = (values: any) => {
    if (room && room.status === 'waiting') {
      handleJoinRoom({ room_code: values.room_code });
    } else {
      // 先查询房间
      fetchRoom(values.room_code);
    }
  };

  // 渲染加入表单
  const renderJoinForm = () => (
    <Card className="card-chinese max-w-md mx-auto">
      <div className="text-center py-6">
        <EnterOutlined className="text-6xl text-blue-600 mb-4" />
        <Title level={3} className="font-chinese mb-2">加入好友对战</Title>
        <Text className="text-gray-600 mb-8 block">
          输入房间号，加入好友的对局
        </Text>
      </div>

      {error && (
        <Alert
          message={error}
          type="error"
          showIcon
          icon={<ExclamationCircleOutlined />}
          className="mb-6"
        />
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Form.Item
          label="房间号"
          name="room_code"
          rules={[
            { required: true, message: '请输入房间号' },
            { min: 5, message: '房间号至少 5 位' },
            { pattern: /^[A-Z0-9]+$/i, message: '房间号只能包含字母和数字' },
          ]}
          extra="房间号格式：CHESS + 5 位字母数字"
        >
          <Input
            size="large"
            placeholder="例如：CHESS2A3B5"
            disabled={isJoining}
            onChange={(e) => {
              // 自动转换为大写
              e.target.value = e.target.value.toUpperCase();
            }}
          />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            block
            loading={isJoining}
            icon={<EnterOutlined />}
          >
            加入房间
          </Button>
        </Form.Item>
      </Form>

      <Divider />

      <Alert
        message="如何获取房间号？"
        description="请您的好友创建房间后，将房间号或邀请链接分享给您"
        type="info"
        showIcon
        className="mb-6"
      />

      <div className="text-center">
        <Space>
          <Button onClick={() => navigate('/games/friend/create/')}>
            <LoginOutlined /> 创建房间
          </Button>
          <Button onClick={() => navigate('/')}>
            <ArrowLeftOutlined /> 返回首页
          </Button>
        </Space>
      </div>
    </Card>
  );

  // 渲染房间信息（查询后）
  const renderRoomInfo = () => (
    <Row gutter={[24, 24]} justify="center">
      <Col xs={24} md={12} lg={8}>
        {room && (
          <RoomStatus
            room={room}
            onJoin={() => handleJoinRoom({ room_code: room.room_code })}
          />
        )}
      </Col>

      <Col xs={24} md={12} lg={8}>
        <Card className="card-chinese">
          <div className="text-center py-6">
            {room?.status === 'waiting' ? (
              <>
                <EnterOutlined className="text-6xl text-green-600 mb-4" />
                <Title level={4} className="mb-4">准备加入房间</Title>
                
                <Alert
                  message="房间信息"
                  description={
                    <div className="text-sm text-left">
                      <p className="mb-2">房主：{room.creator_username}</p>
                      <p className="mb-2">状态：等待中</p>
                      <p>点击"加入房间"开始对局</p>
                    </div>
                  }
                  type="success"
                  showIcon
                  className="mb-6"
                />

                <Button
                  type="primary"
                  size="large"
                  block
                  loading={isJoining}
                  icon={<EnterOutlined />}
                  onClick={() => handleJoinRoom({ room_code: room.room_code })}
                >
                  加入房间
                </Button>
              </>
            ) : (
              <>
                <ExclamationCircleOutlined className="text-6xl text-red-600 mb-4" />
                <Title level={4} className="mb-4">无法加入</Title>
                
                <Alert
                  message={error || '房间不可加入'}
                  type="error"
                  showIcon
                  className="mb-6"
                />

                <Button
                  size="large"
                  block
                  onClick={() => {
                    setRoom(null);
                    setError(null);
                    form.resetFields();
                  }}
                >
                  重新输入
                </Button>
              </>
            )}
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
            登录后才能加入好友对战
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
  if (room || error) {
    return renderRoomInfo();
  }

  return renderJoinForm();
};

export default JoinRoomPage;
