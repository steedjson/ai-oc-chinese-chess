"""
观战 API 视图单元测试

测试 spectator_views.py 中的 API 接口
"""
import pytest
import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from games.models import Game, GameStatus
from games.spectator import Spectator, SpectatorStatus
from users.models import User


@pytest.fixture
def api_client():
    """API 客户端"""
    return APIClient()


@pytest.fixture
def test_user(db):
    """创建测试用户"""
    return User.objects.create_user(
        username='spectator_test_user',
        email='spectator_test@example.com',
        password='SecurePass123'
    )


@pytest.fixture
def test_user2(db):
    """创建第二个测试用户"""
    return User.objects.create_user(
        username='spectator_test_user2',
        email='spectator_test2@example.com',
        password='SecurePass123'
    )


@pytest.fixture
def game(db, test_user, test_user2):
    """创建测试游戏"""
    return Game.objects.create(
        game_type='online',
        status=GameStatus.PLAYING,
        red_player=test_user,
        black_player=test_user2,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        turn='w'
    )


@pytest.fixture
def auth_token(test_user):
    """获取测试用户的 token"""
    from authentication.services import TokenService
    return TokenService.generate_token(str(test_user.id))


@pytest.fixture
def auth_token2(test_user2):
    """获取第二个测试用户的 token"""
    from authentication.services import TokenService
    return TokenService.generate_token(str(test_user2.id))


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """认证的 API 客户端"""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
    return api_client


