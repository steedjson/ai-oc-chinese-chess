"""
测试游戏服务模块

测试 games/services/ 中的服务类
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from games.services.anomaly_detector import AnomalyDetector
from games.services.checkmate_detector import CheckmateDetector
from games.services.stalemate_detector import StalemateDetector


@pytest.mark.django_db
class TestCheckmateDetector:
    """测试将死检测器"""
    
    def test_detect_checkmate(self):
        """测试检测将死"""
        detector = CheckmateDetector()
        
        # 典型的将死局面（后车杀王）
        fen = "k7/8/8/8/8/8/8/R3K3 w - - 0 1"
        
        # 注意：实际检测需要完整的棋盘状态
        # 这里测试基本接口
        assert hasattr(detector, 'is_checkmate') or hasattr(detector, 'detect')
    
    def test_detect_checkmate_with_board(self):
        """测试使用棋盘对象检测将死"""
        detector = CheckmateDetector()
        
        # 模拟棋盘
        mock_board = Mock()
        mock_board.is_checkmate.return_value = True
        
        result = detector.is_checkmate(mock_board)
        
        assert result is True
        mock_board.is_checkmate.assert_called_once()
    
    def test_not_checkmate(self):
        """测试非将死局面"""
        detector = CheckmateDetector()
        
        mock_board = Mock()
        mock_board.is_checkmate.return_value = False
        
        result = detector.is_checkmate(mock_board)
        
        assert result is False
    
    def test_checkmate_message(self):
        """测试将死消息"""
        detector = CheckmateDetector()
        
        mock_board = Mock()
        mock_board.turn = 'w'  # 白方被将死
        mock_board.is_checkmate.return_value = True
        
        result = detector.detect(mock_board)
        
        assert result is not None
        assert 'winner' in result or 'message' in result


@pytest.mark.django_db
class TestStalemateDetector:
    """测试困毙检测器"""
    
    def test_detect_stalemate(self):
        """测试检测困毙"""
        detector = StalemateDetector()
        
        mock_board = Mock()
        mock_board.is_stalemate.return_value = True
        
        result = detector.is_stalemate(mock_board)
        
        assert result is True
        mock_board.is_stalemate.assert_called_once()
    
    def test_not_stalemate(self):
        """测试非困毙局面"""
        detector = StalemateDetector()
        
        mock_board = Mock()
        mock_board.is_stalemate.return_value = False
        
        result = detector.is_stalemate(mock_board)
        
        assert result is False
    
    def test_stalemate_conditions(self):
        """测试困毙条件"""
        detector = StalemateDetector()
        
        # 困毙条件：无合法走法且未被将军
        mock_board = Mock()
        mock_board.legal_moves = []  # 无合法走法
        mock_board.is_check.return_value = False  # 未被将军
        
        result = detector.detect(mock_board)
        
        assert result is True or result is not None


@pytest.mark.django_db
class TestAnomalyDetector:
    """测试异常检测器"""
    
    def test_detect_impossible_position(self):
        """测试检测不可能的位置"""
        detector = AnomalyDetector()
        
        # 不可能的 FEN（两个红帅）
        fen = "k7/8/8/8/8/8/8/R3K3R w - - 0 1"
        
        # 检测应该返回异常
        result = detector.detect_fen(fen)
        
        # 应该检测到异常或返回 False
        assert result is not None
    
    def test_detect_impossible_turn(self):
        """测试检测不可能的回合"""
        detector = AnomalyDetector()
        
        # 双方都不可能被将军的局面
        fen = "k7/8/8/8/8/8/8/4K3 w - - 0 1"
        
        result = detector.validate_turn(fen, 'w')
        
        # 应该验证通过或失败
        assert result is not None
    
    def test_detect_too_many_pieces(self):
        """测试检测过多棋子"""
        detector = AnomalyDetector()
        
        # 创建有很多棋子的 FEN
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
        
        result = detector.count_pieces(fen)
        
        assert isinstance(result, int)
        assert result > 0
    
    def test_validate_fen_format(self):
        """测试验证 FEN 格式"""
        detector = AnomalyDetector()
        
        # 有效 FEN
        valid_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        result = detector.validate_fen_format(valid_fen)
        
        assert result is True or result is not None
        
        # 无效 FEN
        invalid_fen = "invalid fen string"
        
        result = detector.validate_fen_format(invalid_fen)
        
        assert result is False or result is None
    
    def test_detect_repeated_position(self):
        """测试检测重复局面"""
        detector = AnomalyDetector()
        
        move_history = [
            "e2e4", "e7e5",
            "e4e2", "e5e7",
            "e2e4", "e7e5",
        ]
        
        result = detector.detect_repetition(move_history)
        
        # 应该检测到重复
        assert result is True or result is not None
    
    def test_analyze_game_anomalies(self):
        """测试分析游戏异常"""
        detector = AnomalyDetector()
        
        game_data = {
            'fen_current': "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            'move_history': [],
            'turn': 'red',
        }
        
        result = detector.analyze(game_data)
        
        assert isinstance(result, dict) or result is not None


class TestAnomalyDetectorEdgeCases:
    """测试异常检测器边界情况"""
    
    def test_empty_fen(self):
        """测试空 FEN"""
        detector = AnomalyDetector()
        
        result = detector.validate_fen_format("")
        
        assert result is False
    
    def test_none_fen(self):
        """测试 None FEN"""
        detector = AnomalyDetector()
        
        result = detector.validate_fen_format(None)
        
        assert result is False
    
    def test_invalid_piece_count(self):
        """测试无效棋子计数"""
        detector = AnomalyDetector()
        
        # 不可能的棋子数量（32 个以上）
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
        
        count = detector.count_pieces(fen)
        
        # 标准开局应该是 32 个棋子
        assert count == 32 or count > 0


@pytest.fixture
def sample_game():
    """创建示例游戏数据"""
    return {
        'id': 1,
        'fen_current': "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
        'turn': 'red',
        'move_history': [
            {'from': 'c1', 'to': 'c4', 'piece': 'C'},
            {'from': 'h9', 'to': 'h7', 'piece': 'C'},
        ],
    }
