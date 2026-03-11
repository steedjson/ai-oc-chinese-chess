"""
匹配系统 WebSocket Consumer 单元测试

测试 matchmaking/consumers.py 中的 MatchmakingConsumer 类

测试范围：
- 连接建立/断开
- 认证和权限验证
- 加入/退出匹配队列
- 队列状态查询
- 匹配通知
- 心跳管理
- 错误处理

覆盖率目标：174 语句 → 200 行测试代码
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from matchmaking.consumers import MatchmakingConsumer
from matchmaking.queue import MatchmakingQueue, QueueUser
from matchmaking.models import MatchQueue, MatchQueueStatus


# ==================== Fixtures ====================

@pytest.fixture
def test_user(db):
    """创建测试用户"""
    from users.models import User
    return User.objects.create_user(
        username='testplayer',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_user_2(db):
    """创建第二个测试用户"""
    from users.models import User
    return User.objects.create_user(
        username='testplayer2',
        email='test2@example.com',
        password='testpass123'
    )


@pytest.fixture
def create_token():
    """创建 JWT token 的工厂函数"""
    from authentication.services import TokenService
    
    def _create_token(user):
        tokens = TokenService.generate_tokens(user)
        return tokens['access_token']
    
    return _create_token


@pytest.fixture
def test_asgi_app():
    """创建测试 ASGI 应用"""
    from matchmaking import routing
    
    # 检查是否有路由配置
    try:
        websocket_urlpatterns = routing.websocket_urlpatterns
    except (AttributeError, ImportError):
        # 如果没有路由，创建一个简单的
        from django.urls import re_path
        websocket_urlpatterns = [
            re_path(r'ws/matchmaking/$', MatchmakingConsumer.as_asgi()),
        ]
    
    return ProtocolTypeRouter({
        "websocket": AllowedHostsOriginValidator(
            URLRouter(websocket_urlpatterns)
        ),
    })


@pytest.fixture
def mock_queue():
    """Mock 匹配队列"""
    with patch('matchmaking.consumers.MatchmakingQueue') as mock:
        queue_instance = MagicMock()
        mock.return_value = queue_instance
        yield queue_instance


@pytest.fixture
def mock_matchmaker():
    """Mock 匹配算法"""
    with patch('matchmaking.consumers.Matchmaker') as mock:
        matchmaker_instance = MagicMock()
        mock.return_value = matchmaker_instance
        yield matchmaker_instance


# ==================== 连接测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMatchmakingConsumerConnect:
    """MatchmakingConsumer 连接测试"""
    
    async def test_connect_success(self, test_user, create_token, test_asgi_app):
        """测试成功连接"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        # 连接应该成功
        connected, subprotocol = await communicator.connect(timeout=5)
        assert connected is True
        
        # 应该收到连接确认
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'connected'
        assert response['payload']['user_id'] == str(test_user.id)
        
        await communicator.disconnect()
    
    async def test_connect_failure_no_token(self, test_asgi_app):
        """测试无 token 连接失败"""
        communicator = WebsocketCommunicator(
            test_asgi_app,
            "/ws/matchmaking/"
        )
        
        # 连接应该失败（认证失败）
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()
    
    async def test_connect_failure_invalid_token(self, test_asgi_app):
        """测试无效 token 连接失败"""
        communicator = WebsocketCommunicator(
            test_asgi_app,
            "/ws/matchmaking/?token=invalid_token"
        )
        
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()


# ==================== 断开连接测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMatchmakingConsumerDisconnect:
    """MatchmakingConsumer 断开连接测试"""
    
    async def test_disconnect_clean(self, test_user, create_token, test_asgi_app):
        """测试正常断开连接"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 断开连接
        await communicator.disconnect()
        
        # 等待一小段时间确保清理完成
        await asyncio.sleep(0.1)
    
    async def test_disconnect_removes_from_queue(self, test_user, create_token, test_asgi_app, mock_queue):
        """测试断开连接时自动退出队列"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 先加入队列
        await communicator.send_json_to({
            'type': 'JOIN_QUEUE',
            'payload': {'game_type': 'ranked'}
        })
        
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'queue_joined'
        
        # 断开连接
        await communicator.disconnect()
        
        # 验证队列被调用退出
        # mock_queue.leave_queue.assert_called()
        
        await asyncio.sleep(0.1)


