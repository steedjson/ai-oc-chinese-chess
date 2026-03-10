"""
好友对战房间加入测试

测试端点：POST /api/v1/friend/join/
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from django.utils import timezone

from games.models import FriendRoom, Game

User = get_user_model()


@pytest.mark.django_db
class TestJoinRoom:
    """测试加入房间"""
    
    @pytest.fixture
    def api_client(self):
        """API 客户端"""
        return APIClient()
    
    @pytest.fixture
    def user1(self, db):
        """创建者用户"""
        return User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='SecurePass123'
        )
    
    @pytest.fixture
    def user2(self, db):
        """加入者用户"""
        return User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='SecurePass123'
        )
    
    @pytest.fixture
    def room(self, user1):
        """创建测试房间"""
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user1,
            timeout_seconds=600,
            red_time_remaining=600,
            black_time_remaining=600,
        )
        
        room = FriendRoom.objects.create(
            game=game,
            creator=user1,
            status='waiting',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        
        return room
    
    def test_join_room_success(self, api_client, user2, room):
        """测试成功加入房间"""
        api_client.force_authenticate(user=user2)
        
        data = {
            'room_code': room.room_code,
        }
        
        response = api_client.post('/api/v1/friend/join/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '加入成功'
        assert response.data['your_color'] == 'black'
        assert 'room' in response.data
        assert 'game_id' in response.data
        
        # 验证房间状态更新
        room.refresh_from_db()
        assert room.status == 'playing'
        assert room.started_at is not None
        
        # 验证游戏状态更新
        game = room.game
        game.refresh_from_db()
        assert game.status == 'playing'
        assert game.player_black == user2
    
    def test_join_room_not_found(self, api_client, user2):
        """测试加入不存在的房间"""
        api_client.force_authenticate(user=user2)
        
        data = {
            'room_code': 'CHESSINVALID',
        }
        
        response = api_client.post('/api/v1/friend/join/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'room_code' in response.data
    
    def test_join_room_expired(self, api_client, user2, user1):
        """测试加入过期房间"""
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user1,
            timeout_seconds=600,
        )
        
        room = FriendRoom.objects.create(
            game=game,
            creator=user1,
            status='waiting',
            expires_at=timezone.now() - timedelta(hours=1),  # 已过期
        )
        
        api_client.force_authenticate(user=user2)
        
        data = {
            'room_code': room.room_code,
        }
        
        response = api_client.post('/api/v1/friend/join/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'room_code' in response.data
    
    def test_join_room_already_playing(self, api_client, user2, room):
        """测试加入已在进行中的房间"""
        # 更新房间状态为 playing
        room.status = 'playing'
        room.save()
        
        api_client.force_authenticate(user=user2)
        
        data = {
            'room_code': room.room_code,
        }
        
        response = api_client.post('/api/v1/friend/join/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'room_code' in response.data
    
    def test_join_own_room(self, api_client, user1, room):
        """测试加入自己的房间"""
        api_client.force_authenticate(user=user1)
        
        data = {
            'room_code': room.room_code,
        }
        
        response = api_client.post('/api/v1/friend/join/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'room_code' in response.data
        assert '不能加入自己的房间' in str(response.data['room_code'])
    
    def test_join_room_case_insensitive(self, api_client, user2, room):
        """测试房间号大小写不敏感"""
        api_client.force_authenticate(user=user2)
        
        # 使用小写房间号
        data = {
            'room_code': room.room_code.lower(),
        }
        
        response = api_client.post('/api/v1/friend/join/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # 验证加入成功
        room.refresh_from_db()
        assert room.status == 'playing'
    
    def test_join_room_unauthenticated(self, api_client, room):
        """测试未认证用户加入房间"""
        data = {
            'room_code': room.room_code,
        }
        
        response = api_client.post('/api/v1/friend/join/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_join_room_finished(self, api_client, user2, user1):
        """测试加入已结束的房间"""
        game = Game.objects.create(
            game_type='friend',
            status='finished',
            player_red=user1,
            timeout_seconds=600,
        )
        
        room = FriendRoom.objects.create(
            game=game,
            creator=user1,
            status='finished',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        
        api_client.force_authenticate(user=user2)
        
        data = {
            'room_code': room.room_code,
        }
        
        response = api_client.post('/api/v1/friend/join/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_join_room_full(self, api_client, user2, user1):
        """测试加入已满的房间（已有黑方）"""
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='SecurePass123',
        )
        
        game = Game.objects.create(
            game_type='friend',
            status='playing',
            player_red=user1,
            player_black=user3,
            timeout_seconds=600,
        )
        
        room = FriendRoom.objects.create(
            game=game,
            creator=user1,
            status='playing',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        
        api_client.force_authenticate(user=user2)
        
        data = {
            'room_code': room.room_code,
        }
        
        response = api_client.post('/api/v1/friend/join/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
