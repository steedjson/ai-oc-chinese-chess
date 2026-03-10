"""
好友对战房间创建测试

测试端点：POST /api/v1/friend/create/
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
class TestCreateRoom:
    """测试创建房间"""
    
    def test_create_room_success(self):
        """测试成功创建房间"""
        from rest_framework.test import APIClient
        
        # 创建用户
        user = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='SecurePass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        data = {
            'time_control': 600,
            'is_rated': False,
        }
        
        response = client.post('/api/v1/friend/create/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'room_code' in response.data
        assert response.data['room_code'].startswith('CHESS')
        assert response.data['status'] == 'waiting'
        assert response.data['creator_username'] == 'testuser1'
        assert 'invite_link' in response.data
        
        # 验证数据库记录
        room = FriendRoom.objects.get(room_code=response.data['room_code'])
        assert room.creator.username == 'testuser1'
        assert room.game.timeout_seconds == 600
        assert room.game.is_rated == False
    
    def test_create_room_unauthenticated(self):
        """测试未认证用户创建房间"""
        from rest_framework.test import APIClient
        
        client = APIClient()
        data = {
            'time_control': 600,
        }
        
        response = client.post('/api/v1/friend/create/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
