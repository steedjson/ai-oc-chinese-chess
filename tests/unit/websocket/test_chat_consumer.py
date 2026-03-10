"""
聊天 WebSocket Consumer 完整单元测试

测试 games/chat_consumer.py 中的 ChatConsumer 类

测试范围：
- 消息发送/接收
- 房间管理
- 消息历史
- 认证和权限验证
- 限流控制
- 错误处理
- 表情消息
- 系统消息
"""
import pytest
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.db import database_sync_to_async
from django.utils import timezone

from games.chat_consumer import ChatConsumer
from games.models import Game, GameStatus
from games.chat import ChatMessage, ChatMessageManager, MessageType
from games.spectator import Spectator, SpectatorStatus
from users.models import User
from authentication.services import TokenService


# ==================== 测试 Fixtures ====================

@pytest.fixture
def test_user(db):
    """创建测试用户（红方）"""
    return User.objects.create_user(
        username='chat_test_user',
        email='chat_test@example.com',
        password='SecurePass123'
    )


@pytest.fixture
def test_user2(db):
    """创建第二个测试用户（黑方）"""
    return User.objects.create_user(
        username='chat_test_user2',
        email='chat_test2@example.com',
        password='SecurePass123'
    )


@pytest.fixture
def spectator_user(db, game):
    """创建观战用户"""
    user = User.objects.create_user(
        username='chat_spectator',
        email='chat_spectator@example.com',
        password='SecurePass123'
    )
    
    Spectator.objects.create(
        game=game,
        user=user,
        status=SpectatorStatus.WATCHING
    )
    
    return user


@pytest.fixture
def game(db, test_user, test_user2):
    """创建测试游戏"""
    return Game.objects.create(
        game_type='online',
        status=GameStatus.PLAYING,
        red_player=test_user,
        black_player=test_user2,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        turn='w'
    )


@pytest.fixture
def finished_game(db, test_user, test_user2):
    """创建已结束的游戏"""
    return Game.objects.create(
        game_type='online',
        status=GameStatus.RED_WIN,
        red_player=test_user,
        black_player=test_user2,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        winner='red'
    )


@pytest.fixture
def create_token():
    """创建 JWT token 工厂函数"""
    def _create_token(user):
        tokens = TokenService.generate_tokens(user)
        return tokens['access_token']
    return _create_token


