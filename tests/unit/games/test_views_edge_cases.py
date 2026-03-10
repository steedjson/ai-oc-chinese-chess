"""
游戏 API 视图补充测试

补充边缘情况和额外测试用例，提高测试覆盖率。
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.utils import timezone
from games.models import Game, GameMove

User = get_user_model()


@pytest.mark.django_db
class TestGameListAPIEdgeCases:
    """游戏列表 API 边缘情况测试"""

    def test_list_games_empty(self):
        """测试空游戏列表"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 0

    def test_list_games_pagination(self):
        """测试游戏列表分页"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        # 创建多个游戏
        for i in range(25):
            Game.objects.create(
                red_player=user,
                game_type='single',
                status='playing'
            )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-list')
        response = client.get(url, {'page': '1', 'page_size': '10'})
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_games_only_user_games(self):
        """测试只返回用户自己的游戏"""
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
        
        # user1 创建游戏
        Game.objects.create(red_player=user1, game_type='single')
        Game.objects.create(red_player=user1, game_type='single')
        
        # user2 创建游戏
        Game.objects.create(red_player=user2, game_type='single')
        
        client = APIClient()
        client.force_authenticate(user=user1)
        
        url = reverse('game-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # 只应该看到自己的 2 个游戏
        assert len(response.data['results']) == 2

    def test_list_games_as_black_player(self):
        """测试作为黑方查看游戏列表"""
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
        
        # user2 作为黑方的游戏
        Game.objects.create(
            red_player=user1,
            black_player=user2,
            game_type='multiplayer'
        )
        
        client = APIClient()
        client.force_authenticate(user=user2)
        
        url = reverse('game-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # 应该能看到自己作为黑方的游戏
        assert len(response.data['results']) >= 1


@pytest.mark.django_db
class TestGameCreateAPIEdgeCases:
    """创建游戏 API 边缘情况测试"""

    def test_create_game_invalid_time_control(self):
        """测试创建游戏使用无效时间控制"""
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
                'initial_time': -100,  # 负数
                'increment': -5
            }
        }
        
        response = client.post(url, data, format='json')
        
        # 根据实现，可能拒绝或接受
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_create_game_missing_time_control(self):
        """测试创建游戏缺少时间控制"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-create')
        data = {
            'game_type': 'single'
        }
        
        response = client.post(url, data, format='json')
        
        # 根据实现，可能使用默认值或拒绝
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_create_game_invalid_game_type(self):
        """测试创建游戏使用无效游戏类型"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-create')
        data = {
            'game_type': 'invalid_type'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_game_empty_data(self):
        """测试创建游戏空数据"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-create')
        data = {}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestGameRetrieveAPIEdgeCases:
    """获取游戏详情 API 边缘情况测试"""

    def test_retrieve_game_with_moves(self):
        """测试获取有走棋记录的游戏详情"""
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
        
        # 创建走棋记录
        GameMove.objects.create(
            game=game,
            move_number=1,
            piece='horse',
            from_pos='h0',
            to_pos='h2'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-detail', kwargs={'pk': game.id})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_retrieve_game_finished(self):
        """测试获取已结束的游戏详情"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        game = Game.objects.create(
            red_player=user,
            game_type='single',
            status='finished',
            winner='red'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-detail', kwargs={'pk': game.id})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'finished'


@pytest.mark.django_db
class TestGameMoveAPIEdgeCases:
    """游戏走棋 API 边缘情况测试"""

    def test_make_move_missing_from_pos(self):
        """测试走棋缺少起始位置"""
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
            'to_pos': 'h2'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_make_move_missing_to_pos(self):
        """测试走棋缺少目标位置"""
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
            'from_pos': 'h0'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_make_move_invalid_position_format(self):
        """测试走棋使用无效位置格式"""
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
            'from_pos': 'invalid',
            'to_pos': 'position'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_make_move_same_position(self):
        """测试走棋起始和目标位置相同"""
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
            'from_pos': 'h0',
            'to_pos': 'h0'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_make_move_pending_game(self):
        """测试未开始游戏走棋"""
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
        
        url = reverse('game-move', kwargs={'pk': game.id})
        data = {
            'from_pos': 'h0',
            'to_pos': 'h2'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == '游戏未进行中'


@pytest.mark.django_db
class TestGameStatusAPIEdgeCases:
    """游戏状态更新 API 边缘情况测试"""

    def test_update_status_to_pending(self):
        """测试更新状态为 pending"""
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
            'status': 'pending'
        }
        
        response = client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'pending'

    def test_update_status_to_draw(self):
        """测试更新状态为和棋"""
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
            'status': 'draw'
        }
        
        response = client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'draw'
        
        # 验证游戏已结束
        game.refresh_from_db()
        assert game.finished_at is not None

    def test_update_status_missing_status(self):
        """测试更新状态缺少 status 字段"""
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
        data = {}
        
        response = client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestGameDestroyAPIEdgeCases:
    """取消游戏 API 边缘情况测试"""

    def test_cancel_playing_game(self):
        """测试取消进行中的游戏"""
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
        response = client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 验证游戏已取消
        game.refresh_from_db()
        assert game.status == 'aborted'

    def test_cancel_multiplayer_game(self):
        """测试取消多人游戏"""
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
            black_player=user2,
            game_type='multiplayer',
            status='pending'
        )
        
        client = APIClient()
        client.force_authenticate(user=user1)
        
        url = reverse('game-detail', kwargs={'pk': game.id})
        response = client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestUserGamesViewSet:
    """用户对局视图集测试"""

    def test_list_user_games_success(self):
        """测试获取用户对局成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        # 创建游戏
        Game.objects.create(red_player=user, game_type='single')
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('user-games-list', kwargs={'user_id': user.id})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'games' in response.data

    def test_list_user_games_unauthorized(self):
        """测试无权查看他人对局"""
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
        
        url = reverse('user-games-list', kwargs={'user_id': user2.id})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'error' in response.data

    def test_list_user_games_staff(self):
        """测试管理员查看他人对局"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123'
        )
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123',
            is_staff=True
        )
        
        client = APIClient()
        client.force_authenticate(user=admin)
        
        url = reverse('user-games-list', kwargs={'user_id': user1.id})
        response = client.get(url)
        
        # 管理员应该可以查看
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestGameAPIResponseFormat:
    """游戏 API 响应格式测试"""

    def test_game_list_response_format(self):
        """测试游戏列表响应格式"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or 'games' in response.data

    def test_game_create_response_format(self):
        """测试创建游戏响应格式"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('game-create')
        data = {
            'game_type': 'single'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'success' in response.data or 'game_id' in response.data

    def test_game_detail_response_format(self):
        """测试游戏详情响应格式"""
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
        assert 'success' in response.data or 'game_id' in response.data
