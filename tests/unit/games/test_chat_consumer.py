"""
聊天系统 WebSocket Consumer 测试
"""
import pytest
import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.conf import settings
from django.urls import re_path

# 导入路由配置和 Consumer
from games.routing import websocket_urlpatterns
from games.chat_consumer import ChatConsumer


# 创建测试用的 ASGI 应用
def create_test_asgi_application():
    """创建测试用的 ASGI 应用"""
    return ProtocolTypeRouter({
        "websocket": AllowedHostsOriginValidator(
            URLRouter(websocket_urlpatterns)
        ),
    })


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumer:
    """测试 ChatConsumer"""
    
    async def test_connect_to_game_chat(self, game, user, create_token):
        """测试连接到对局聊天"""
        token = create_token(user)
        
        application = create_test_asgi_application()
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        
        assert connected is True
        
        # 应该收到欢迎消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'WELCOME'
        assert response['payload']['room_type'] == 'game'
        
        # 应该收到历史消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_HISTORY'
        
        await communicator.disconnect()
    
    async def test_connect_to_spectator_chat(self, game, spectator_user, create_token):
        """测试连接到观战聊天"""
        token = create_token(spectator_user)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/spectator/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        
        assert connected is True
        
        # 应该收到欢迎消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'WELCOME'
        assert response['payload']['room_type'] == 'spectator'
        
        await communicator.disconnect()
    
    async def test_non_participant_cannot_join_game_chat(self, game, spectator_user, create_token):
        """测试非参与者不能加入对局聊天"""
        token = create_token(spectator_user)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        # 尝试连接，应该会收到 websocket.close 而不是 websocket.accept
        # WebsocketCommunicator.connect() 会断言收到 accept，所以会抛出 AssertionError
        # 这是预期行为，表示连接被拒绝
        with pytest.raises(AssertionError):
            await communicator.connect()
        
        await communicator.disconnect()
    
    async def test_non_spectator_cannot_join_spectator_chat(self, game, user2, create_token):
        """测试非观战者不能加入观战聊天"""
        token = create_token(user2)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/spectator/{game.id}/?token={token}"
        )
        
        # 尝试连接，应该会收到 websocket.close 而不是 websocket.accept
        # WebsocketCommunicator.connect() 会断言收到 accept，所以会抛出 AssertionError
        # 这是预期行为，表示连接被拒绝
        with pytest.raises(AssertionError):
            await communicator.connect()
        
        await communicator.disconnect()
    
    async def test_send_chat_message(self, game, user, create_token):
        """测试发送聊天消息"""
        token = create_token(user)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        assert connected is True
        
        # 消耗欢迎消息和历史消息
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Hello from WebSocket!',
            'message_type': 'text'
        })
        
        # 应该收到广播的消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_MESSAGE'
        assert response['payload']['success'] is True
        assert response['payload']['message']['content'] == 'Hello from WebSocket!'
        
        await communicator.disconnect()
    
    async def test_send_emoji_message(self, game, user, create_token):
        """测试发送表情消息"""
        token = create_token(user)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        assert connected is True
        
        # 消耗欢迎消息和历史消息
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送表情消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': '😀',
            'message_type': 'emoji'
        })
        
        # 应该收到广播的消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'CHAT_MESSAGE'
        assert response['payload']['success'] is True
        assert response['payload']['message']['message_type'] == 'emoji'
        
        await communicator.disconnect()
    
    async def test_send_message_rate_limit(self, game, user, create_token):
        """测试消息限流"""
        token = create_token(user)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        assert connected is True
        
        # 消耗欢迎消息和历史消息
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
    
    async def test_send_empty_message(self, game, user, create_token):
        """测试发送空消息"""
        token = create_token(user)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        assert connected is True
        
        # 消耗欢迎消息和历史消息
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
    
    async def test_send_too_long_message(self, game, user, create_token):
        """测试发送超长消息"""
        token = create_token(user)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        assert connected is True
        
        # 消耗欢迎消息和历史消息
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送超长消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'x' * 600,
            'message_type': 'text'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'MESSAGE_TOO_LONG'
        
        await communicator.disconnect()
    
    async def test_broadcast_message_to_multiple_clients(self, game, user, user2, create_token):
        """测试消息广播到多个客户端"""
        # 创建两个连接（红方和黑方）
        token1 = create_token(user)
        token2 = create_token(user2)
        
        comm1 = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token1}"
        )
        comm2 = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token2}"
        )
        
        connected1, _ = await comm1.connect()
        connected2, _ = await comm2.connect()
        
        assert connected1 is True
        assert connected2 is True
        
        # 消耗欢迎消息和历史消息
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
    
    async def test_get_chat_history(self, game, user, create_token):
        """测试获取聊天历史"""
        token = create_token(user)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        assert connected is True
        
        # 应该收到历史消息
        response = await communicator.receive_json_from()  # WELCOME
        assert response['type'] == 'WELCOME'
        
        response = await communicator.receive_json_from()  # CHAT_HISTORY
        assert response['type'] == 'CHAT_HISTORY'
        assert 'messages' in response['payload']
        
        await communicator.disconnect()
    
    async def test_heartbeat(self, game, user, create_token):
        """测试心跳"""
        token = create_token(user)
        
        communicator = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect()
        assert connected is True
        
        # 消耗欢迎消息和历史消息
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # 发送心跳
        await communicator.send_json_to({
            'type': 'HEARTBEAT'
        })
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'HEARTBEAT'
        assert response['payload']['acknowledged'] is True
        
        await communicator.disconnect()
    
    async def test_disconnect(self, game, user, create_token):
        """测试断开连接"""
        token = create_token(user)
        
        # 第一次连接
        communicator1 = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        connected1, subprotocol = await communicator1.connect()
        assert connected1 is True
        
        # 收到欢迎消息和历史消息
        await communicator1.receive_json_from()
        await communicator1.receive_json_from()
        
        # 断开连接
        await communicator1.disconnect()
        
        # 创建新的连接（模拟二次连接）
        communicator2 = WebsocketCommunicator(
            create_test_asgi_application(),
            f"/ws/chat/game/{game.id}/?token={token}"
        )
        
        # 二次连接应该成功（因为这是新的连接）
        connected2, _ = await communicator2.connect()
        assert connected2 is True
        
        # 清理
        await communicator2.disconnect()


