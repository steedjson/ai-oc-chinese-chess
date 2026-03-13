"""
AI 对弈 WebSocket Consumer 单元测试

测试 ai_engine/consumers.py 中的 AIGameConsumer 类

测试范围：
- 连接建立/断开
- 认证和权限验证
- AI 走棋请求
- AI 提示请求
- AI 分析请求
- 心跳管理
- 通知接收

覆盖率目标：74 语句 → 100 行测试代码
"""
import pytest
import json
import asyncio
from datetime import datetime
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from ai_engine.consumers import AIGameConsumer


# ==================== Fixtures ====================

@pytest.fixture
def test_user(db):
    """创建测试用户"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='aiplayer',
        email='ai@example.com',
        password='testpass123'
    )


@pytest.fixture
def ai_game(test_user, db):
    """创建 AI 对局"""
    from ai_engine.models import AIGame
    from uuid import uuid4
    
    game = AIGame.objects.create(
        id=uuid4(),
        player=test_user,
        ai_level=5,
        ai_side='black',
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        move_history=[],
        status='playing',
        winner=None
    )
    return game


@pytest.fixture
def create_token():
    """创建 JWT token"""
    from authentication.services import TokenService
    
    def _create_token(user):
        tokens = TokenService.generate_tokens(user)
        return tokens['access_token']
    
    return _create_token


@pytest.fixture
def test_asgi_app():
    """创建测试 ASGI 应用"""
    from django.urls import re_path
    
    websocket_urlpatterns = [
        re_path(r'ws/ai_game/(?P<game_id>[^/]+)/$', AIGameConsumer.as_asgi()),
    ]
    
    return ProtocolTypeRouter({
        "websocket": AllowedHostsOriginValidator(
            URLRouter(websocket_urlpatterns)
        ),
    })


# ==================== 连接测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestAIGameConsumerConnect:
    """AIGameConsumer 连接测试"""
    
    async def test_connect_success(self, ai_game, test_user, create_token, test_asgi_app):
        """测试成功连接"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{str(ai_game.id)}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=10)
        
        # 检查连接响应（可能因为认证失败而关闭）
        if connected:
            try:
                response = await communicator.receive_json_from(timeout=5)
                assert response['type'] == 'connected'
            except Exception:
                # 如果超时，说明连接建立但没有收到消息
                pass
        
        await communicator.disconnect()
        assert response['data']['game_id'] == str(ai_game.id)
        
        await communicator.disconnect()
    
    async def test_connect_failure_no_token(self, ai_game, test_asgi_app):
        """测试无 token 连接失败"""
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/"
        )
        
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()
    
    async def test_connect_failure_invalid_token(self, ai_game, test_asgi_app):
        """测试无效 token 连接失败"""
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token=invalid"
        )
        
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()
    
    async def test_connect_failure_wrong_user(self, ai_game, db, create_token):
        """测试非游戏所有者连接失败"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otherplayer',
            email='other@example.com',
            password='testpass123'
        )
        
        token = create_token(other_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        # 非游戏所有者应该被拒绝
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()


# ==================== 断开连接测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestAIGameConsumerDisconnect:
    """AIGameConsumer 断开连接测试"""
    
    async def test_disconnect_clean(self, ai_game, test_user, create_token, test_asgi_app):
        """测试正常断开连接"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        await communicator.disconnect()
        await asyncio.sleep(0.1)


