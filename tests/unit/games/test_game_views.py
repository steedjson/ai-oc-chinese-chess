"""
游戏 API 视图测试
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.utils import timezone
from games.models import Game

User = get_user_model()


@pytest.mark.django_db
class TestGameListAPI:
    """游戏列表 API 测试"""

    def test_list_games_success(self):
        """测试获取游戏列表成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        # 创建测试游戏
        Game.objects.create(
            red_player=user,
            game_type='single',
            status='playing'
        )
        Game.objects.create(
            red_player=user,
            game_type='multiplayer',
            status='pending'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 2

    def test_list_games_unauthenticated(self):
        """测试未认证用户获取游戏列表"""
        url = reverse('game-list')
        response = APIClient().get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_games_filter_by_status(self):
        """测试按状态筛选游戏"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        Game.objects.create(
            red_player=user,
            game_type='single',
            status='playing'
        )
        Game.objects.create(
            red_player=user,
            game_type='single',
            status='finished'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-list')
        response = client.get(url, {'status': 'playing'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == 'playing'


@pytest.mark.django_db
class TestGameCreateAPI:
    """创建游戏 API 测试"""

    def test_create_single_game_success(self):
        """测试创建单机游戏成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-create')
        data = {
            'game_type': 'single',
            'time_control': {
                'initial_time': 600,
                'increment': 5
            }
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['game_type'] == 'single'
        assert response.data['data']['status'] == 'playing'
        
        # 验证游戏已创建
        assert Game.objects.filter(red_player=user).exists()

    def test_create_multiplayer_game_success(self):
        """测试创建多人游戏成功"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user1)
        
        url = reverse('game-create')
        data = {
            'game_type': 'multiplayer',
            'black_player_id': str(user2.id),
            'time_control': {
                'initial_time': 600,
                'increment': 5
            }
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['game_type'] == 'multiplayer'
        assert response.data['data']['black_player']['user_id'] == str(user2.id)

    def test_create_multiplayer_game_self(self):
        """测试创建与自己对战的多人游戏"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-create')
        data = {
            'game_type': 'multiplayer',
            'black_player_id': str(user.id)
        }
        
        response = client.post(url, data, format='json')
        
        # 根据实际实现，可能允许或拒绝
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]

    def test_create_multiplayer_game_user_not_found(self):
        """测试创建多人游戏时对手不存在"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-create')
        data = {
            'game_type': 'multiplayer',
            'black_player_id': '00000000-0000-0000-0000-000000000000'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestGameRetrieveAPI:
    """获取游戏详情 API 测试"""

    def test_retrieve_game_success(self):
        """测试获取游戏详情成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='playing'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-detail', kwargs={'pk': game.id})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['game_id'] == str(game.id)

    def test_retrieve_game_not_found(self):
        """测试获取不存在的游戏"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_game_unauthorized(self):
        """测试无权查看他人游戏"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user1,
            game_type='single',
            status='playing'
        )
        
        client = APIClient()
        client.force_authenticate(user=user2)
        
        url = reverse('game-detail', kwargs={'pk': game.id})
        response = client.get(url)
        
        # 根据实际实现，可能返回 403 或 404
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
class TestGameMoveAPI:
    """游戏走棋 API 测试"""

    def test_make_move_success(self):
        """测试走棋成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='playing',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-move', kwargs={'pk': game.id})
        data = {
            'from_pos': 'h0',
            'to_pos': 'h2'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'move' in response.data
        assert 'fen' in response.data

    def test_make_move_not_your_turn(self):
        """测试非己方回合走棋"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        # 创建黑方回合的游戏
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='playing',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1',
            turn='b'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-move', kwargs={'pk': game.id})
        data = {
            'from_pos': 'h0',
            'to_pos': 'h2'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == '不是你的回合'

    def test_make_move_invalid_move(self):
        """测试无效走棋"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='playing'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-move', kwargs={'pk': game.id})
        data = {
            'from_pos': 'e0',
            'to_pos': 'e9'  # 无效走棋
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == '无效走棋'

    def test_make_move_game_not_playing(self):
        """测试未进行中的游戏走棋"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='finished'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-move', kwargs={'pk': game.id})
        data = {
            'from_pos': 'h0',
            'to_pos': 'h2'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == '游戏未进行中'


@pytest.mark.django_db
class TestGameStatusAPI:
    """游戏状态更新 API 测试"""

    def test_update_game_status_success(self):
        """测试更新游戏状态成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='playing'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-status', kwargs={'pk': game.id})
        data = {
            'status': 'red_win'
        }
        
        response = client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'red_win'
        
        # 验证游戏已结束
        game.refresh_from_db()
        assert game.status == 'red_win'
        assert game.finished_at is not None

    def test_update_game_status_invalid(self):
        """测试更新为无效状态"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='playing'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-status', kwargs={'pk': game.id})
        data = {
            'status': 'invalid_status'
        }
        
        response = client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestGameDestroyAPI:
    """取消游戏 API 测试"""

    def test_cancel_game_success(self):
        """测试取消游戏成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='pending'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-detail', kwargs={'pk': game.id})
        response = client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 验证游戏已取消
        game.refresh_from_db()
        assert game.status == 'aborted'
        assert game.finished_at is not None

    def test_cancel_finished_game(self):
        """测试取消已结束的游戏"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='finished'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-detail', kwargs={'pk': game.id})
        response = client.delete(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
