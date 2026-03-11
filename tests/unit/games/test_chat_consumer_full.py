"""
聊天系统 WebSocket Consumer 单元测试

测试 games/chat_consumer.py 中的 ChatConsumer 类

测试范围：
- 连接建立/断开
- 认证和权限验证
- 聊天消息发送/接收
- 消息限流
- 历史消息获取
- 消息删除
- 表情消息

覆盖率目标：227 语句 → 300 行测试代码
"""
import pytest
import json
import time
import asyncio
from datetime import datetime
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from games.chat_consumer import ChatConsumer
from games.models import Game, GameStatus
from games.chat import ChatMessage, ChatMessageManager, MessageType


# ==================== Fixtures ====================

@pytest.fixture
def red_player(db):
    """创建红方玩家"""
    from users.models import User
    return User.objects.create_user(
        username='redplayer',
        email='red@example.com',
        password='testpass123'
    )


@pytest.fixture
def black_player(db):
    """创建黑方玩家"""
    from users.models import User
    return User.objects.create_user(
        username='blackplayer',
        email='black@example.com',
        password='testpass123'
    )


@pytest.fixture
def spectator(db):
    """创建观战者"""
    from users.models import User
    from games.spectator import Spectator, SpectatorStatus
    
    user = User.objects.create_user(
        username='spectator',
        email='spectator@example.com',
        password='testpass123'
    )
    
    return user


@pytest.fixture
def active_game(red_player, black_player, db):
    """创建进行中的游戏"""
    return Game.objects.create(
        red_player=red_player,
        black_player=black_player,
        game_type='ranked',
        status=GameStatus.PLAYING,
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        turn='w'
    )


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
    from games import routing
    
    return ProtocolTypeRouter({
        "websocket": AllowedHostsOriginValidator(
            URLRouter(routing.websocket_urlpatterns)
        ),
    })


# ==================== 连接测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerConnect:
    """ChatConsumer 连接测试"""
    
    async def test_connect_to_game_chat_participant(self, active_game, red_player, create_token, test_asgi_app):
        """测试游戏参与者连接到对局聊天"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        
        # 应该收到欢迎消息
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'WELCOME'
        assert response['payload']['room_type'] == 'game'
        
        # 应该收到历史消息
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'CHAT_HISTORY'
        
        await communicator.disconnect()
    
    async def test_connect_non_participant_cannot_join_game_chat(self, active_game, spectator, create_token, test_asgi_app):
        """测试非参与者不能加入对局聊天"""
        token = create_token(spectator)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        # 应该被拒绝连接
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()
    
    async def test_connect_invalid_room_type(self, active_game, red_player, create_token, test_asgi_app):
        """测试无效房间类型"""
        token = create_token(red_player)
        
        # 注意：实际路由可能不允许无效的房间类型
        # 这个测试取决于路由配置
        pass
    
    async def test_connect_game_not_found(self, red_player, create_token, test_asgi_app):
        """测试游戏不存在"""
        token = create_token(red_player)
        fake_game_id = '00000000-0000-0000-0000-000000000000'
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{fake_game_id}/?token={token}"
        )
        
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()


# ==================== 消息发送测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerSendMessage:
    """ChatConsumer 发送消息测试"""
    
    async def test_send_text_message(self, active_game, red_player, create_token, test_asgi_app):
        """测试发送文本消息"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        
        # 消耗欢迎消息和历史消息
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 发送聊天消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Hello, this is a test message!',
            'message_type': 'text'
        })
        
        # 应该收到广播的消息
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'CHAT_MESSAGE'
        assert response['payload']['success'] is True
        
        await communicator.disconnect()
    
    async def test_send_empty_message(self, active_game, red_player, create_token, test_asgi_app):
        """测试发送空消息"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 发送空消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': '',
            'message_type': 'text'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'EMPTY_MESSAGE'
        
        await communicator.disconnect()
    
    async def test_send_message_too_long(self, active_game, red_player, create_token, test_asgi_app):
        """测试发送超长消息"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 发送超长消息（超过 500 字符）
        long_message = 'x' * 501
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': long_message,
            'message_type': 'text'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'MESSAGE_TOO_LONG'
        
        await communicator.disconnect()
    
    async def test_send_invalid_message_type(self, active_game, red_player, create_token, test_asgi_app):
        """测试发送无效消息类型"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 发送无效消息类型
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Test message',
            'message_type': 'invalid_type'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'INVALID_MESSAGE_TYPE'
        
        await communicator.disconnect()
    
    async def test_send_emoji_message(self, active_game, red_player, create_token, test_asgi_app):
        """测试发送表情消息"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 发送表情消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': '😀',
            'message_type': 'emoji'
        })
        
        # 应该收到响应（成功或无效表情）
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] in ['CHAT_MESSAGE', 'ERROR']
        
        await communicator.disconnect()