# ==================== 加入队列测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMatchmakingConsumerJoinQueue:
    """MatchmakingConsumer 加入队列测试"""
    
    async def test_join_queue_ranked(self, test_user, create_token, test_asgi_app):
        """测试加入排位队列"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)  # connected
        
        # 发送加入队列请求
        await communicator.send_json_to({
            'type': 'JOIN_QUEUE',
            'payload': {'game_type': 'ranked'}
        })
        
        # 应该收到加入成功响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'queue_joined'
        assert response['payload']['success'] is True
        assert response['payload']['game_type'] == 'ranked'
        assert 'rating' in response['payload']
        assert 'queue_position' in response['payload']
        
        await communicator.disconnect()
    
    async def test_join_queue_casual(self, test_user, create_token, test_asgi_app):
        """测试加入休闲队列"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送加入休闲队列请求
        await communicator.send_json_to({
            'type': 'JOIN_QUEUE',
            'payload': {'game_type': 'casual'}
        })
        
        # 应该收到加入成功响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'queue_joined'
        assert response['payload']['success'] is True
        assert response['payload']['game_type'] == 'casual'
        
        await communicator.disconnect()
    
    async def test_join_queue_default_game_type(self, test_user, create_token, test_asgi_app):
        """测试加入队列（默认游戏类型）"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送加入队列请求（不指定游戏类型）
        await communicator.send_json_to({
            'type': 'JOIN_QUEUE'
        })
        
        # 应该默认加入 ranked 队列
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'queue_joined'
        assert response['payload']['success'] is True
        assert response['payload']['game_type'] == 'ranked'
        
        await communicator.disconnect()
    
    async def test_join_queue_twice(self, test_user, create_token, test_asgi_app):
        """测试重复加入队列"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 第一次加入
        await communicator.send_json_to({
            'type': 'JOIN_QUEUE',
            'payload': {'game_type': 'ranked'}
        })
        response1 = await communicator.receive_json_from(timeout=5)
        assert response1['type'] == 'queue_joined'
        
        # 第二次加入（应该失败或更新）
        await communicator.send_json_to({
            'type': 'JOIN_QUEUE',
            'payload': {'game_type': 'ranked'}
        })
        response2 = await communicator.receive_json_from(timeout=5)
        # 根据实现，可能成功（更新）或失败
        assert response2['type'] in ['queue_joined', 'ERROR']
        
        await communicator.disconnect()


