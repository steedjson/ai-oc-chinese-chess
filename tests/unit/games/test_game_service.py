"""
Game Service 测试
测试游戏服务层核心功能：走棋处理、游戏状态管理、将死/困毙检测
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime

# 添加 backend 目录到路径
backend_dir = Path(__file__).resolve().parent.parent.parent.parent / 'src' / 'backend'
sys.path.insert(0, str(backend_dir))

from games.services.game_service import GameService
from games.models import Game, GameStatus


@pytest.fixture
def game_service():
    """创建 GameService 实例"""
    return GameService()


@pytest.fixture
def mock_game():
    """创建 Mock 游戏对象"""
    game = Mock(spec=Game)
    game.id = 1
    game.fen_current = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
    game.turn = 'w'
    game.move_count = 0
    game.status = GameStatus.PLAYING
    game.game_type = 'ranked'
    game.red_player_id = 1
    game.black_player_id = 2
    game.finished_at = None
    return game


@pytest.fixture
def mock_board():
    """创建 Mock 棋盘对象"""
    board = Mock()
    board.turn = 'w'
    board.to_fen.return_value = 'new_fen_after_move'
    return board


class TestGameServiceInit:
    """GameService 初始化测试"""
    
    def test_service_initialization(self, game_service):
        """测试服务初始化"""
        assert game_service is not None
        assert game_service.checkmate_detector is not None
        assert game_service.stalemate_detector is not None


class TestMakeMove:
    """走棋功能测试"""
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_make_move_success(self, mock_board_class, mock_game_model, game_service, mock_game, mock_board):
        """测试成功走棋"""
        # 设置 mock
        mock_game_model.objects.get.return_value = mock_game
        mock_board_class.return_value = mock_board
        mock_board._is_legal_move.return_value = True
        mock_board.is_check.return_value = False
        mock_board.get_piece.return_value = None
        
        # Mock checkmate 和 stalemate detector
        game_service.checkmate_detector.check_checkmate = Mock(return_value=False)
        game_service.stalemate_detector.check_stalemate = Mock(return_value=False)
        
        move_data = {
            'from_pos': 'e2',
            'to_pos': 'e4',
            'piece': 'P'
        }
        
        result = game_service.make_move(1, move_data)
        
        # 验证结果
        assert result['success'] is True
        assert result['fen'] == 'new_fen_after_move'
        assert result['turn'] == 'w'
        assert result['is_check'] is False
        assert result['is_checkmate'] is False
        assert result['is_stalemate'] is False
        assert result['game_over'] is False
        
        # 验证数据库操作
        mock_game_model.objects.get.assert_called_once_with(id=1)
        mock_board_class.assert_called_once()
        mock_board._is_legal_move.assert_called_once()
        mock_board.make_move.assert_called_once()
        mock_game.save.assert_called_once()
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_make_move_illegal_move(self, mock_board_class, mock_game_model, game_service, mock_game, mock_board):
        """测试非法走棋"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board_class.return_value = mock_board
        mock_board._is_legal_move.return_value = False
        
        move_data = {
            'from_pos': 'e2',
            'to_pos': 'e5',  # 非法走棋
            'piece': 'P'
        }
        
        result = game_service.make_move(1, move_data)
        
        assert result['success'] is False
        assert result['error_code'] == 'ILLEGAL_MOVE'
        assert result['error_message'] == '非法走棋'
        
        # 不应该执行走棋
        mock_board.make_move.assert_not_called()
        mock_game.save.assert_not_called()
    
    @patch('games.services.game_service.Game')
    def test_make_move_game_not_found(self, mock_game_model, game_service):
        """测试游戏不存在"""
        mock_game_model.objects.get.side_effect = Game.DoesNotExist()
        
        move_data = {
            'from_pos': 'e2',
            'to_pos': 'e4',
            'piece': 'P'
        }
        
        result = game_service.make_move(999, move_data)
        
        assert result['success'] is False
        assert result['error_code'] == 'GAME_NOT_FOUND'
        assert result['error_message'] == '游戏不存在'
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_make_move_checkmate(self, mock_board_class, mock_game_model, game_service, mock_game, mock_board):
        """测试将死情况"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board_class.return_value = mock_board
        mock_board._is_legal_move.return_value = True
        mock_board.is_check.return_value = True
        mock_board.turn = 'b'
        mock_board.get_piece.return_value = None
        
        # Mock 将死检测
        game_service.checkmate_detector.check_checkmate = Mock(return_value=True)
        game_service.stalemate_detector.check_stalemate = Mock(return_value=False)
        
        move_data = {
            'from_pos': 'e2',
            'to_pos': 'e4',
            'piece': 'P'
        }
        
        result = game_service.make_move(1, move_data)
        
        assert result['success'] is True
        assert result['is_checkmate'] is True
        assert result['game_over'] is True
        assert result['winner'] == 'black'  # 红方走棋后将死，黑方获胜
        assert result['win_reason'] == 'checkmate'
        
        # 验证游戏状态更新
        assert mock_game.status == 'black_win'
        assert mock_game.finished_at is not None
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_make_move_stalemate(self, mock_board_class, mock_game_model, game_service, mock_game, mock_board):
        """测试困毙情况"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board_class.return_value = mock_board
        mock_board._is_legal_move.return_value = True
        mock_board.is_check.return_value = False
        mock_board.turn = 'b'
        mock_board.get_piece.return_value = None
        
        # Mock 困毙检测
        game_service.checkmate_detector.check_checkmate = Mock(return_value=False)
        game_service.stalemate_detector.check_stalemate = Mock(return_value=True)
        
        move_data = {
            'from_pos': 'e2',
            'to_pos': 'e4',
            'piece': 'P'
        }
        
        result = game_service.make_move(1, move_data)
        
        assert result['success'] is True
        assert result['is_stalemate'] is True
        assert result['game_over'] is True
        assert result['winner'] is None
        assert result['win_reason'] == 'stalemate'
        
        # 验证游戏状态更新
        assert mock_game.status == 'draw'
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_make_move_with_notation(self, mock_board_class, mock_game_model, game_service, mock_game, mock_board):
        """测试带棋谱记号的走棋"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board_class.return_value = mock_board
        mock_board._is_legal_move.return_value = True
        mock_board.is_check.return_value = False
        mock_board.get_piece.return_value = None
        mock_board.make_move = Mock()
        
        game_service.checkmate_detector.check_checkmate = Mock(return_value=False)
        game_service.stalemate_detector.check_stalemate = Mock(return_value=False)
        
        # Mock _record_move
        game_service._record_move = Mock()
        
        move_data = {
            'from_pos': 'e2',
            'to_pos': 'e4',
            'piece': 'P',
            'notation': '炮二平五'
        }
        
        result = game_service.make_move(1, move_data)
        
        assert result['success'] is True
        game_service._record_move.assert_called_once()


class TestCheckGameStatus:
    """游戏状态检查测试"""
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_check_game_status_playing(self, mock_board_class, mock_game_model, game_service, mock_game):
        """测试检查进行中的游戏状态"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board = Mock()
        mock_board.turn = 'w'
        mock_board.is_check.return_value = False
        mock_board_class.return_value = mock_board
        
        game_service.checkmate_detector.check_checkmate = Mock(return_value=False)
        game_service.stalemate_detector.check_stalemate = Mock(return_value=False)
        
        result = game_service.check_game_status(1)
        
        assert result['game_id'] == 1
        assert result['fen'] == mock_game.fen_current
        assert result['turn'] == 'w'
        assert result['is_check'] is False
        assert result['is_checkmate'] is False
        assert result['is_stalemate'] is False
        assert result['game_over'] is False
        assert result['status'] == GameStatus.PLAYING
    
    @patch('games.services.game_service.Game')
    def test_check_game_status_not_found(self, mock_game_model, game_service):
        """测试游戏不存在"""
        mock_game_model.objects.get.side_effect = Game.DoesNotExist()
        
        result = game_service.check_game_status(999)
        
        assert 'error' in result
        assert result['error'] == 'Game not found'
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_check_game_status_checkmate(self, mock_board_class, mock_game_model, game_service, mock_game, mock_board):
        """测试检查将死状态"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board.turn = 'w'
        mock_board.is_check.return_value = True
        mock_board_class.return_value = mock_board
        
        game_service.checkmate_detector.check_checkmate = Mock(return_value=True)
        game_service.stalemate_detector.check_stalemate = Mock(return_value=False)
        
        result = game_service.check_game_status(1)
        
        assert result['is_check'] is True
        assert result['is_checkmate'] is True
        assert result['game_over'] is True
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_check_game_status_stalemate(self, mock_board_class, mock_game_model, game_service, mock_game, mock_board):
        """测试检查困毙状态"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board.turn = 'w'
        mock_board.is_check.return_value = False
        mock_board_class.return_value = mock_board
        
        game_service.checkmate_detector.check_checkmate = Mock(return_value=False)
        game_service.stalemate_detector.check_stalemate = Mock(return_value=True)
        
        result = game_service.check_game_status(1)
        
        assert result['is_check'] is False
        assert result['is_checkmate'] is False
        assert result['is_stalemate'] is True
        assert result['game_over'] is True


