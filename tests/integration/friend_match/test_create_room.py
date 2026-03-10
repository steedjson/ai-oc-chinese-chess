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
    
    @pytest.fixture
    def api_client(self):
        """API 客户端"""
        return APIClient()
    
    @pytest.fixture
    def user(self, db):
        """测试用户"""
        return User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='SecurePass123'
        )
    
    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """认证客户端"""
        api_client.force_authenticate(user=user)
        return api_client
    
    def test_create_room_success(self, authenticated_client):
        """测试成功创建房间"""
        data = {
            'time_control': 600,
            'is_rated': False,
        }
        
        response = authenticated_client.post('/api/v1/friend/create/', data)
        
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
    
    def test_create_room_default_time_control(self, authenticated_client):
        """测试使用默认时间控制创建房间"""
        response = authenticated_client.post('/api/v1/friend/create/', {})
        
        assert response.status_code == status.HTTP_201_CREATED
        room = FriendRoom.objects.get(room_code=response.data['room_code'])
        assert room.game.timeout_seconds == 600  # 默认值
    
    def test_create_room_custom_time_control(self, authenticated_client):
        """测试自定义时间控制"""
        data = {
            'time_control': 1800,  # 30 分钟
            'is_rated': True,
        }
        
        response = authenticated_client.post('/api/v1/friend/create/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        room = FriendRoom.objects.get(room_code=response.data['room_code'])
        assert room.game.timeout_seconds == 1800
        assert room.game.is_rated == True
    
    def test_create_room_invalid_time_control_low(self, authenticated_client):
        """测试时间控制过低"""
        data = {
            'time_control': 30,  # 低于最小值 60
        }
        
        response = authenticated_client.post('/api/v1/friend/create/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'time_control' in response.data
    
    def test_create_room_invalid_time_control_high(self, authenticated_client):
        """测试时间控制过高"""
        data = {
            'time_control': 10000,  # 高于最大值 7200
        }
        
        response = authenticated_client.post('/api/v1/friend/create/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'time_control' in response.data
    
    def test_create_room_expires_at(self, authenticated_client):
        """测试房间过期时间"""
        response = authenticated_client.post('/api/v1/friend/create/', {})
        
        assert response.status_code == status.HTTP_201_CREATED
        room = FriendRoom.objects.get(room_code=response.data['room_code'])
        
        # 过期时间应该是 24 小时后
        expected_expires = timezone.now() + timedelta(hours=24)
        assert abs((room.expires_at - expected_expires).total_seconds()) < 60  # 1 分钟误差
    
    def test_create_room_multiple(self, authenticated_client):
        """测试创建多个房间"""
        room_codes = []
        
        for i in range(3):
            response = authenticated_client.post('/api/v1/friend/create/', {})
            assert response.status_code == status.HTTP_201_CREATED
            room_codes.append(response.data['room_code'])
        
        # 验证所有房间都是唯一的
        assert len(set(room_codes)) == 3
        
        # 验证用户有 3 个房间
        rooms = FriendRoom.objects.filter(creator__username='testuser1')
        assert rooms.count() == 3
    
    def test_create_room_unauthenticated(self, api_client):
        """测试未认证用户创建房间"""
        data = {
            'time_control': 600,
        }
        
        response = api_client.post('/api/v1/friend/create/', data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
