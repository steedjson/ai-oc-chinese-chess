"""
User Service 测试
测试用户服务层核心功能：用户详情、密码修改、用户统计、对局历史
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from rest_framework.test import APIClient
from rest_framework import status


# ==================== UserDetailView 测试 ====================

class TestUserDetailView:
    """用户详情视图测试"""
    
    @pytest.fixture
    def api_client(self):
        """创建 API 客户端"""
        return APIClient()
    
    @pytest.fixture
    def mock_user(self):
        """创建 Mock 用户"""
        user = Mock()
        user.id = 1
        user.username = 'testuser'
        user.email = 'test@example.com'
        user.elo_rating = 1500
        user.avatar_url = 'https://example.com/avatar.jpg'
        user.is_active = True
        return user
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    def test_get_user_detail_success(self, mock_jwt, mock_user_model, api_client, mock_user):
        """测试成功获取用户详情"""
        # Mock 认证
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        
        # Mock 用户查询
        mock_user_model.objects.get.return_value = mock_user
        
        # 设置认证
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/1/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    def test_get_user_detail_not_found(self, mock_jwt, mock_user_model, api_client, mock_user):
        """测试用户不存在"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'USER_NOT_FOUND'
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    def test_update_user_detail_success(self, mock_jwt, mock_user_model, api_client, mock_user):
        """测试成功更新用户详情"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        # Mock serializer
        with patch('users.views.UserSerializer') as mock_serializer:
            mock_serializer_instance = Mock()
            mock_serializer_instance.is_valid.return_value = True
            mock_serializer_instance.save = Mock()
            mock_serializer_instance.data = {'username': 'newusername'}
            mock_serializer.return_value = mock_serializer_instance
            
            api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
            
            response = api_client.put('/api/users/1/', {
                'username': 'newusername',
                'email': 'new@example.com'
            })
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['success'] is True
            mock_serializer_instance.save.assert_called_once()
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    def test_update_user_detail_permission_denied(self, mock_jwt, mock_user_model, api_client, mock_user):
        """测试无权修改其他用户"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        
        other_user = Mock()
        other_user.id = 2
        mock_user_model.objects.get.return_value = other_user
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.put('/api/users/2/', {
            'username': 'hacked'
        })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'PERMISSION_DENIED'
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    def test_patch_user_detail_partial_update(self, mock_jwt, mock_user_model, api_client, mock_user):
        """测试部分更新用户详情"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        with patch('users.views.UserSerializer') as mock_serializer:
            mock_serializer_instance = Mock()
            mock_serializer_instance.is_valid.return_value = True
            mock_serializer_instance.save = Mock()
            mock_serializer_instance.data = {'username': 'testuser', 'email': 'new@example.com'}
            mock_serializer.return_value = mock_serializer_instance
            
            api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
            
            response = api_client.patch('/api/users/1/', {
                'email': 'new@example.com'
            })
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['success'] is True


# ==================== ChangePasswordView 测试 ====================

class TestChangePasswordView:
    """修改密码视图测试"""
    
    @pytest.fixture
    def api_client(self):
        """创建 API 客户端"""
        return APIClient()
    
    @pytest.fixture
    def mock_user(self):
        """创建 Mock 用户"""
        user = Mock()
        user.id = 1
        user.username = 'testuser'
        user.email = 'test@example.com'
        return user
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    @patch('users.views.AuthService')
    def test_change_password_success(self, mock_auth_service, mock_jwt, mock_user_model, api_client, mock_user):
        """测试成功修改密码"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        mock_auth_service.change_password = Mock()
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.put('/api/users/1/password/', {
            'old_password': 'oldpass123',
            'new_password': 'newpass456'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['message'] == '密码修改成功，请重新登录'
        mock_auth_service.change_password.assert_called_once()
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    @patch('users.views.AuthService')
    def test_change_password_wrong_old(self, mock_auth_service, mock_jwt, mock_user_model, api_client, mock_user):
        """测试旧密码错误"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        mock_auth_service.change_password.side_effect = Exception("WRONG_OLD_PASSWORD")
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.put('/api/users/1/password/', {
            'old_password': 'wrongpass',
            'new_password': 'newpass456'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'WRONG_OLD_PASSWORD'
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    @patch('users.views.AuthService')
    def test_change_password_same_password(self, mock_auth_service, mock_jwt, mock_user_model, api_client, mock_user):
        """测试新密码与旧密码相同"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        mock_auth_service.change_password.side_effect = Exception("SAME_PASSWORD")
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.put('/api/users/1/password/', {
            'old_password': 'samepass',
            'new_password': 'samepass'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'SAME_PASSWORD'
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    def test_change_password_permission_denied(self, mock_jwt, mock_user_model, api_client, mock_user):
        """测试无权修改其他用户密码"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        
        other_user = Mock()
        other_user.id = 2
        mock_user_model.objects.get.return_value = other_user
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.put('/api/users/2/password/', {
            'old_password': 'oldpass',
            'new_password': 'newpass'
        })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'PERMISSION_DENIED'


# ==================== UserProfileView 测试 ====================

class TestUserProfileView:
    """当前用户 Profile 视图测试"""
    
    @pytest.fixture
    def api_client(self):
        """创建 API 客户端"""
        return APIClient()
    
    @pytest.fixture
    def mock_user(self):
        """创建 Mock 用户"""
        user = Mock()
        user.id = 1
        user.username = 'testuser'
        user.email = 'test@example.com'
        user.elo_rating = 1500
        return user
    
    @patch('users.views.JWTAuthentication')
    def test_get_current_user_profile(self, mock_jwt, api_client, mock_user):
        """测试获取当前用户信息"""
        # Mock request.user
        mock_request = Mock()
        mock_request.user = mock_user
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        api_client.request.user = mock_user
        
        with patch('users.views.UserDetailSerializer') as mock_serializer:
            mock_serializer_instance = Mock()
            mock_serializer_instance.data = {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'elo_rating': 1500
            }
            mock_serializer.return_value = mock_serializer_instance
            
            response = api_client.get('/api/users/profile/')
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['success'] is True
    
    @patch('users.views.JWTAuthentication')
    def test_update_current_user_profile(self, mock_jwt, api_client, mock_user):
        """测试更新当前用户信息"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        
        with patch('users.views.UserSerializer') as mock_serializer:
            mock_serializer_instance = Mock()
            mock_serializer_instance.is_valid.return_value = True
            mock_serializer_instance.save = Mock()
            mock_serializer_instance.data = {'username': 'newusername'}
            mock_serializer.return_value = mock_serializer_instance
            
            api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
            
            response = api_client.patch('/api/users/profile/', {
                'username': 'newusername'
            })
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['success'] is True
            mock_serializer_instance.save.assert_called_once()


# ==================== UserStatsView 测试 ====================

class TestUserStatsView:
    """用户统计视图测试"""
    
    @pytest.fixture
    def api_client(self):
        """创建 API 客户端"""
        return APIClient()
    
    @pytest.fixture
    def mock_user(self):
        """创建 Mock 用户"""
        user = Mock()
        user.id = 1
        user.username = 'testuser'
        user.elo_rating = 1500
        return user
    
    @patch('users.views.User')
    @patch('users.views.Game')
    @patch('users.views.JWTAuthentication')
    def test_get_user_stats_success(self, mock_jwt, mock_game_model, mock_user_model, api_client, mock_user):
        """测试成功获取用户统计"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        # Mock 游戏统计
        mock_game_model.objects.filter.return_value.count.return_value = 100  # 总局数
        mock_game_model.objects.filter.return_value.count.side_effect = [100, 60, 30, 10]  # total, wins, losses, draws
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/1/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert response.data['data']['total_games'] == 100
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    def test_get_user_stats_not_found(self, mock_jwt, mock_user_model, api_client, mock_user):
        """测试用户不存在"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/999/stats/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
    
    @patch('users.views.User')
    @patch('users.views.Game')
    @patch('users.views.JWTAuthentication')
    def test_get_user_stats_zero_games(self, mock_jwt, mock_game_model, mock_user_model, api_client, mock_user):
        """测试零场对局"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        mock_game_model.objects.filter.return_value.count.return_value = 0
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/1/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['win_rate'] == 0.0  # 零场时胜率应为 0


# ==================== UserGamesView 测试 ====================

class TestUserGamesView:
    """用户对局历史视图测试"""
    
    @pytest.fixture
    def api_client(self):
        """创建 API 客户端"""
        return APIClient()
    
    @pytest.fixture
    def mock_user(self):
        """创建 Mock 用户"""
        user = Mock()
        user.id = 1
        user.username = 'testuser'
        user.elo_rating = 1500
        return user
    
    @pytest.fixture
    def mock_game(self):
        """创建 Mock 游戏"""
        game = Mock()
        game.id = 1
        game.red_player = None  # 将在测试中设置
        game.black_player = None
        game.winner = 'red'
        game.status = 'red_win'
        game.game_type = 'ranked'
        game.created_at = '2026-03-11T10:00:00Z'
        return game
    
    @patch('users.views.User')
    @patch('users.views.Game')
    @patch('users.views.JWTAuthentication')
    def test_get_user_games_success(self, mock_jwt, mock_game_model, mock_user_model, api_client, mock_user, mock_game):
        """测试成功获取对局历史"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        # Mock 游戏查询
        mock_queryset = Mock()
        mock_queryset.count.return_value = 50
        mock_queryset.__getitem__.return_value = [mock_game]
        mock_game_model.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/1/games/?page=1&page_size=20')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'results' in response.data['data']
        assert 'pagination' in response.data['data']
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    def test_get_user_games_not_found(self, mock_jwt, mock_user_model, api_client, mock_user):
        """测试用户不存在"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/999/games/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
    
    @patch('users.views.User')
    @patch('users.views.Game')
    @patch('users.views.JWTAuthentication')
    def test_get_user_games_pagination(self, mock_jwt, mock_game_model, mock_user_model, api_client, mock_user, mock_game):
        """测试分页功能"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        mock_queryset = Mock()
        mock_queryset.count.return_value = 150
        mock_queryset.__getitem__.return_value = [mock_game] * 20
        mock_game_model.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/1/games/?page=2&page_size=20')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['pagination']['page'] == 2
        assert response.data['data']['pagination']['page_size'] == 20
        assert response.data['data']['pagination']['total_count'] == 150
        assert response.data['data']['pagination']['total_pages'] == 8
    
    @patch('users.views.User')
    @patch('users.views.Game')
    @patch('users.views.JWTAuthentication')
    def test_get_user_games_result_win(self, mock_jwt, mock_game_model, mock_user_model, api_client, mock_user, mock_game):
        """测试胜利对局结果"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        # 设置红方玩家
        mock_game.red_player = mock_user
        mock_game.black_player = Mock(id=2, username='opponent', elo_rating=1450)
        mock_game.winner = 'red'
        
        mock_queryset = Mock()
        mock_queryset.count.return_value = 1
        mock_queryset.__getitem__.return_value = [mock_game]
        mock_game_model.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/1/games/')
        
        assert response.status_code == status.HTTP_200_OK
        game_data = response.data['data']['results'][0]
        assert game_data['result'] == 'win'
        assert game_data['is_red'] is True
    
    @patch('users.views.User')
    @patch('users.views.Game')
    @patch('users.views.JWTAuthentication')
    def test_get_user_games_result_loss(self, mock_jwt, mock_game_model, mock_user_model, api_client, mock_user, mock_game):
        """测试失败对局结果"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        # 设置红方玩家
        mock_game.red_player = mock_user
        mock_game.black_player = Mock(id=2, username='opponent', elo_rating=1550)
        mock_game.winner = 'black'  # 黑方获胜
        
        mock_queryset = Mock()
        mock_queryset.count.return_value = 1
        mock_queryset.__getitem__.return_value = [mock_game]
        mock_game_model.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/1/games/')
        
        assert response.status_code == status.HTTP_200_OK
        game_data = response.data['data']['results'][0]
        assert game_data['result'] == 'loss'
    
    @patch('users.views.User')
    @patch('users.views.Game')
    @patch('users.views.JWTAuthentication')
    def test_get_user_games_result_draw(self, mock_jwt, mock_game_model, mock_user_model, api_client, mock_user, mock_game):
        """测试平局对局结果"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        mock_game.red_player = mock_user
        mock_game.black_player = Mock(id=2, username='opponent', elo_rating=1500)
        mock_game.winner = 'draw'
        mock_game.status = 'draw'
        
        mock_queryset = Mock()
        mock_queryset.count.return_value = 1
        mock_queryset.__getitem__.return_value = [mock_game]
        mock_game_model.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/1/games/')
        
        assert response.status_code == status.HTTP_200_OK
        game_data = response.data['data']['results'][0]
        assert game_data['result'] == 'draw'
    
    @patch('users.views.User')
    @patch('users.views.Game')
    @patch('users.views.JWTAuthentication')
    def test_get_user_games_max_page_size(self, mock_jwt, mock_game_model, mock_user_model, api_client, mock_user, mock_game):
        """测试最大页面大小限制"""
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        mock_queryset = Mock()
        mock_queryset.count.return_value = 100
        mock_queryset.__getitem__.return_value = [mock_game] * 50
        mock_game_model.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        # 请求超过最大限制的页面大小
        response = api_client.get('/api/users/1/games/?page_size=200')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['pagination']['page_size'] == 100  # 限制为 100


# ==================== Edge Cases 测试 ====================

class TestUserViewsEdgeCases:
    """用户视图边界条件测试"""
    
    @pytest.fixture
    def api_client(self):
        """创建 API 客户端"""
        return APIClient()
    
    @patch('users.views.User')
    @patch('users.views.JWTAuthentication')
    def test_user_detail_invalid_user_id(self, mock_jwt, mock_user_model, api_client):
        """测试无效用户 ID"""
        mock_user = Mock()
        mock_user.id = 1
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.side_effect = ValueError("Invalid ID")
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        response = api_client.get('/api/users/invalid/')
        
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
    
    @patch('users.views.User')
    @patch('users.views.Game')
    @patch('users.views.JWTAuthentication')
    def test_user_stats_database_error(self, mock_jwt, mock_game_model, mock_user_model, api_client):
        """测试数据库错误"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.elo_rating = 1500
        mock_jwt.return_value.authenticate.return_value = (mock_user, None)
        mock_user_model.objects.get.return_value = mock_user
        
        mock_game_model.objects.filter.side_effect = Exception("Database error")
        
        api_client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        # 应该抛出异常或被处理
        with pytest.raises(Exception):
            api_client.get('/api/users/1/stats/')


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