class TestSpectateAPI:
    """观战 API 测试"""
    
    def test_spectate_join_success(self, authenticated_client, game, test_user2, auth_token2):
        """测试成功加入观战"""
        # 使用 test_user2 的 token
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        
        url = f'/api/v1/games/{game.id}/spectate/'
        response = authenticated_client.post(url, {})
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'spectator' in response.data
        assert 'game_state' in response.data
        assert response.data['spectator']['game_id'] == str(game.id)
    
    def test_spectate_join_game_not_found(self, authenticated_client, auth_token2):
        """测试游戏不存在"""
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        
        fake_game_id = str(uuid.uuid4())
        url = f'/api/v1/games/{fake_game_id}/spectate/'
        response = authenticated_client.post(url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_spectate_join_finished_game(self, authenticated_client, test_user, test_user2, auth_token2):
        """测试已结束游戏不能观战"""
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        
        finished_game = Game.objects.create(
            game_type='online',
            status=GameStatus.RED_WIN,
            red_player=test_user,
            black_player=test_user2,
            fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            winner='red'
        )
        
        url = f'/api/v1/games/{finished_game.id}/spectate/'
        response = authenticated_client.post(url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_spectate_join_player_cannot_spectate(self, authenticated_client, game):
        """测试游戏参与者不能观战"""
        # test_user 是红方玩家
        url = f'/api/v1/games/{game.id}/spectate/'
        response = authenticated_client.post(url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_spectate_join_anonymous(self, authenticated_client, game, auth_token2):
        """测试匿名观战"""
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        
        url = f'/api/v1/games/{game.id}/spectate/'
        response = authenticated_client.post(url, {'is_anonymous': True})
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['spectator']['is_anonymous'] is True
    
    def test_spectate_leave_success(self, authenticated_client, game, auth_token2):
        """测试成功离开观战"""
        # 先加入
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        join_url = f'/api/v1/games/{game.id}/spectate/'
        authenticated_client.post(join_url, {})
        
        # 离开
        leave_url = f'/api/v1/games/{game.id}/spectate/leave/'
        response = authenticated_client.post(leave_url, {})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'duration' in response.data
    
    def test_spectate_leave_not_watching(self, authenticated_client, game):
        """测试未观战时离开"""
        url = f'/api/v1/games/{game.id}/spectate/leave/'
        response = authenticated_client.post(url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_spectate_get_spectators(self, authenticated_client, game, test_user2, auth_token2):
        """测试获取观战列表"""
        # test_user2 加入观战
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        join_url = f'/api/v1/games/{game.id}/spectate/'
        authenticated_client.post(join_url, {})
        
        # 获取观战列表
        spectators_url = f'/api/v1/games/{game.id}/spectators/'
        response = authenticated_client.get(spectators_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'spectators' in response.data
        assert response.data['count'] >= 1
    
    def test_spectate_get_spectators_with_limit(self, authenticated_client, game, auth_token2):
        """测试获取观战列表带限制"""
        url = f'/api/v1/games/{game.id}/spectators/?limit=5'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_spectate_kick_success(self, authenticated_client, game, test_user2, auth_token2):
        """测试踢出观战者"""
        # test_user2 加入观战
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        join_url = f'/api/v1/games/{game.id}/spectate/'
        join_response = authenticated_client.post(join_url, {})
        spectator_id = join_response.data['spectator']['id']
        
        # test_user（创建者）踢出
        url = f'/api/v1/games/{game.id}/spectators/kick/'
        response = authenticated_client.post(url, {'spectator_id': spectator_id})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_spectate_kick_no_permission(self, authenticated_client, game, test_user2, auth_token2):
        """测试无权限踢出观战者"""
        # test_user2 加入观战
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        join_url = f'/api/v1/games/{game.id}/spectate/'
        join_response = authenticated_client.post(join_url, {})
        spectator_id = join_response.data['spectator']['id']
        
        # 创建第三个用户
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='SecurePass123'
        )
        from authentication.services import TokenService
        token3 = TokenService.generate_token(str(user3.id))
        
        # user3 尝试踢人
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token3}')
        url = f'/api/v1/games/{game.id}/spectators/kick/'
        response = authenticated_client.post(url, {'spectator_id': spectator_id})
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
    
    def test_spectate_kick_missing_id(self, authenticated_client, game):
        """测试踢出时缺少 spectator_id"""
        url = f'/api/v1/games/{game.id}/spectators/kick/'
        response = authenticated_client.post(url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False


class TestActiveGamesAPI:
    """活跃游戏 API 测试"""
    
    def test_get_active_games(self, authenticated_client, game):
        """测试获取活跃游戏列表"""
        url = '/api/v1/spectator/active-games/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'games' in response.data
    
    def test_get_active_games_with_limit(self, authenticated_client):
        """测试获取活跃游戏列表带限制"""
        url = '/api/v1/spectator/active-games/?limit=10'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_active_games_only_playing(self, authenticated_client, test_user, test_user2):
        """测试只返回进行中的游戏"""
        # 创建已结束的游戏
        finished_game = Game.objects.create(
            game_type='online',
            status=GameStatus.RED_WIN,
            red_player=test_user,
            black_player=test_user2,
            fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            winner='red'
        )
        
        url = '/api/v1/spectator/active-games/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # 已结束的游戏不应该出现在列表中
        game_ids = [g['id'] for g in response.data['games']]
        assert str(finished_game.id) not in game_ids


class TestSpectatorInfoAPI:
    """观战者信息 API 测试"""
    
    def test_get_spectator_info_self(self, authenticated_client, game, auth_token2, test_user2):
        """测试获取自己的观战信息"""
        # 先加入观战
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        join_url = f'/api/v1/games/{game.id}/spectate/'
        join_response = authenticated_client.post(join_url, {})
        spectator_id = join_response.data['spectator']['id']
        
        # 获取信息
        info_url = f'/api/v1/games/{game.id}/spectators/{spectator_id}/'
        response = authenticated_client.get(info_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['id'] == str(test_user2.id)
    
    def test_get_spectator_info_not_found(self, authenticated_client, game):
        """测试观战者不存在"""
        fake_spectator_id = str(uuid.uuid4())
        url = f'/api/v1/games/{game.id}/spectators/{fake_spectator_id}/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_spectator_info_no_permission(self, authenticated_client, game, test_user2, auth_token2):
        """测试无权限查看他人观战信息"""
        # test_user2 加入观战
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token2}')
        join_url = f'/api/v1/games/{game.id}/spectate/'
        join_response = authenticated_client.post(join_url, {})
        spectator_id = join_response.data['spectator']['id']
        
        # 创建第三个用户
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='SecurePass123'
        )
        from authentication.services import TokenService
        token3 = TokenService.generate_token(str(user3.id))
        
        # user3 尝试查看
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token3}')
        info_url = f'/api/v1/games/{game.id}/spectators/{spectator_id}/'
        response = authenticated_client.get(info_url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSpectatorAuthentication:
    """观战认证测试"""
    
    def test_spectate_without_auth(self, api_client, game):
        """测试未认证用户不能观战"""
        url = f'/api/v1/games/{game.id}/spectate/'
        response = api_client.post(url, {})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_spectate_with_invalid_token(self, api_client, game):
        """测试无效 token"""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        url = f'/api/v1/games/{game.id}/spectate/'
        response = api_client.post(url, {})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