# 导入 Consumer
from games.chat_consumer import ChatConsumer


# Pytest fixtures
@pytest.fixture
def user():
    """创建测试用户（红方）"""
    from users.models import User
    return User.objects.create_user(
        username='redplayer',
        email='red@example.com',
        password='testpass123'
    )


@pytest.fixture
def user2():
    """创建测试用户（黑方）"""
    from users.models import User
    return User.objects.create_user(
        username='blackplayer',
        email='black@example.com',
        password='testpass123'
    )


@pytest.fixture
def spectator_user(game):
    """创建测试用户（观战者）"""
    from users.models import User
    from games.spectator import Spectator, SpectatorStatus
    
    user = User.objects.create_user(
        username='spectator',
        email='spectator@example.com',
        password='testpass123'
    )
    
    # 创建观战者记录
    Spectator.objects.create(
        game=game,
        user=user,
        status=SpectatorStatus.WATCHING
    )
    
    return user


@pytest.fixture
def game(user, user2):
    """创建测试游戏"""
    from games.models import Game, GameStatus
    
    return Game.objects.create(
        red_player=user,
        black_player=user2,
        game_type='online',
        status=GameStatus.PLAYING,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        turn='w'
    )


@pytest.fixture
def create_token():
    """创建 JWT token 的工厂函数"""
    from authentication.services import TokenService
    
    def _create_token(user):
        tokens = TokenService.generate_tokens(user)
        return tokens['access_token']
    
    return _create_token