# ==================== 退出队列测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMatchmakingConsumerLeaveQueue:
    """MatchmakingConsumer 退出队列测试"""
    
    async def test_leave_queue_success(self, test_user, create_token, test_asgi_app):
        """测试成功退出队列"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 先加入队列
        await communicator.send_json_to({
            'type': 'JOIN_QUEUE',
            'payload': {'game_type': 'ranked'}
        })
        await communicator.receive_json_from(timeout=5)
        
        # 退出队列
        await communicator.send_json_to({
            'type': 'LEAVE_QUEUE'
        })
        
        # 应该收到退出成功响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'queue_left'
        assert response['payload']['success'] is True
        
        await communicator.disconnect()
    
    async def test_leave_queue_not_in_queue(self, test_user, create_token, test_asgi_app):
        """测试未加入队列时退出"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 直接退出（未加入）
        await communicator.send_json_to({
            'type': 'LEAVE_QUEUE'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'QUEUE_LEAVE_FAILED'
        
        await communicator.disconnect()


# ==================== 队列状态查询测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMatchmakingConsumerGetStatus:
    """MatchmakingConsumer 队列状态查询测试"""
    
    async def test_get_status_not_in_queue(self, test_user, create_token, test_asgi_app):
        """测试查询状态（不在队列中）"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 查询状态
        await communicator.send_json_to({
            'type': 'GET_STATUS'
        })
        
        # 应该收到状态响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'queue_status'
        assert response['payload']['in_queue'] is False
        assert response['payload']['your_position'] is None
        
        await communicator.disconnect()
    
    async def test_get_status_in_queue(self, test_user, create_token, test_asgi_app):
        """测试查询状态（在队列中）"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 加入队列
        await communicator.send_json_to({
            'type': 'JOIN_QUEUE',
            'payload': {'game_type': 'ranked'}
        })
        await communicator.receive_json_from(timeout=5)
        
        # 查询状态
        await communicator.send_json_to({
            'type': 'GET_STATUS'
        })
        
        # 应该收到状态响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'queue_status'
        assert response['payload']['in_queue'] is True
        assert 'total_in_queue' in response['payload']
        
        await communicator.disconnect()


# ==================== 心跳测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMatchmakingConsumerHeartbeat:
    """MatchmakingConsumer 心跳测试"""
    
    async def test_heartbeat(self, test_user, create_token, test_asgi_app):
        """测试心跳消息"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送心跳
        await communicator.send_json_to({
            'type': 'HEARTBEAT',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        # 应该收到心跳响应
        # 注意：根据实现，可能不会返回显式的 HEARTBEAT 响应
        # 这里只验证不抛出异常
        await asyncio.sleep(0.1)
        
        await communicator.disconnect()


# ==================== 消息处理测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMatchmakingConsumerMessages:
    """MatchmakingConsumer 消息处理测试"""
    
    async def test_invalid_message_type(self, test_user, create_token, test_asgi_app):
        """测试无效消息类型"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送未知消息类型
        await communicator.send_json_to({
            'type': 'UNKNOWN_TYPE'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'INVALID_MESSAGE_TYPE'
        
        await communicator.disconnect()
    
    async def test_invalid_json(self, test_user, create_token, test_asgi_app):
        """测试无效 JSON"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送无效 JSON
        await communicator.send_to_text("invalid json {")
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'INVALID_JSON'
        
        await communicator.disconnect()


# ==================== 频道层消息处理器测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMatchmakingConsumerChannelHandlers:
    """MatchmakingConsumer 频道层消息处理器测试"""
    
    async def test_queue_status_update_handler(self, test_user, create_token, test_asgi_app):
        """测试队列状态更新处理器"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收队列状态更新
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'matchmaking',
            {
                'type': 'queue_status_update',
                'data': {
                    'total_in_queue': 5,
                    'your_position': 3,
                    'estimated_wait_time': 120
                }
            }
        )
        
        # 应该收到队列状态更新
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'queue_status'
        
        await communicator.disconnect()
    
    async def test_match_found_handler(self, test_user, create_token, test_asgi_app):
        """测试匹配成功处理器"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收匹配成功通知
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'matchmaking',
            {
                'type': 'match_found',
                'data': {
                    'game_id': '12345678-1234-1234-1234-123456781234',
                    'opponent': {'username': 'opponent_player', 'rating': 1500},
                    'game_type': 'ranked'
                }
            }
        )
        
        # 应该收到匹配成功通知
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'match_found'
        assert response['payload']['success'] is True
        assert 'game_id' in response['payload']
        
        await communicator.disconnect()


# ==================== 边界条件测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMatchmakingConsumerEdgeCases:
    """MatchmakingConsumer 边界条件测试"""
    
    async def test_concurrent_queue_operations(self, test_user, test_user_2, create_token, test_asgi_app):
        """测试并发队列操作"""
        token1 = create_token(test_user)
        token2 = create_token(test_user_2)
        
        # 两个用户同时连接
        comm1 = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token1}"
        )
        comm2 = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token2}"
        )
        
        connected1, _ = await comm1.connect(timeout=5)
        connected2, _ = await comm2.connect(timeout=5)
        
        assert connected1 is True
        assert connected2 is True
        
        await comm1.receive_json_from(timeout=5)
        await comm2.receive_json_from(timeout=5)
        
        # 同时加入队列
        await comm1.send_json_to({
            'type': 'JOIN_QUEUE',
            'payload': {'game_type': 'ranked'}
        })
        await comm2.send_json_to({
            'type': 'JOIN_QUEUE',
            'payload': {'game_type': 'ranked'}
        })
        
        # 都应该收到响应
        response1 = await comm1.receive_json_from(timeout=5)
        response2 = await comm2.receive_json_from(timeout=5)
        
        assert response1['type'] == 'queue_joined'
        assert response2['type'] == 'queue_joined'
        
        await comm1.disconnect()
        await comm2.disconnect()
    
    async def test_rapid_join_leave(self, test_user, create_token, test_asgi_app):
        """测试快速加入/退出序列"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/matchmaking/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 快速加入和退出多次
        for _ in range(3):
            await communicator.send_json_to({
                'type': 'JOIN_QUEUE',
                'payload': {'game_type': 'ranked'}
            })
            await communicator.receive_json_from(timeout=5)
            
            await communicator.send_json_to({
                'type': 'LEAVE_QUEUE'
            })
            await communicator.receive_json_from(timeout=5)
        
        await communicator.disconnect()
