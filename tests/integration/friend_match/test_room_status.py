"""
好友对战房间状态查询测试

测试端点：GET /api/v1/friend/{room_code}/
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
class TestRoomStatus:
    """测试房间状态查询"""
    
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
    
    def test_get_room_status_success(self, api_client, user2, room):
        """测试成功获取房间状态"""
        api_client.force_authenticate(user=user2)
        
        response = api_client.get(f'/api/v1/friend/rooms/{room.room_code}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['room_code'] == room.room_code
        assert response.data['status'] == 'waiting'
        assert response.data['creator_username'] == 'user1'
        assert 'invite_link' in response.data
        assert 'expires_at' in response.data
        assert 'created_at' in response.data
    
    def test_get_room_status_not_found(self, api_client, user2):
        """测试获取不存在的房间"""
        api_client.force_authenticate(user=user2)
        
        response = api_client.get('/api/v1/friend/rooms/CHESSINVALID/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_room_status_case_insensitive(self, api_client, user2, room):
        """测试房间号大小写不敏感"""
        api_client.force_authenticate(user=user2)
        
        # 使用小写房间号
        response = api_client.get(f'/api/v1/friend/rooms/{room.room_code.lower()}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['room_code'] == room.room_code
    
    def test_get_room_status_playing(self, api_client, user2, room):
        """测试获取进行中的房间状态"""
        # 更新房间状态
        room.status = 'playing'
        room.started_at = timezone.now()
        room.save()
        
        api_client.force_authenticate(user=user2)
        
        response = api_client.get(f'/api/v1/friend/rooms/{room.room_code}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'playing'
        assert 'started_at' in response.data
    
    def test_get_room_status_finished(self, api_client, user2, room):
        """测试获取已结束的房间状态"""
        # 更新房间状态
        room.status = 'finished'
        room.finished_at = timezone.now()
        room.save()
        
        api_client.force_authenticate(user=user2)
        
        response = api_client.get(f'/api/v1/friend/rooms/{room.room_code}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'finished'
        assert 'finished_at' in response.data
    
    def test_get_room_status_expired(self, api_client, user2, room):
        """测试获取已过期的房间状态"""
        # 更新房间过期时间
        room.expires_at = timezone.now() - timedelta(hours=1)
        room.status = 'expired'
        room.save()
        
        api_client.force_authenticate(user=user2)
        
        response = api_client.get(f'/api/v1/friend/rooms/{room.room_code}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'expired'
    
    def test_get_room_status_unauthenticated(self, api_client, room):
        """测试未认证用户获取房间状态"""
        response = api_client.get(f'/api/v1/friend/rooms/{room.room_code}/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_room_status_creator(self, api_client, user1, room):
        """测试房主获取自己房间状态"""
        api_client.force_authenticate(user=user1)
        
        response = api_client.get(f'/api/v1/friend/rooms/{room.room_code}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['creator_username'] == 'user1'
    
    def test_get_room_status_invite_link(self, api_client, user2, room):
        """测试邀请链接格式"""
        api_client.force_authenticate(user=user2)
        
        response = api_client.get(f'/api/v1/friend/rooms/{room.room_code}/')
        
        assert response.status_code == status.HTTP_200_OK
        invite_link = response.data['invite_link']
        assert room.room_code in invite_link
        assert '/games/friend/join/' in invite_link
    
    def test_get_room_status_timestamps(self, api_client, user2, room):
        """测试时间戳格式"""
        api_client.force_authenticate(user=user2)
        
        response = api_client.get(f'/api/v1/friend/rooms/{room.room_code}/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # 验证时间戳是 ISO 格式
        assert 'T' in response.data['created_at']
        assert 'T' in response.data['updated_at']
        assert 'T' in response.data['expires_at']


@pytest.mark.django_db
class TestMyRooms:
    """测试我的房间列表"""
    
    @pytest.fixture
    def api_client(self):
        """API 客户端"""
        return APIClient()
    
    @pytest.fixture
    def user(self, db):
        """测试用户"""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123'
        )
    
    def test_get_my_rooms_success(self, api_client, user):
        """测试获取我的房间列表"""
        api_client.force_authenticate(user=user)
        
        # 创建 3 个房间
        for i in range(3):
            from games.models import Game, FriendRoom
            from django.utils import timezone
            from datetime import timedelta
            
            game = Game.objects.create(
                game_type='friend',
                status='waiting',
                player_red=user,
                timeout_seconds=600,
            )
            
            FriendRoom.objects.create(
                game=game,
                creator=user,
                status='waiting',
                expires_at=timezone.now() + timedelta(hours=24),
            )
        
        response = api_client.get('/api/v1/friend/my-rooms/')
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 3
        
        # 验证所有房间都是该用户创建的
        for room_data in response.data:
            assert room_data['creator_username'] == 'testuser'
    
    def test_get_my_rooms_empty(self, api_client, user):
        """测试空房间列表"""
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/v1/friend/my-rooms/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []
    
    def test_get_my_rooms_unauthenticated(self, api_client):
        """测试未认证用户获取房间列表"""
        response = api_client.get('/api/v1/friend/my-rooms/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_my_rooms_limit(self, api_client, user):
        """测试房间列表数量限制"""
        api_client.force_authenticate(user=user)
        
        # 创建 15 个房间
        for i in range(15):
            from games.models import Game, FriendRoom
            from django.utils import timezone
            from datetime import timedelta
            
            game = Game.objects.create(
                game_type='friend',
                status='waiting',
                player_red=user,
                timeout_seconds=600,
            )
            
            FriendRoom.objects.create(
                game=game,
                creator=user,
                status='waiting',
                expires_at=timezone.now() + timedelta(hours=24),
            )
        
        response = api_client.get('/api/v1/friend/my-rooms/')
        
        assert response.status_code == status.HTTP_200_OK
        # 应该只返回最新的 10 个
        assert len(response.data) == 10


@pytest.mark.django_db
class TestActiveRooms:
    """测试活跃房间列表"""
    
    @pytest.fixture
    def api_client(self):
        """API 客户端"""
        return APIClient()
    
    @pytest.fixture
    def user(self, db):
        """测试用户"""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123'
        )
    
    def test_get_active_rooms_success(self, api_client, user):
        """测试获取活跃房间列表"""
        api_client.force_authenticate(user=user)
        
        # 创建 3 个活跃房间
        for i in range(3):
            from games.models import Game, FriendRoom
            from django.utils import timezone
            from datetime import timedelta
            
            game = Game.objects.create(
                game_type='friend',
                status='waiting',
                player_red=user,
                timeout_seconds=600,
            )
            
            FriendRoom.objects.create(
                game=game,
                creator=user,
                status='waiting',
                expires_at=timezone.now() + timedelta(hours=24),
            )
        
        response = api_client.get('/api/v1/friend/active-rooms/')
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        # 应该包含所有活跃房间
        assert len(response.data) >= 3
    
    def test_get_active_rooms_only_waiting(self, api_client, user):
        """测试只返回等待中的房间"""
        api_client.force_authenticate(user=user)
        
        from games.models import Game, FriendRoom
        from django.utils import timezone
        from datetime import timedelta
        
        # 创建等待中的房间
        game1 = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user,
            timeout_seconds=600,
        )
        room1 = FriendRoom.objects.create(
            game=game1,
            creator=user,
            status='waiting',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        
        # 创建进行中的房间
        game2 = Game.objects.create(
            game_type='friend',
            status='playing',
            player_red=user,
            timeout_seconds=600,
        )
        room2 = FriendRoom.objects.create(
            game=game2,
            creator=user,
            status='playing',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        
        response = api_client.get('/api/v1/friend/active-rooms/')
        
        assert response.status_code == status.HTTP_200_OK
        # 只应该返回等待中的房间
        room_codes = [r['room_code'] for r in response.data]
        assert room1.room_code in room_codes
        assert room2.room_code not in room_codes
    
    def test_get_active_rooms_unauthenticated(self, api_client):
        """测试未认证用户获取活跃房间"""
        response = api_client.get('/api/v1/friend/active-rooms/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
