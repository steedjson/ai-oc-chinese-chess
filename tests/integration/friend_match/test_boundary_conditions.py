"""
好友对战边界条件测试

测试端点：
- POST /api/v1/friend/create/
- POST /api/v1/friend/join/
- GET /api/v1/friend/{room_code}/
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta, datetime
from django.utils import timezone
from unittest.mock import patch

from games.models import FriendRoom, Game

User = get_user_model()


@pytest.mark.django_db
class TestRoomCodeCaseInsensitive:
    """测试房间号大小写不敏感"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123'
        )
    
    @pytest.fixture
    def room(self, user, db):
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user,
            timeout_seconds=600,
        )
        return FriendRoom.objects.create(
            game=game,
            creator=user,
            status='waiting',
            expires_at=timezone.now() + timedelta(hours=24),
        )
    
    def test_retrieve_room_lowercase(self, api_client, user, room):
        """测试使用小写房间号查询"""
        api_client.force_authenticate(user=user)
        
        # 使用小写房间号
        lowercase_code = room.room_code.lower()
        response = api_client.get(f'/api/v1/friend/{lowercase_code}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['room_code'] == room.room_code
    
    def test_retrieve_room_mixed_case(self, api_client, user, room):
        """测试使用混合大小写房间号查询"""
        api_client.force_authenticate(user=user)
        
        # 使用混合大小写
        mixed_case = room.room_code[:5] + room.room_code[5:].lower()
        response = api_client.get(f'/api/v1/friend/{mixed_case}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['room_code'] == room.room_code


@pytest.mark.django_db
class TestRoomExpirationBoundary:
    """测试房间过期时间边界"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123'
        )
    
    def test_room_expires_exactly_at_boundary(self, api_client, user, db):
        """测试房间在过期时间边界点的状态"""
        # 创建刚好过期的房间
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user,
            timeout_seconds=600,
        )
        
        # 过期时间设置为 1 秒前
        expires_at = timezone.now() - timedelta(seconds=1)
        room = FriendRoom.objects.create(
            game=game,
            creator=user,
            status='waiting',
            expires_at=expires_at,
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get(f'/api/v1/friend/{room.room_code}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'waiting'  # 状态不会自动更新，需要清理任务
    
    def test_room_not_expired_yet(self, api_client, user, db):
        """测试房间还未过期"""
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user,
            timeout_seconds=600,
        )
        
        # 过期时间设置为 1 分钟后
        expires_at = timezone.now() + timedelta(minutes=1)
        room = FriendRoom.objects.create(
            game=game,
            creator=user,
            status='waiting',
            expires_at=expires_at,
        )
        
        assert not room.is_expired()
        assert room.is_joinable()
    
    def test_room_expires_in_future(self, api_client, user, db):
        """测试房间过期时间在将来"""
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user,
            timeout_seconds=600,
        )
        
        # 过期时间设置为 24 小时后
        expires_at = timezone.now() + timedelta(hours=24)
        room = FriendRoom.objects.create(
            game=game,
            creator=user,
            status='waiting',
            expires_at=expires_at,
        )
        
        assert not room.is_expired()
        assert room.is_joinable()
    
    def test_cleanup_expired_rooms(self, db):
        """测试清理过期房间"""
        user = User.objects.create_user(
            username='cleanupuser',
            email='cleanup@example.com',
            password='SecurePass123'
        )
        
        # 创建 3 个过期房间
        expired_count = 0
        for i in range(3):
            game = Game.objects.create(
                game_type='friend',
                status='waiting',
                player_red=user,
                timeout_seconds=600,
            )
            room = FriendRoom.objects.create(
                game=game,
                creator=user,
                status='waiting',
                expires_at=timezone.now() - timedelta(hours=i+1),
            )
            expired_count += 1
        
        # 创建 1 个未过期房间
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user,
            timeout_seconds=600,
        )
        active_room = FriendRoom.objects.create(
            game=game,
            creator=user,
            status='waiting',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        
        # 清理过期房间
        cleaned = FriendRoom.cleanup_expired_rooms()
        
        assert cleaned == 3
        
        # 验证过期房间状态已更新
        for room in FriendRoom.objects.filter(creator=user, status='expired'):
            assert room.status == 'expired'
        
        # 验证活跃房间未受影响
        active_room.refresh_from_db()
        assert active_room.status == 'waiting'


@pytest.mark.django_db
class TestConcurrentJoinRoom:
    """测试并发加入房间"""
    
    @pytest.fixture
    def user1(self, db):
        return User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='SecurePass123'
        )
    
    @pytest.fixture
    def user2(self, db):
        return User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='SecurePass123'
        )
    
    @pytest.fixture
    def user3(self, db):
        return User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='SecurePass123'
        )
    
    @pytest.fixture
    def room(self, user1, db):
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user1,
            timeout_seconds=600,
        )
        return FriendRoom.objects.create(
            game=game,
            creator=user1,
            status='waiting',
            expires_at=timezone.now() + timedelta(hours=24),
        )
    
    def test_first_join_succeeds_second_fails(self, api_client, user2, user3, room):
        """测试第一个加入成功，第二个加入失败"""
        client2 = APIClient()
        client2.force_authenticate(user=user2)
        
        client3 = APIClient()
        client3.force_authenticate(user=user3)
        
        # 用户 2 先加入
        response2 = client2.post('/api/v1/friend/join/', 
                                {'room_code': room.room_code},
                                format='json')
        assert response2.status_code == status.HTTP_200_OK
        
        # 验证房间状态已更新
        room.refresh_from_db()
        assert room.status == 'playing'
        assert room.game.player_black == user2
        
        # 用户 3 再加入（应该失败，因为房间已满）
        response3 = client3.post('/api/v1/friend/join/',
                                {'room_code': room.room_code},
                                format='json')
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.fixture
    def api_client(self):
        return APIClient()


@pytest.mark.django_db
class TestRoomStateTransitions:
    """测试房间状态转换"""
    
    @pytest.fixture
    def user1(self, db):
        return User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='SecurePass123'
        )
    
    @pytest.fixture
    def user2(self, db):
        return User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='SecurePass123'
        )
    
    def test_waiting_to_playing_transition(self, db, user1, user2):
        """测试从 waiting 到 playing 的状态转换"""
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
            expires_at=timezone.now() + timedelta(hours=24),
        )
        
        assert room.status == 'waiting'
        assert game.status == 'waiting'
        
        # 用户 2 加入
        game.player_black = user2
        game.status = 'playing'
        game.save()
        room.start_game()
        
        room.refresh_from_db()
        game.refresh_from_db()
        
        assert room.status == 'playing'
        assert room.started_at is not None
        assert game.status == 'playing'
    
    def test_playing_to_finished_transition(self, db, user1, user2):
        """测试从 playing 到 finished 的状态转换"""
        game = Game.objects.create(
            game_type='friend',
            status='playing',
            player_red=user1,
            player_black=user2,
            timeout_seconds=600,
        )
        room = FriendRoom.objects.create(
            game=game,
            creator=user1,
            status='playing',
            expires_at=timezone.now() + timedelta(hours=24),
            started_at=timezone.now(),
        )
        
        # 结束游戏
        room.finish_game()
        
        room.refresh_from_db()
        
        assert room.status == 'finished'
        assert room.finished_at is not None
    
    def test_waiting_to_expired_transition(self, db, user1):
        """测试从 waiting 到 expired 的状态转换"""
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
            expires_at=timezone.now() - timedelta(hours=1),
        )
        
        # 清理过期房间
        FriendRoom.cleanup_expired_rooms()
        
        room.refresh_from_db()
        
        assert room.status == 'expired'
    
    def test_cannot_join_finished_room(self, db, user1, user2):
        """测试不能加入已结束的房间"""
        game = Game.objects.create(
            game_type='friend',
            status='finished',
            player_red=user1,
            player_black=user2,
            timeout_seconds=600,
        )
        room = FriendRoom.objects.create(
            game=game,
            creator=user1,
            status='finished',
            expires_at=timezone.now() + timedelta(hours=24),
            finished_at=timezone.now(),
        )
        
        assert not room.is_joinable()
        assert room.status == 'finished'
    
    def test_cannot_join_expired_room(self, db, user1, user2):
        """测试不能加入已过期的房间"""
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
            expires_at=timezone.now() - timedelta(hours=1),
        )
        
        assert not room.is_joinable()
        assert room.is_expired()
