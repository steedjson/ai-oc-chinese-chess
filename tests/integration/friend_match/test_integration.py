"""
好友对战集成测试

测试完整的用户流程和关键路径
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from django.utils import timezone
import time

from games.models import FriendRoom, Game

User = get_user_model()


@pytest.mark.django_db
class TestFullGameFlow:
    """测试完整游戏流程：创建→加入→开始→结束"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user1(self, db):
        return User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='SecurePass123'
        )
    
    @pytest.fixture
    def user2(self, db):
        return User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='SecurePass123'
        )
    
    def test_full_create_join_play_flow(self, api_client, user1, user2):
        """测试完整的创建 - 加入 - 游戏流程"""
        # 步骤 1: 用户 1 创建房间
        api_client.force_authenticate(user=user1)
        create_response = api_client.post('/api/v1/friend/create/',
                                         {'time_control': 600, 'is_rated': False},
                                         format='json')
        
        assert create_response.status_code == status.HTTP_201_CREATED
        room_code = create_response.data['room_code']
        assert room_code.startswith('CHESS')
        
        # 步骤 2: 用户 1 获取房间详情
        status_response = api_client.get(f'/api/v1/friend/{room_code}/')
        assert status_response.status_code == status.HTTP_200_OK
        assert status_response.data['status'] == 'waiting'
        assert status_response.data['creator_username'] == 'player1'
        
        # 步骤 3: 用户 2 加入房间
        api_client.force_authenticate(user=user2)
        join_response = api_client.post('/api/v1/friend/join/',
                                       {'room_code': room_code},
                                       format='json')
        
        assert join_response.status_code == status.HTTP_200_OK
        assert join_response.data['message'] == '加入成功'
        assert join_response.data['your_color'] == 'black'
        
        # 步骤 4: 验证房间状态已更新
        room = FriendRoom.objects.get(room_code=room_code)
        assert room.status == 'playing'
        assert room.started_at is not None
        assert room.game.status == 'playing'
        assert room.game.player_red == user1
        assert room.game.player_black == user2
        
        # 步骤 5: 双方都可以查询房间状态
        api_client.force_authenticate(user=user1)
        red_status = api_client.get(f'/api/v1/friend/{room_code}/')
        assert red_status.status_code == status.HTTP_200_OK
        assert red_status.data['status'] == 'playing'
        
        api_client.force_authenticate(user=user2)
        black_status = api_client.get(f'/api/v1/friend/{room_code}/')
        assert black_status.status_code == status.HTTP_200_OK
        assert black_status.data['status'] == 'playing'
    
    def test_create_room_and_get_invite_link(self, api_client, user1):
        """测试创建房间并获取邀请链接"""
        api_client.force_authenticate(user=user1)
        
        response = api_client.post('/api/v1/friend/create/',
                                  {'time_control': 600},
                                  format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'invite_link' in response.data
        
        invite_link = response.data['invite_link']
        assert response.data['room_code'] in invite_link
        assert '/games/friend/join/' in invite_link
    
    def test_multiple_users_try_to_join_same_room(self, api_client, user1, user2, db):
        """测试多个用户尝试加入同一个房间"""
        # 创建房间
        api_client.force_authenticate(user=user1)
        create_response = api_client.post('/api/v1/friend/create/',
                                         {'time_control': 600},
                                         format='json')
        room_code = create_response.data['room_code']
        
        # 创建第三个用户
        user3 = User.objects.create_user(
            username='player3',
            email='player3@example.com',
            password='SecurePass123'
        )
        
        # 用户 2 加入
        api_client.force_authenticate(user=user2)
        join_response2 = api_client.post('/api/v1/friend/join/',
                                        {'room_code': room_code},
                                        format='json')
        assert join_response2.status_code == status.HTTP_200_OK
        
        # 用户 3 尝试加入（应该失败）
        api_client.force_authenticate(user=user3)
        join_response3 = api_client.post('/api/v1/friend/join/',
                                        {'room_code': room_code},
                                        format='json')
        assert join_response3.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRoomExpirationCleanup:
    """测试房间过期自动清理"""
    
    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123'
        )
    
    def test_cleanup_expired_rooms(self, db, user):
        """测试清理过期房间"""
        # 创建 3 个过期房间
        for i in range(3):
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
                expires_at=timezone.now() - timedelta(hours=i+1),
            )
        
        # 创建 2 个活跃房间
        for i in range(2):
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
        
        # 清理过期房间
        cleaned_count = FriendRoom.cleanup_expired_rooms()
        
        assert cleaned_count == 3
        
        # 验证过期房间状态
        expired_rooms = FriendRoom.objects.filter(status='expired')
        assert expired_rooms.count() == 3
        
        # 验证活跃房间未受影响
        active_rooms = FriendRoom.objects.filter(status='waiting')
        assert active_rooms.count() == 2
    
    def test_expired_room_not_joinable(self, db, user):
        """测试过期房间不可加入"""
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
            expires_at=timezone.now() - timedelta(hours=1),
        )
        
        assert not room.is_joinable()
        assert room.is_expired()
    
    def test_room_expires_at_boundary(self, db, user):
        """测试房间过期时间边界"""
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user,
            timeout_seconds=600,
        )
        
        # 创建刚好未过期的房间
        room_not_expired = FriendRoom.objects.create(
            game=game,
            creator=user,
            status='waiting',
            expires_at=timezone.now() + timedelta(seconds=1),
        )
        
        assert not room_not_expired.is_expired()
        assert room_not_expired.is_joinable()