class TestGetLegalMoves:
    """获取合法走法测试"""
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_get_legal_moves_success(self, mock_board_class, mock_game_model, game_service, mock_game):
        """测试成功获取合法走法"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board = Mock()
        mock_board.get_all_legal_moves.return_value = [
            Mock(from_pos='e2', to_pos='e4', piece='P', captured=None),
            Mock(from_pos='b2', to_pos='b4', piece='P', captured=None),
        ]
        mock_board_class.return_value = mock_board
        
        result = game_service.get_legal_moves(1)
        
        assert result['game_id'] == 1
        assert result['legal_moves_count'] == 2
        assert len(result['legal_moves']) == 2
        assert result['legal_moves'][0]['from_pos'] == 'e2'
        assert result['legal_moves'][0]['to_pos'] == 'e4'
    
    @patch('games.services.game_service.Game')
    def test_get_legal_moves_not_found(self, mock_game_model, game_service):
        """测试游戏不存在"""
        mock_game_model.objects.get.side_effect = Game.DoesNotExist()
        
        result = game_service.get_legal_moves(999)
        
        assert 'error' in result
        assert result['error'] == 'Game not found'
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_get_legal_moves_no_moves(self, mock_board_class, mock_game_model, game_service, mock_game):
        """测试没有合法走法（将死或困毙）"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board = Mock()
        mock_board.get_all_legal_moves.return_value = []
        mock_board_class.return_value = mock_board
        
        result = game_service.get_legal_moves(1)
        
        assert result['legal_moves_count'] == 0
        assert result['legal_moves'] == []


