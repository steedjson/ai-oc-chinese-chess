"""
悔棋功能测试

测试悔棋功能的完整流程：
- 悔棋请求
- 悔棋响应
- 悔棋执行
- 悔棋次数限制
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from games.models import Game, UndoRequest
from games.engine import Board

User = get_user_model()


class UndoRequestTestCase(TestCase):
    """悔棋请求测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        
        # 创建测试用户
        self.user_red = User.objects.create_user(
            username='red_player',
            email='red@example.com',
            password='password123'
        )
        self.user_black = User.objects.create_user(
            username='black_player',
            email='black@example.com',
            password='password123'
        )
        
        # 创建游戏
        self.game = Game.objects.create(
            player_red=self.user_red,
            player_black=self.user_black,
            game_type='friend',
            status='playing',
            undo_limit=3
        )
        
        # 创建走棋记录
        from games.models import GameMove
        self.move1 = GameMove.objects.create(
            game=self.game,
            player=self.user_red,
            move_number=1,
            piece='P',
            from_pos='e2',
            to_pos='e4',
            notation='炮二平五',
            fen_before='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
            fen_after='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1'
        )
        
        # 获取 Token
        self.token_red = Token.objects.create(user=self.user_red)
        self.token_black = Token.objects.create(user=self.user_black)
    
    def test_request_undo_success(self):
        """测试成功请求悔棋"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_red.key)
        
        response = self.client.post(f'/api/v1/games/{self.game.id}/undo/request/', {
            'undo_count': 1,
            'reason': '不小心点错了'
        })
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['reason'], '不小心点错了')
        
        # 验证悔棋请求已创建
        undo_request = UndoRequest.objects.filter(game=self.game).first()
        self.assertIsNotNone(undo_request)
        self.assertEqual(undo_request.status, 'pending')
    
    def test_request_undo_limit_reached(self):
        """测试悔棋次数达到上限"""
        # 设置已达到悔棋上限
        self.game.undo_count_red = 3
        self.game.save()
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_red.key)
        
        response = self.client.post(f'/api/v1/games/{self.game.id}/undo/request/', {
            'undo_count': 1
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['success'], False)
        self.assertIn('悔棋次数', response.data['error'])
    
    def test_respond_to_undo_accept(self):
        """测试接受悔棋请求"""
        # 先创建悔棋请求
        undo_request = UndoRequest.objects.create(
            game=self.game,
            requester=self.user_red,
            move_to_undo=self.move1,
            undo_count=1,
            reason='测试悔棋'
        )
        
        # 黑方接受悔棋
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_black.key)
        
        response = self.client.post(f'/api/v1/games/{self.game.id}/undo/respond/', {
            'request_id': undo_request.id,
            'accept': True
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['accepted'], True)
        
        # 验证悔棋请求状态已更新
        undo_request.refresh_from_db()
        self.assertEqual(undo_request.status, 'accepted')
        
        # 验证游戏状态已回退
        self.game.refresh_from_db()
        self.assertEqual(self.game.undo_count_red, 1)
    
    def test_respond_to_undo_reject(self):
        """测试拒绝悔棋请求"""
        # 先创建悔棋请求
        undo_request = UndoRequest.objects.create(
            game=self.game,
            requester=self.user_red,
            move_to_undo=self.move1,
            undo_count=1,
            reason='测试悔棋'
        )
        
        # 黑方拒绝悔棋
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_black.key)
        
        response = self.client.post(f'/api/v1/games/{self.game.id}/undo/respond/', {
            'request_id': undo_request.id,
            'accept': False
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['accepted'], False)
        
        # 验证悔棋请求状态已更新
        undo_request.refresh_from_db()
        self.assertEqual(undo_request.status, 'rejected')
        
        # 验证游戏状态未变化
        self.game.refresh_from_db()
        self.assertEqual(self.game.undo_count_red, 0)
    
    def test_cannot_respond_to_own_request(self):
        """测试玩家不能响应自己的悔棋请求"""
        # 先创建悔棋请求
        undo_request = UndoRequest.objects.create(
            game=self.game,
            requester=self.user_red,
            move_to_undo=self.move1,
            undo_count=1
        )
        
        # 红方尝试响应自己的请求
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_red.key)
        
        response = self.client.post(f'/api/v1/games/{self.game.id}/undo/respond/', {
            'request_id': undo_request.id,
            'accept': True
        })
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['success'], False)
        self.assertIn('自己的悔棋请求', response.data['error'])
    
    def test_get_undo_history(self):
        """测试获取悔棋历史"""
        # 创建多个悔棋请求
        UndoRequest.objects.create(
            game=self.game,
            requester=self.user_red,
            move_to_undo=self.move1,
            undo_count=1,
            status='accepted'
        )
        UndoRequest.objects.create(
            game=self.game,
            requester=self.user_red,
            move_to_undo=self.move1,
            undo_count=1,
            status='pending'
        )
        
        # 红方获取悔棋历史
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_red.key)
        
        response = self.client.get(f'/api/v1/games/{self.game.id}/undo/requests/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(len(response.data['data']['requests']), 2)
        self.assertEqual(response.data['data']['undo_limit'], 3)
        self.assertEqual(response.data['data']['undo_count_red'], 0)


class UndoServiceTestCase(TestCase):
    """悔棋服务测试"""
    
    def test_can_request_undo(self):
        """测试检查是否可以悔棋"""
        from games.undo_service import get_undo_service
        
        user = User.objects.create_user(username='test_user', email='test@example.com', password='password')
        game = Game.objects.create(
            player_red=user,
            player_black=None,
            game_type='ai',
            status='playing'
        )
        
        undo_service = get_undo_service()
        can_undo, reason = undo_service.can_request_undo(game, user)
        
        # 因为没有走棋记录，所以不能悔棋
        self.assertFalse(can_undo)
        self.assertEqual(reason, "没有可悔的棋")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