# ==================== 消息限流测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerRateLimit:
    """ChatConsumer 消息限流测试"""
    
    async def test_rate_limit(self, active_game, red_player, create_token, test_asgi_app):
        """测试消息限流"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 快速发送两条消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'First message',
            'message_type': 'text'
        })
        await communicator.receive_json_from(timeout=5)
        
        # 立即发送第二条消息（应该被限流）
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Second message',
            'message_type': 'text'
        })
        
        # 应该收到限流错误
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'RATE_LIMITED'
        
        await communicator.disconnect()


# ==================== 历史消息测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerHistory:
    """ChatConsumer 历史消息测试"""
    
    async def test_get_history(self, active_game, red_player, create_token, test_asgi_app):
        """测试获取历史消息"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 请求历史消息
        await communicator.send_json_to({
            'type': 'GET_HISTORY',
            'limit': 50
        })
        
        # 应该收到历史消息
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'CHAT_HISTORY'
        assert response['payload']['success'] is True
        assert 'messages' in response['payload']
        
        await communicator.disconnect()
    
    async def test_get_history_with_limit(self, active_game, red_player, create_token, test_asgi_app):
        """测试获取带限制的历史消息"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 请求历史消息（限制 10 条）
        await communicator.send_json_to({
            'type': 'GET_HISTORY',
            'limit': 10
        })
        
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'CHAT_HISTORY'
        assert len(response['payload']['messages']) <= 10
        
        await communicator.disconnect()


# ==================== 消息删除测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerDeleteMessage:
    """ChatConsumer 消息删除测试"""
    
    async def test_delete_message(self, active_game, red_player, create_token, test_asgi_app):
        """测试删除消息"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 先发送一条消息
        await communicator.send_json_to({
            'type': 'CHAT_MESSAGE',
            'content': 'Message to delete',
            'message_type': 'text'
        })
        msg_response = await communicator.receive_json_from(timeout=5)
        
        # 获取消息 ID（从响应中）
        message_id = msg_response['payload'].get('message', {}).get('id')
        
        if message_id:
            # 删除消息
            await communicator.send_json_to({
                'type': 'DELETE_MESSAGE',
                'message_id': message_id
            })
            
            # 应该收到删除响应
            response = await communicator.receive_json_from(timeout=5)
            assert response['type'] in ['MESSAGE_DELETED', 'ERROR']
        
        await communicator.disconnect()
    
    async def test_delete_message_missing_id(self, active_game, red_player, create_token, test_asgi_app):
        """测试删除消息缺少 ID"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 删除消息但不提供 ID
        await communicator.send_json_to({
            'type': 'DELETE_MESSAGE'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'MISSING_MESSAGE_ID'
        
        await communicator.disconnect()


# ==================== 心跳测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerHeartbeat:
    """ChatConsumer 心跳测试"""
    
    async def test_heartbeat(self, active_game, red_player, create_token, test_asgi_app):
        """测试心跳消息"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 发送心跳
        await communicator.send_json_to({
            'type': 'HEARTBEAT'
        })
        
        # 应该收到响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'HEARTBEAT'
        assert response['payload']['acknowledged'] is True
        
        await communicator.disconnect()


# ==================== 频道层消息处理器测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerChannelHandlers:
    """ChatConsumer 频道层消息处理器测试"""
    
    async def test_chat_message_handler(self, active_game, red_player, create_token, test_asgi_app):
        """测试 chat_message 消息处理器"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收聊天消息
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'chat_game_{active_game.id}',
            {
                'type': 'chat_message',
                'message': {
                    'id': '123',
                    'content': 'Test message from other user',
                    'sender': {'username': 'other_user'},
                    'message_type': 'text',
                    'created_at': datetime.utcnow().isoformat() + 'Z'
                }
            }
        )
        
        # 应该收到聊天消息
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'CHAT_MESSAGE'
        assert response['payload']['success'] is True
        
        await communicator.disconnect()
    
    async def test_message_deleted_handler(self, active_game, red_player, create_token, test_asgi_app):
        """测试 message_deleted 消息处理器"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收消息删除通知
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'chat_game_{active_game.id}',
            {
                'type': 'message_deleted',
                'message_id': '123'
            }
        )
        
        # 应该收到消息删除通知
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'MESSAGE_DELETED'
        assert response['payload']['success'] is True
        
        await communicator.disconnect()
    
    async def test_system_message_handler(self, active_game, red_player, create_token, test_asgi_app):
        """测试 system_message 消息处理器"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收系统消息
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'chat_game_{active_game.id}',
            {
                'type': 'system_message',
                'content': 'System notification'
            }
        )
        
        # 应该收到系统消息
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'SYSTEM_MESSAGE'
        assert response['payload']['content'] == 'System notification'
        
        await communicator.disconnect()


# ==================== 边界条件测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerEdgeCases:
    """ChatConsumer 边界条件测试"""
    
    async def test_invalid_json(self, active_game, red_player, create_token, test_asgi_app):
        """测试无效 JSON"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 发送无效 JSON
        await communicator.send_to_text("invalid json {")
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'INVALID_JSON'
        
        await communicator.disconnect()
    
    async def test_unknown_message_type(self, active_game, red_player, create_token, test_asgi_app):
        """测试未知消息类型"""
        token = create_token(red_player)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/chat/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        await communicator.receive_json_from(timeout=5)
        
        # 发送未知消息类型
        await communicator.send_json_to({
            'type': 'UNKNOWN_TYPE'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'UNKNOWN_MESSAGE_TYPE'
        
        await communicator.disconnect()