class TestRecordMove:
    """记录走棋历史测试"""
    
    @patch('games.services.game_service.GameMove')
    def test_record_move_success(self, mock_gamemodel_model, game_service, mock_game):
        """测试成功记录走棋"""
        mock_move = Mock()
        mock_move.from_pos = 'e2'
        mock_move.to_pos = 'e4'
        mock_move.piece = 'P'
        mock_move.captured = None
        
        game_service._record_move(mock_game, mock_move, '炮二平五')
        
        mock_gamemodel_model.objects.create.assert_called_once_with(
            game=mock_game,
            move_number=mock_game.move_count + 1,
            piece='P',
            from_pos='e2',
            to_pos='e4',
            captured=None,
            notation='炮二平五'
        )
    
    @patch('games.services.game_service.GameMove')
    def test_record_move_empty_notation(self, mock_gamemodel_model, game_service, mock_game):
        """测试空棋谱记号时自动生成"""
        mock_move = Mock()
        mock_move.from_pos = 'e2'
        mock_move.to_pos = 'e4'
        mock_move.piece = 'P'
        mock_move.captured = None
        
        game_service._record_move(mock_game, mock_move, '')
        
        call_args = mock_gamemodel_model.objects.create.call_args
        assert call_args[1]['notation'] == 'Pe2-e4'


class TestMakeMoveEdgeCases:
    """走棋边界条件测试"""
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_make_move_exception_handling(self, mock_board_class, mock_game_model, game_service, mock_game):
        """测试异常处理"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board_class.side_effect = Exception("Board initialization failed")
        
        move_data = {
            'from_pos': 'e2',
            'to_pos': 'e4',
            'piece': 'P'
        }
        
        result = game_service.make_move(1, move_data)
        
        assert result['success'] is False
        assert result['error_code'] == 'MOVE_ERROR'
        assert 'Board initialization failed' in result['error_message']
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_make_move_missing_fields(self, mock_board_class, mock_game_model, game_service, mock_game):
        """测试走棋数据缺少字段"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board = Mock()
        mock_board._is_legal_move.side_effect = KeyError("'from_pos'")
        mock_board_class.return_value = mock_board
        
        move_data = {
            'to_pos': 'e4',  # 缺少 from_pos
            'piece': 'P'
        }
        
        result = game_service.make_move(1, move_data)
        
        assert result['success'] is False
        assert result['error_code'] == 'MOVE_ERROR'
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_make_move_turn_change(self, mock_board_class, mock_game_model, game_service, mock_game, mock_board):
        """测试回合切换"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board_class.return_value = mock_board
        mock_board._is_legal_move.return_value = True
        mock_board.is_check.return_value = False
        mock_board.turn = 'b'  # 走棋后切换到黑方
        mock_board.get_piece.return_value = None
        
        game_service.checkmate_detector.check_checkmate = Mock(return_value=False)
        game_service.stalemate_detector.check_stalemate = Mock(return_value=False)
        
        move_data = {
            'from_pos': 'e2',
            'to_pos': 'e4',
            'piece': 'P'
        }
        
        result = game_service.make_move(1, move_data)
        
        assert result['turn'] == 'b'  # 回合已切换
        assert mock_game.turn == 'b'
        assert mock_game.move_count == 1


class TestMakeMoveCapture:
    """吃子场景测试"""
    
    @patch('games.services.game_service.Game')
    @patch('games.services.game_service.Board')
    def test_make_move_with_capture(self, mock_board_class, mock_game_model, game_service, mock_game, mock_board):
        """测试吃子走棋"""
        mock_game_model.objects.get.return_value = mock_game
        mock_board_class.return_value = mock_board
        mock_board._is_legal_move.return_value = True
        mock_board.is_check.return_value = False
        mock_board.get_piece.return_value = 'p'  # 吃到黑方卒
        
        game_service.checkmate_detector.check_checkmate = Mock(return_value=False)
        game_service.stalemate_detector.check_stalemate = Mock(return_value=False)
        
        move_data = {
            'from_pos': 'e2',
            'to_pos': 'e4',
            'piece': 'P'
        }
        
        result = game_service.make_move(1, move_data)
        
        assert result['success'] is True
        mock_board.get_piece.assert_called_with('e4')


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