@pytest.fixture
def create_expired_token():
    """创建过期 JWT token 工厂函数"""
    def _create_expired_token(user):
        from authentication.services import TokenService
        import jwt
        from django.conf import settings
        
        # 创建已过期的 token
        payload = {
            'user_id': str(user.id),
            'username': user.username,
            'exp': datetime.utcnow() - timedelta(hours=1),  # 1 小时前过期
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return token
    return _create_expired_token


@pytest.fixture
def chat_consumer_instance():
    """创建 ChatConsumer 实例（用于单元测试）"""
    consumer = ChatConsumer()
    return consumer


# ==================== 连接测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerConnection:
    """ChatConsumer 连接测试"""
    
    async def test_connect_to_game_chat_success(self, game, test_user, create_token):
        """测试成功连接到对局聊天"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        
        assert connected is True
        
        # 收到欢迎消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'WELCOME'
        assert response['payload']['room_type'] == 'game'
        assert response['payload']['game_id'] == str(game.id)
        
        # 收到历史消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_HISTORY'
        
        await communicator.disconnect()
    
    async def test_connect_to_spectator_chat_success(self, game, spectator_user, create_token):
        """测试成功连接到观战聊天"""
        token = create_token(spectator_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/spectator/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        
        assert connected is True
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'WELCOME'
        assert response['payload']['room_type'] == 'spectator'
        
        await communicator.disconnect()
    
    async def test_connect_invalid_room_type(self, game, test_user, create_token):
        """测试连接无效房间类型"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/invalid/{game.id}/?token={token}"
        )
        
        # 应该连接失败
        with pytest.raises(AssertionError):
            await communicator.connect()
        
        await communicator.disconnect()
    
    async def test_connect_game_not_found(self, test_user, create_token):
        """测试连接不存在游戏"""
        token = create_token(test_user)
        fake_game_id = '00000000-0000-0000-0000-000000000000'
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{fake_game_id}/?token={token}"
        )
        
        with pytest.raises(AssertionError):
            await communicator.connect()
        
        await communicator.disconnect()
    
    async def test_connect_non_participant_to_game_chat(self, game, spectator_user, create_token):
        """测试非参与者不能连接到对局聊天"""
        token = create_token(spectator_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        # 非参与者连接应该被拒绝
        with pytest.raises(AssertionError):
            await communicator.connect()
        
        await communicator.disconnect()
    
    async def test_connect_non_spectator_to_spectator_chat(self, game, test_user2, create_token):
        """测试非观战者不能连接到观战聊天"""
        token = create_token(test_user2)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/spectator/{game.id}/?token={token}"
        )
        
        # 非观战者连接应该被拒绝
        with pytest.raises(AssertionError):
            await communicator.connect()
        
        await communicator.disconnect()
    
    async def test_connect_with_expired_token(self, game, test_user, create_expired_token):
        """测试使用过期 token 连接"""
        token = create_expired_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        with pytest.raises(AssertionError):
            await communicator.connect()
        
        await communicator.disconnect()
    
    async def test_connect_staff_user_bypass_permission(self, game, create_token):
        """测试管理员用户绕过权限检查"""
        # 创建管理员用户
        admin_user = User.objects.create_user(
            username='chat_admin',
            email='chat_admin@example.com',
            password='SecurePass123',
            is_staff=True
        )
        
        token = create_token(admin_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        # 管理员应该可以连接
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.disconnect()
    
    async def test_disconnect_cleanup(self, game, test_user, create_token):
        """测试断开连接清理"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        # 消耗欢迎和历史消息
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 断开连接
        await communicator.disconnect()
        
        # 重新连接应该成功
        communicator2 = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected2, _ = await communicator2.connect()
        assert connected2 is True
        
        await communicator2.disconnect()


# ==================== 消息发送测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerMessaging:
    """ChatConsumer 消息发送测试"""
    
    async def test_send_text_message(self, game, test_user, create_token):
        """测试发送文本消息"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        # 消耗欢迎和历史消息
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Hello from WebSocket!',
            'message_type': 'text'
        })
        
        # 收到广播消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_MESSAGE'
        assert response['payload']['success'] is True
        assert response['payload']['message']['content'] == 'Hello from WebSocket!'
        assert response['payload']['message']['message_type'] == 'text'
        
        await communicator.disconnect()
    
    async def test_send_emoji_message(self, game, test_user, create_token):
        """测试发送表情消息"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送表情消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': '😀',
            'message_type': 'emoji'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_MESSAGE'
        assert response['payload']['success'] is True
        assert response['payload']['message']['message_type'] == 'emoji'
        
        await communicator.disconnect()
    
    async def test_send_empty_message_error(self, game, test_user, create_token):
        """测试发送空消息错误"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送空消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': '',
            'message_type': 'text'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'EMPTY_MESSAGE'
        
        await communicator.disconnect()
    
    async def test_send_too_long_message_error(self, game, test_user, create_token):
        """测试发送超长消息错误"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送超长消息（超过 500 字符）
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'x' * 600,
            'message_type': 'text'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'MESSAGE_TOO_LONG'
        
        await communicator.disconnect()
    
    async def test_send_invalid_message_type_error(self, game, test_user, create_token):
        """测试发送无效消息类型错误"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送无效消息类型
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Test',
            'message_type': 'invalid_type'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'INVALID_MESSAGE_TYPE'
        
        await communicator.disconnect()
    
    async def test_send_system_message_non_staff_error(self, game, test_user, create_token):
        """测试非管理员发送系统消息错误"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送系统消息（非管理员）
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'System message',
            'message_type': 'system'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'NO_PERMISSION'
        
        await communicator.disconnect()
    
    async def test_send_message_rate_limit(self, game, test_user, create_token):
        """测试消息限流"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送第一条消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Message 1',
            'message_type': 'text'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_MESSAGE'
        assert response['payload']['success'] is True
        
        # 立即发送第二条消息（应该被限流）
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Message 2',
            'message_type': 'text'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'RATE_LIMITED'
        
        await communicator.disconnect()
    
    async def test_send_message_after_rate_limit_delay(self, game, test_user, create_token):
        """测试限流后延迟发送"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送第一条消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Message 1',
            'message_type': 'text'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_MESSAGE'
        
        # 等待限流时间（2 秒）
        import asyncio
        await asyncio.sleep(2.5)
        
        # 发送第二条消息（应该成功）
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Message 2',
            'message_type': 'text'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_MESSAGE'
        assert response['payload']['success'] is True
        
        await communicator.disconnect()


# ==================== 消息广播测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerBroadcast:
    """ChatConsumer 消息广播测试"""
    
    async def test_broadcast_to_multiple_clients(self, game, test_user, test_user2, create_token):
        """测试消息广播到多个客户端"""
        token1 = create_token(test_user)
        token2 = create_token(test_user2)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        comm1 = WebsocketCommunicator(application, f"/ws/chat/game/{game.id}/?token={token1}")
        comm2 = WebsocketCommunicator(application, f"/ws/chat/game/{game.id}/?token={token2}")
        
        connected1, _ = await comm1.connect()
        connected2, _ = await comm2.connect()
        
        assert connected1 is True
        assert connected2 is True
        
        # 消耗欢迎和历史消息
        await comm1.receive_json_from()
        await comm1.receive_json_from()
        await comm2.receive_json_from()
        await comm2.receive_json_from()
        
        # 用户 1 发送消息
        await comm1.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Hello from user1!',
            'message_type': 'text'
        })
        
        # 两个用户都应该收到消息
        response1 = await comm1.receive_json_from()
        response2 = await comm2.receive_json_from()
        
        assert response1['type'] == 'CHAT_MESSAGE'
        assert response2['type'] == 'CHAT_MESSAGE'
        assert response1['payload']['message']['content'] == 'Hello from user1!'
        assert response2['payload']['message']['content'] == 'Hello from user1!'
        
        await comm1.disconnect()
        await comm2.disconnect()
    
    async def test_receive_system_message(self, game, test_user, create_token):
        """测试接收系统消息"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 模拟接收系统消息
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'chat_game_{game.id}',
            {
                'type': 'system_message',
                'content': 'System broadcast message'
            }
        )
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'SYSTEM_MESSAGE'
        assert response['payload']['content'] == 'System broadcast message'
        
        await communicator.disconnect()


