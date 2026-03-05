"""
AI Engine 单元测试 - Stockfish 引擎服务测试

测试 Stockfish 引擎的初始化、走棋生成、局面评估等功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_engine.services import StockfishService, AIMove
from ai_engine.config import get_difficulty_config


class TestStockfishService:
    """Stockfish 引擎服务测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_engine_initialization(self, mock_stockfish):
        """测试引擎初始化"""
        service = StockfishService(difficulty=5)
        
        assert service is not None
        assert service.difficulty == 5
        mock_stockfish.assert_called_once()
    
    @patch('ai_engine.services.Stockfish')
    def test_engine_initialization_with_config(self, mock_stockfish):
        """测试引擎使用难度配置初始化"""
        service = StockfishService(difficulty=5)
        config = get_difficulty_config(5)
        
        # 验证 Stockfish 使用正确的参数初始化
        call_args = mock_stockfish.call_args
        assert call_args is not None
        
        # 验证参数包含 Skill Level
        params = call_args[1].get('parameters', {})
        assert 'Skill Level' in params
        assert params['Skill Level'] == config.skill_level
    
    @patch('ai_engine.services.Stockfish')
    def test_get_best_move(self, mock_stockfish_class):
        """测试获取最佳走棋"""
        # Mock Stockfish 实例
        mock_engine = MagicMock()
        mock_engine.get_best_move.return_value = "e2e4"
        mock_engine.get_evaluation.return_value = {'type': 'cp', 'value': 35}
        mock_engine.get_current_depth.return_value = 15
        mock_stockfish_class.return_value = mock_engine
        
        service = StockfishService(difficulty=5)
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        move = service.get_best_move(fen)
        
        assert move is not None
        assert isinstance(move, AIMove)
        assert move.from_pos == "e2"
        assert move.to_pos == "e4"
        mock_engine.set_fen_position.assert_called_with(fen)
        mock_engine.get_best_move.assert_called_once()
    
    @patch('ai_engine.services.Stockfish')
    def test_get_best_move_with_time_limit(self, mock_stockfish_class):
        """测试带时间限制的走棋"""
        mock_engine = MagicMock()
        mock_engine.get_best_move.return_value = "c1c4"
        mock_stockfish_class.return_value = mock_engine
        
        service = StockfishService(difficulty=5)
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        move = service.get_best_move(fen, time_limit=2000)
        
        assert move is not None
        # 验证传入了时间参数
        mock_engine.get_best_move.assert_called()
        call_kwargs = mock_engine.get_best_move.call_args[1]
        assert 'time' in call_kwargs
    
    @patch('ai_engine.services.Stockfish')
    def test_evaluate_position(self, mock_stockfish_class):
        """测试局面评估"""
        mock_engine = MagicMock()
        mock_engine.get_evaluation.return_value = {'type': 'cp', 'value': 50}
        mock_engine.get_best_move.return_value = "h2h5"
        mock_engine.get_current_depth.return_value = 18
        mock_stockfish_class.return_value = mock_engine
        
        service = StockfishService(difficulty=5)
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        evaluation = service.evaluate_position(fen, depth=18)
        
        assert evaluation is not None
        assert 'score' in evaluation
        assert evaluation['score'] == 0.5  # 50/100
        assert evaluation['depth'] == 18
        mock_engine.set_fen_position.assert_called_with(fen)
    
    @patch('ai_engine.services.Stockfish')
    def test_evaluate_position_mate(self, mock_stockfish_class):
        """测试将死局面评估"""
        mock_engine = MagicMock()
        mock_engine.get_evaluation.return_value = {'type': 'mate', 'value': 3}
        mock_stockfish_class.return_value = mock_engine
        
        service = StockfishService(difficulty=5)
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        evaluation = service.evaluate_position(fen)
        
        assert evaluation['score'] == 100.0  # 将死返回极大值
    
    @patch('ai_engine.services.Stockfish')
    def test_get_top_moves(self, mock_stockfish_class):
        """测试获取多个候选走法（用于提示）"""
        mock_engine = MagicMock()
        mock_engine.get_stockfish_major_info.return_value = [
            {'move': 'e2e4', 'score': 35, 'depth': 15},
            {'move': 'h2h5', 'score': 28, 'depth': 15},
            {'move': 'b1c3', 'score': 22, 'depth': 15},
        ]
        mock_stockfish_class.return_value = mock_engine
        
        service = StockfishService(difficulty=5)
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        top_moves = service.get_top_moves(fen, count=3)
        
        assert len(top_moves) == 3
        assert top_moves[0]['from'] == "e2"
        assert top_moves[0]['to'] == "e4"
        assert top_moves[0]['evaluation'] == 35
        assert top_moves[1]['from'] == "h2"
        assert top_moves[1]['to'] == "h5"
    
    @patch('ai_engine.services.Stockfish')
    def test_set_difficulty(self, mock_stockfish_class):
        """测试动态调整难度"""
        mock_engine = MagicMock()
        mock_stockfish_class.return_value = mock_engine
        
        service = StockfishService(difficulty=5)
        service.set_difficulty(8)
        
        assert service.difficulty == 8
        config = get_difficulty_config(8)
        mock_engine.set_skill_level.assert_called_with(config.skill_level)
    
    @patch('ai_engine.services.Stockfish')
    def test_engine_cleanup(self, mock_stockfish_class):
        """测试引擎清理"""
        mock_engine = MagicMock()
        mock_stockfish_class.return_value = mock_engine
        
        service = StockfishService(difficulty=5)
        service.cleanup()
        
        mock_engine.quit.assert_called_once()
    
    @patch('ai_engine.services.Stockfish')
    def test_parse_move_format(self, mock_stockfish_class):
        """测试走棋格式解析"""
        mock_engine = MagicMock()
        mock_engine.get_best_move.return_value = "c1c4"
        mock_stockfish_class.return_value = mock_engine
        
        service = StockfishService(difficulty=5)
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        move = service.get_best_move(fen)
        
        # 验证走棋格式正确（中国象棋坐标）
        assert len(move.from_pos) == 2
        assert len(move.to_pos) == 2
    
    @patch('ai_engine.services.Stockfish')
    def test_thinking_time_tracking(self, mock_stockfish_class):
        """测试思考时间记录"""
        mock_engine = MagicMock()
        mock_engine.get_best_move.return_value = "e2e4"
        mock_stockfish_class.return_value = mock_engine
        
        service = StockfishService(difficulty=5)
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        move = service.get_best_move(fen)
        
        assert move.thinking_time >= 0
        assert isinstance(move.thinking_time, int)


class TestAIMove:
    """AI 走棋数据类测试"""
    
    def test_aimove_creation(self):
        """测试 AIMove 创建"""
        move = AIMove(
            from_pos="e2",
            to_pos="e4",
            piece="P",
            evaluation=0.35,
            depth=15,
            thinking_time=1850
        )
        
        assert move.from_pos == "e2"
        assert move.to_pos == "e4"
        assert move.piece == "P"
        assert move.evaluation == 0.35
        assert move.depth == 15
        assert move.thinking_time == 1850
    
    def test_aimove_default_notation(self):
        """测试 AIMove 默认 notation"""
        move = AIMove(
            from_pos="c1",
            to_pos="c4",
            piece="C",
            evaluation=0.28,
            depth=14,
            thinking_time=1500
        )
        
        assert move.notation == ""  # 默认为空，需要后续填充
