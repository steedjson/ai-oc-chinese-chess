"""
聊天系统 API 视图测试
"""
import pytest
import json
from django.urls import reverse
from rest_framework.test import APIClient

from games.chat import ChatMessage, MessageType
from games.models import Game


@pytest.mark.django_db
class TestChatMessageAPI:
    """测试聊天消息 API"""
    
    def test_send_message_success(self, game, user, auth_client):
        """测试成功发送消息"""
        url = reverse('chat-send-message', kwargs={'game_id': game.id})
        
        data = {
            'content': 'Hello from API!',
            'message_type': 'text',
            'room_type': 'game'
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['success'] is True
        assert response.data['message']['content'] == 'Hello from API!'
        assert response.data['message']['sender']['id'] == str(user.id)
    
    def test_send_message_unauthenticated(self, game, api_client):
        """测试未认证用户发送消息"""
        url = reverse('chat-send-message', kwargs={'game_id': game.id})
        
        data = {
            'content': 'Hello!',
            'message_type': 'text',
            'room_type': 'game'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 401
    
    def test_send_message_empty_content(self, game, user, auth_client):
        """测试发送空消息"""
        url = reverse('chat-send-message', kwargs={'game_id': game.id})
        
        data = {
            'content': '',
            'message_type': 'text',
            'room_type': 'game'
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert '不能为空' in response.data['error']
    
    def test_send_message_too_long(self, game, user, auth_client):
        """测试发送超长消息"""
        url = reverse('chat-send-message', kwargs={'game_id': game.id})
        
        data = {
            'content': 'x' * 600,
            'message_type': 'text',
            'room_type': 'game'
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert '长度不能超过' in response.data['error']
    
    def test_send_message_invalid_room_type(self, game, user, auth_client):
        """测试无效的房间类型"""
        url = reverse('chat-send-message', kwargs={'game_id': game.id})
        
        data = {
            'content': 'Hello!',
            'message_type': 'text',
            'room_type': 'invalid'
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert '无效的房间类型' in response.data['error']
    
    def test_send_message_invalid_message_type(self, game, user, auth_client):
        """测试无效的消息类型"""
        url = reverse('chat-send-message', kwargs={'game_id': game.id})
        
        data = {
            'content': 'Hello!',
            'message_type': 'invalid',
            'room_type': 'game'
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert '无效的消息类型' in response.data['error']
    
    def test_send_system_message_as_admin(self, game, admin_user, admin_client):
        """测试管理员发送系统消息"""
        url = reverse('chat-send-message', kwargs={'game_id': game.id})
        
        data = {
            'content': 'System announcement',
            'message_type': 'system',
            'room_type': 'game'
        }
        
        response = admin_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['success'] is True
        assert response.data['message']['message_type'] == 'system'
    
    def test_send_system_message_as_normal_user(self, game, user, auth_client):
        """测试普通用户发送系统消息（应该失败）"""
        url = reverse('chat-send-message', kwargs={'game_id': game.id})
        
        data = {
            'content': 'Fake system message',
            'message_type': 'system',
            'room_type': 'game'
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == 403
        assert response.data['success'] is False
        assert '无权限' in response.data['error']
    
    def test_get_chat_history(self, game, user, auth_client):
        """测试获取聊天历史"""
        # 先创建一些消息
        for i in range(5):
            ChatMessage.objects.create(
                game=game,
                sender=user,
                content=f'Message {i}',
                message_type=MessageType.TEXT,
                room_type='game'
            )
        
        url = reverse('chat-get-history', kwargs={'game_id': game.id})
        
        response = auth_client.get(url)
        
        assert response.status_code == 200
        assert response.data['success'] is True
        assert len(response.data['messages']) == 5
    
    def test_get_chat_history_limit(self, game, user, auth_client):
        """测试获取聊天历史（限制数量）"""
        # 创建 10 条消息
        for i in range(10):
            ChatMessage.objects.create(
                game=game,
                sender=user,
                content=f'Message {i}',
                message_type=MessageType.TEXT,
                room_type='game'
            )
        
        url = reverse('chat-get-history', kwargs={'game_id': game.id})
        
        response = auth_client.get(url, {'limit': 5})
        
        assert response.status_code == 200
        assert response.data['success'] is True
        assert len(response.data['messages']) == 5
    
    def test_get_chat_history_spectator_room(self, game, user, auth_client):
        """测试获取观战房间聊天历史"""
        # 创建观战房间消息
        ChatMessage.objects.create(
            game=game,
            sender=user,
            content='Spectator message',
            message_type=MessageType.TEXT,
            room_type='spectator'
        )
        
        url = reverse('chat-get-history', kwargs={'game_id': game.id})
        
        response = auth_client.get(url, {'room_type': 'spectator'})
        
        assert response.status_code == 200
        assert response.data['success'] is True
        assert len(response.data['messages']) == 1
        assert response.data['messages'][0]['content'] == 'Spectator message'
    
    def test_get_chat_history_unauthorized(self, game, user3, auth_client_3):
        """测试未授权用户获取聊天历史"""
        url = reverse('chat-get-history', kwargs={'game_id': game.id})
        
        response = auth_client_3.get(url)
        
        # 非参与者应该被拒绝
        assert response.status_code == 403
        assert response.data['success'] is False
        assert '无权限' in response.data['error']
    
    def test_delete_message_success(self, game, user, auth_client):
        """测试成功删除消息"""
        # 创建消息
        message = ChatMessage.objects.create(
            game=game,
            sender=user,
            content='To delete',
            message_type=MessageType.TEXT,
            room_type='game'
        )
        
        url = reverse('chat-delete-message', kwargs={'message_uuid': message.message_uuid})
        
        response = auth_client.delete(url)
        
        assert response.status_code == 200
        assert response.data['success'] is True
        
        # 验证消息已软删除
        message.refresh_from_db()
        assert message.is_deleted is True
    
    def test_delete_message_no_permission(self, game, user, user2, auth_client_2):
        """测试无权限删除他人消息"""
        # 用户 1 创建消息
        message = ChatMessage.objects.create(
            game=game,
            sender=user,
            content='My message',
            message_type=MessageType.TEXT,
            room_type='game'
        )
        
        url = reverse('chat-delete-message', kwargs={'message_uuid': message.message_uuid})
        
        # 用户 2 尝试删除
        response = auth_client_2.delete(url)
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert '无权限' in response.data['error']
    
    def test_get_chat_stats(self, game, user, auth_client):
        """测试获取聊天统计"""
        # 创建一些消息
        for i in range(3):
            ChatMessage.objects.create(
                game=game,
                sender=user,
                content=f'Game message {i}',
                message_type=MessageType.TEXT,
                room_type='game'
            )
        
        for i in range(2):
            ChatMessage.objects.create(
                game=game,
                sender=user,
                content=f'Spectator message {i}',
                message_type=MessageType.TEXT,
                room_type='spectator'
            )
        
        url = reverse('chat-get-stats', kwargs={'game_id': game.id})
        
        response = auth_client.get(url)
        
        assert response.status_code == 200
        assert response.data['success'] is True
        assert response.data['stats']['total_messages'] == 5
        assert response.data['stats']['game_messages'] == 3
        assert response.data['stats']['spectator_messages'] == 2


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
def user3():
    """创建测试用户（非参与者/观战者）"""
    from users.models import User
    return User.objects.create_user(
        username='spectator',
        email='spectator@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user():
    """创建管理员用户"""
    from users.models import User
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def game(user, user2):
    """创建测试游戏"""
    return Game.objects.create(
        red_player=user,
        black_player=user2,
        game_type='online',
        status='playing',
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        turn='w'
    )


@pytest.fixture
def api_client():
    """创建未认证的 API 客户端"""
    return APIClient()


@pytest.fixture
def auth_client(user):
    """创建已认证的 API 客户端（普通用户）"""
    from authentication.services import TokenService
    
    client = APIClient()
    tokens = TokenService.generate_tokens(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
    return client


@pytest.fixture
def auth_client_2(user2):
    """创建已认证的 API 客户端（用户 2 - 黑方）"""
    from authentication.services import TokenService
    
    client = APIClient()
    tokens = TokenService.generate_tokens(user2)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
    return client


@pytest.fixture
def auth_client_3(user3):
    """创建已认证的 API 客户端（用户 3 - 非参与者）"""
    from authentication.services import TokenService
    
    client = APIClient()
    tokens = TokenService.generate_tokens(user3)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
    return client


@pytest.fixture
def admin_client(admin_user):
    """创建已认证的管理员客户端"""
    from authentication.services import TokenService
    
    client = APIClient()
    tokens = TokenService.generate_tokens(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
    return client