# ==================== 消息处理测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestAIGameConsumerMessages:
    """AIGameConsumer 消息处理测试"""
    
    async def test_request_move(self, ai_game, test_user, create_token, test_asgi_app):
        """测试请求 AI 走棋"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送请求 AI 走棋
        await communicator.send_json_to({
            'type': 'request_move',
            'fen': 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
        })
        
        # 应该收到处理中响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'move_requested'
        assert response['data']['status'] == 'processing'
        
        await communicator.disconnect()
    
    async def test_request_hint(self, ai_game, test_user, create_token, test_asgi_app):
        """测试请求 AI 提示"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送请求 AI 提示
        await communicator.send_json_to({
            'type': 'request_hint',
            'fen': 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
        })
        
        # 应该收到处理中响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'hint_requested'
        assert response['data']['status'] == 'processing'
        
        await communicator.disconnect()
    
    async def test_request_analysis(self, ai_game, test_user, create_token, test_asgi_app):
        """测试请求 AI 分析"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送请求 AI 分析
        await communicator.send_json_to({
            'type': 'request_analysis',
            'fen': 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
        })
        
        # 应该收到处理中响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'analysis_requested'
        assert response['data']['status'] == 'processing'
        
        await communicator.disconnect()
    
    async def test_heartbeat(self, ai_game, test_user, create_token, test_asgi_app):
        """测试心跳消息"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送心跳
        await communicator.send_json_to({
            'type': 'heartbeat',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        # 应该收到心跳确认
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'heartbeat_ack'
        
        await communicator.disconnect()
    
    async def test_invalid_json(self, ai_game, test_user, create_token, test_asgi_app):
        """测试无效 JSON"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送无效 JSON
        await communicator.send_to_text("invalid json {")
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'error'
        assert response['data']['code'] == 'INVALID_JSON'
        
        await communicator.disconnect()


# ==================== 频道层消息处理器测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestAIGameConsumerChannelHandlers:
    """AIGameConsumer 频道层消息处理器测试"""
    
    async def test_ai_thinking_handler(self, ai_game, test_user, create_token, test_asgi_app):
        """测试 AI 思考中处理器"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收 AI 思考中通知
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'ai_game_{ai_game.id}',
            {
                'type': 'ai_thinking',
                'data': {
                    'depth': 5,
                    'eval': 0.5,
                    'pv': ['c2', 'e2']
                }
            }
        )
        
        # 应该收到 AI 思考中通知
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ai_thinking'
        assert response['data']['depth'] == 5
        
        await communicator.disconnect()
    
    async def test_ai_move_handler(self, ai_game, test_user, create_token, test_asgi_app):
        """测试 AI 走棋完成处理器"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收 AI 走棋完成通知
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'ai_game_{ai_game.id}',
            {
                'type': 'ai_move',
                'data': {
                    'from': 'c7',
                    'to': 'e7',
                    'piece': 'c',
                    'fen': 'new_fen'
                }
            }
        )
        
        # 应该收到 AI 走棋通知
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ai_move'
        assert response['data']['from'] == 'c7'
        
        await communicator.disconnect()
    
    async def test_ai_hint_handler(self, ai_game, test_user, create_token, test_asgi_app):
        """测试 AI 提示处理器"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收 AI 提示
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'ai_game_{ai_game.id}',
            {
                'type': 'ai_hint',
                'data': {
                    'best_move': {'from': 'c2', 'to': 'e2'},
                    'eval': 0.3
                }
            }
        )
        
        # 应该收到 AI 提示
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ai_hint'
        assert response['data']['best_move']['from'] == 'c2'
        
        await communicator.disconnect()
    
    async def test_ai_analysis_handler(self, ai_game, test_user, create_token, test_asgi_app):
        """测试 AI 分析处理器"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收 AI 分析
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'ai_game_{ai_game.id}',
            {
                'type': 'ai_analysis',
                'data': {
                    'eval': 0.5,
                    'depth': 10,
                    'analysis': 'Position is slightly better for red'
                }
            }
        )
        
        # 应该收到 AI 分析
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ai_analysis'
        assert response['data']['eval'] == 0.5
        
        await communicator.disconnect()
    
    async def test_ai_error_handler(self, ai_game, test_user, create_token, test_asgi_app):
        """测试 AI 错误处理器"""
        token = create_token(test_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{ai_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收 AI 错误
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'ai_game_{ai_game.id}',
            {
                'type': 'ai_error',
                'data': {
                    'code': 'ENGINE_ERROR',
                    'message': 'AI engine failed to start'
                }
            }
        )
        
        # 应该收到 AI 错误
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ai_error'
        assert response['data']['code'] == 'ENGINE_ERROR'
        
        await communicator.disconnect()


# ==================== 边界条件测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestAIGameConsumerEdgeCases:
    """AIGameConsumer 边界条件测试"""
    
    async def test_game_not_found(self, test_user, create_token, test_asgi_app):
        """测试游戏不存在"""
        token = create_token(test_user)
        fake_game_id = '00000000-0000-0000-0000-000000000000'
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/ai_game/{fake_game_id}/?token={token}"
        )
        
        # 游戏不存在应该拒绝连接
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()