@pytest.mark.django_db
class TestMultipleRoomsConcurrent:
    """测试多个房间并发操作"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
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
    
    def test_create_multiple_rooms_same_user(self, api_client, user1):
        """测试同一用户创建多个房间"""
        api_client.force_authenticate(user=user1)
        
        room_codes = []
        for i in range(5):
            response = api_client.post('/api/v1/friend/create/',
                                      {'time_control': 600 + i * 100},
                                      format='json')
            assert response.status_code == status.HTTP_201_CREATED
            room_codes.append(response.data['room_code'])
        
        # 验证所有房间号唯一
        assert len(set(room_codes)) == 5
        
        # 验证用户有 5 个房间
        rooms = FriendRoom.objects.filter(creator=user1)
        assert rooms.count() == 5
    
    def test_multiple_rooms_parallel_operations(self, api_client, user1, user2, user3, db):
        """测试多个房间并行操作"""
        # 创建 3 个房间
        api_client.force_authenticate(user=user1)
        room1_resp = api_client.post('/api/v1/friend/create/',
                                    {'time_control': 600},
                                    format='json')
        
        api_client.force_authenticate(user=user2)
        room2_resp = api_client.post('/api/v1/friend/create/',
                                    {'time_control': 900},
                                    format='json')
        
        api_client.force_authenticate(user=user3)
        room3_resp = api_client.post('/api/v1/friend/create/',
                                    {'time_control': 1200},
                                    format='json')
        
        room1_code = room1_resp.data['room_code']
        room2_code = room2_resp.data['room_code']
        room3_code = room3_resp.data['room_code']
        
        # 验证所有房间都创建成功
        assert FriendRoom.objects.filter(room_code=room1_code).exists()
        assert FriendRoom.objects.filter(room_code=room2_code).exists()
        assert FriendRoom.objects.filter(room_code=room3_code).exists()
        
        # 验证房间配置不同
        room1 = FriendRoom.objects.get(room_code=room1_code)
        room2 = FriendRoom.objects.get(room_code=room2_code)
        room3 = FriendRoom.objects.get(room_code=room3_code)
        
        assert room1.game.timeout_seconds == 600
        assert room2.game.timeout_seconds == 900
        assert room3.game.timeout_seconds == 1200
    
    def test_my_rooms_returns_correct_rooms(self, api_client, user1, user2, db):
        """测试我的房间列表返回正确的房间"""
        # 用户 1 创建 3 个房间
        api_client.force_authenticate(user=user1)
        for i in range(3):
            api_client.post('/api/v1/friend/create/',
                           {'time_control': 600},
                           format='json')
        
        # 用户 2 创建 2 个房间
        api_client.force_authenticate(user=user2)
        for i in range(2):
            api_client.post('/api/v1/friend/create/',
                           {'time_control': 600},
                           format='json')
        
        # 用户 1 获取自己的房间
        api_client.force_authenticate(user=user1)
        my_rooms_resp = api_client.get('/api/v1/friend/my-rooms/')
        
        assert my_rooms_resp.status_code == status.HTTP_200_OK
        assert len(my_rooms_resp.data) == 3
        
        for room in my_rooms_resp.data:
            assert room['creator_username'] == 'user1'
        
        # 用户 2 获取自己的房间
        api_client.force_authenticate(user=user2)
        my_rooms_resp2 = api_client.get('/api/v1/friend/my-rooms/')
        
        assert my_rooms_resp2.status_code == status.HTTP_200_OK
        assert len(my_rooms_resp2.data) == 2
        
        for room in my_rooms_resp2.data:
            assert room['creator_username'] == 'user2'
    
    def test_active_rooms_shows_all_waiting_rooms(self, api_client, user1, user2, db):
        """测试活跃房间列表显示所有等待中的房间"""
        # 创建 3 个等待中的房间
        api_client.force_authenticate(user=user1)
        api_client.post('/api/v1/friend/create/', {'time_control': 600}, format='json')
        api_client.post('/api/v1/friend/create/', {'time_control': 600}, format='json')
        
        api_client.force_authenticate(user=user2)
        api_client.post('/api/v1/friend/create/', {'time_control': 600}, format='json')
        
        # 获取活跃房间
        api_client.force_authenticate(user=user1)
        active_resp = api_client.get('/api/v1/friend/active-rooms/')
        
        assert active_resp.status_code == status.HTTP_200_OK
        assert len(active_resp.data) == 3
        
        # 所有房间都应该是 waiting 状态
        for room in active_resp.data:
            assert room['status'] == 'waiting'


@pytest.mark.django_db
class TestEdgeCasesIntegration:
    """测试边界情况集成"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
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
    
    def test_room_code_case_insensitive_join(self, api_client, user1, user2, db):
        """测试房间号大小写不敏感加入"""
        # 创建房间
        api_client.force_authenticate(user=user1)
        create_resp = api_client.post('/api/v1/friend/create/',
                                     {'time_control': 600},
                                     format='json')
        room_code = create_resp.data['room_code']
        
        # 使用小写房间号加入
        api_client.force_authenticate(user=user2)
        join_resp = api_client.post('/api/v1/friend/join/',
                                   {'room_code': room_code.lower()},
                                   format='json')
        
        assert join_resp.status_code == status.HTTP_200_OK
        
        # 验证加入成功
        room = FriendRoom.objects.get(room_code=room_code)
        assert room.status == 'playing'
        assert room.game.player_black == user2
    
    def test_room_query_after_join(self, api_client, user1, user2, db):
        """测试加入后查询房间"""
        # 创建房间
        api_client.force_authenticate(user=user1)
        create_resp = api_client.post('/api/v1/friend/create/',
                                     {'time_control': 600},
                                     format='json')
        room_code = create_resp.data['room_code']
        
        # 用户 2 加入
        api_client.force_authenticate(user=user2)
        join_resp = api_client.post('/api/v1/friend/join/',
                                   {'room_code': room_code},
                                   format='json')
        assert join_resp.status_code == status.HTTP_200_OK
        
        # 用户 2 查询房间
        query_resp = api_client.get(f'/api/v1/friend/{room_code}/')
        assert query_resp.status_code == status.HTTP_200_OK
        assert query_resp.data['status'] == 'playing'
        
        # 用户 1 查询房间
        api_client.force_authenticate(user=user1)
        query_resp2 = api_client.get(f'/api/v1/friend/{room_code}/')
        assert query_resp2.status_code == status.HTTP_200_OK
        assert query_resp2.data['status'] == 'playing'
    
    def test_room_with_default_settings(self, api_client, user1):
        """测试使用默认设置创建房间"""
        api_client.force_authenticate(user=user1)
        
        response = api_client.post('/api/v1/friend/create/',
                                  {},
                                  format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        room = FriendRoom.objects.get(room_code=response.data['room_code'])
        assert room.game.timeout_seconds == 600  # 默认值
        assert room.game.is_rated == False  # 默认值
    
    def test_room_with_custom_settings(self, api_client, user1):
        """测试使用自定义设置创建房间"""
        api_client.force_authenticate(user=user1)
        
        response = api_client.post('/api/v1/friend/create/',
                                  {'time_control': 1800, 'is_rated': True},
                                  format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        room = FriendRoom.objects.get(room_code=response.data['room_code'])
        assert room.game.timeout_seconds == 1800
        assert room.game.is_rated == True