# ==================== 历史消息测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerHistory:
    """ChatConsumer 历史消息测试"""
    
    async def test_get_history_on_connect(self, game, test_user, create_token):
        """测试连接时获取历史消息"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        # 收到欢迎消息
        welcome = await communicator.receive_json_from()
        assert welcome['type'] == 'WELCOME'
        
        # 收到历史消息
        history = await communicator.receive_json_from()
        assert history['type'] == 'CHAT_HISTORY'
        assert 'messages' in history['payload']
        assert isinstance(history['payload']['messages'], list)
        
        await communicator.disconnect()
    
    async def test_get_history_with_limit(self, game, test_user, create_token):
        """测试获取带限制的历史消息"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 请求历史消息（限制 10 条）
        await communicator.send_json_to({
            'type': 'GET_HISTORY',
            'limit': 10
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_HISTORY'
        assert response['payload']['success'] is True
        assert len(response['payload']['messages']) <= 10
        
        await communicator.disconnect()
    
    async def test_get_history_max_limit(self, game, test_user, create_token):
        """测试获取历史消息最大限制"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 请求超过最大限制的历史消息
        await communicator.send_json_to({
            'type': 'GET_HISTORY',
            'limit': 200  # 超过 100 的最大限制
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_HISTORY'
        # 应该被限制在 100 条
        assert len(response['payload']['messages']) <= 100
        
        await communicator.disconnect()


# ==================== 心跳测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerHeartbeat:
    """ChatConsumer 心跳测试"""
    
    async def test_heartbeat_request(self, game, test_user, create_token):
        """测试心跳请求"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送心跳
        await communicator.send_json_to({
            'type': 'HEARTBEAT'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'HEARTBEAT'
        assert response['payload']['acknowledged'] is True
        assert 'timestamp' in response['payload']
        
        await communicator.disconnect()
    
    async def test_multiple_heartbeats(self, game, test_user, create_token):
        """测试多次心跳"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送多次心跳
        for i in range(3):
            await communicator.send_json_to({'type': 'HEARTBEAT'})
            response = await communicator.receive_json_from()
            assert response['type'] == 'HEARTBEAT'
            assert response['payload']['acknowledged'] is True
        
        await communicator.disconnect()


# ==================== 删除消息测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerDeleteMessage:
    """ChatConsumer 删除消息测试"""
    
    async def test_delete_message_success(self, game, test_user, create_token):
        """测试成功删除消息"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 先发送一条消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Message to delete',
            'message_type': 'text'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_MESSAGE'
        message_id = response['payload']['message']['id']
        
        # 删除消息
        await communicator.send_json_to({
            'type': 'DELETE_MESSAGE',
            'message_id': message_id
        })
        
        # 应该收到删除确认
        response = await communicator.receive_json_from()
        assert response['type'] == 'MESSAGE_DELETED'
        assert response['payload']['success'] is True
        assert response['payload']['message_id'] == message_id
        
        await communicator.disconnect()
    
    async def test_delete_message_missing_id(self, game, test_user, create_token):
        """测试删除消息缺少 ID"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 删除消息不带 ID
        await communicator.send_json_to({
            'type': 'DELETE_MESSAGE'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'MISSING_MESSAGE_ID'
        
        await communicator.disconnect()


# ==================== 未知消息类型测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerUnknownMessage:
    """ChatConsumer 未知消息类型测试"""
    
    async def test_unknown_message_type(self, game, test_user, create_token):
        """测试未知消息类型"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送未知消息类型
        await communicator.send_json_to({
            'type': 'UNKNOWN_TYPE',
            'data': 'test'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'UNKNOWN_MESSAGE_TYPE'
        
        await communicator.disconnect()
    
    async def test_invalid_json(self, game, test_user, create_token):
        """测试无效 JSON"""
        token = create_token(test_user)
        
        from games.routing import websocket_urlpatterns
        application = ProtocolTypeRouter({
            "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        })
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        assert connected is True
        
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送无效 JSON
        await communicator.send_to(text_data='invalid json{{{')
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'INVALID_JSON'
        
        await communicator.disconnect()


# ==================== ChatConsumer 单元测试（不依赖 ASGI） ====================

@pytest.mark.asyncio
class TestChatConsumerUnit:
    """ChatConsumer 单元测试（Mock 方法）"""
    
    async def test_verify_game_exists_true(self, game):
        """测试验证游戏存在 - 存在"""
        consumer = ChatConsumer()
        
        result = await consumer._verify_game_exists(str(game.id))
        
        assert result is True
    
    async def test_verify_game_exists_false(self):
        """测试验证游戏存在 - 不存在"""
        consumer = ChatConsumer()
        
        fake_id = '00000000-0000-0000-0000-000000000000'
        result = await consumer._verify_game_exists(fake_id)
        
        assert result is False
    
    async def test_format_error(self):
        """测试错误格式化"""
        consumer = ChatConsumer()
        
        error_str = consumer._format_error('TEST_CODE', 'Test error message')
        error = json.loads(error_str)
        
        assert error['type'] == 'ERROR'
        assert error['payload']['success'] is False
        assert error['payload']['error']['code'] == 'TEST_CODE'
        assert error['payload']['error']['message'] == 'Test error message'
    
    @pytest.mark.asyncio
    async def test_send_error(self):
        """测试发送错误"""
        consumer = ChatConsumer()
        consumer.send = AsyncMock()
        
        await consumer._send_error('TEST_CODE', 'Test error')
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'ERROR'
        assert call_args['payload']['error']['code'] == 'TEST_CODE'
    
    @pytest.mark.asyncio
    async def test_send_welcome(self):
        """测试发送欢迎消息"""
        consumer = ChatConsumer()
        consumer.send = AsyncMock()
        consumer.room_type = 'game'
        consumer.game_id = 'test-123'
        consumer.user = {'username': 'testuser'}
        
        await consumer._send_welcome()
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'WELCOME'
        assert call_args['payload']['room_type'] == 'game'
        assert call_args['payload']['username'] == 'testuser'
    
    @pytest.mark.asyncio
    async def test_broadcast_system_message(self):
        """测试广播系统消息"""
        consumer = ChatConsumer()
        consumer.room_group_name = 'test_room'
        consumer.channel_layer = MagicMock()
        consumer.channel_layer.group_send = AsyncMock()
        
        await consumer._broadcast_system_message('System message')
        
        consumer.channel_layer.group_send.assert_called_once()


# ==================== 消息类型枚举测试 ====================

class TestMessageType:
    """MessageType 枚举测试"""
    
    def test_message_type_values(self):
        """测试消息类型值"""
        assert MessageType.TEXT.value == 'text'
        assert MessageType.EMOJI.value == 'emoji'
        assert MessageType.SYSTEM.value == 'system'
    
    def test_message_type_labels(self):
        """测试消息类型标签"""
        assert MessageType.TEXT.label == '文本'
        assert MessageType.EMOJI.label == '表情'
        assert MessageType.SYSTEM.label == '系统'
    
    def test_message_type_choices(self):
        """测试消息类型选择"""
        choices = MessageType.choices
        assert len(choices) == 3
        
        values = [choice[0] for choice in choices]
        assert 'text' in values
        assert 'emoji' in values
        assert 'system' in values


# ==================== 限流配置测试 ====================

class TestChatConsumerConfig:
    """ChatConsumer 配置测试"""
    
    def test_rate_limit_seconds(self):
        """测试限流时间"""
        assert ChatConsumer.RATE_LIMIT_SECONDS == 2
    
    def test_max_message_length(self):
        """测试最大消息长度"""
        assert ChatConsumer.MAX_MESSAGE_LENGTH == 500
