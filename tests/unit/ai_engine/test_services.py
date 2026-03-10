"""
AI Engine 服务测试
测试 Stockfish 引擎服务、走棋生成、局面评估等功能
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# 添加 backend 目录到路径
backend_dir = Path(__file__).resolve().parent.parent.parent / 'src' / 'backend'
sys.path.insert(0, str(backend_dir))

from ai_engine.services import StockfishService, AIMove
from ai_engine.config import get_difficulty_config


class TestAIMove:
    """AI 走棋数据类测试"""
    
    def test_aimove_creation(self):
        """测试 AIMove 实例创建"""
        move = AIMove(
            from_pos="e2",
            to_pos="e4",
            piece="P",
            evaluation=0.5,
            depth=10,
            thinking_time=100
        )
        
        assert move.from_pos == "e2"
        assert move.to_pos == "e4"
        assert move.piece == "P"
        assert move.evaluation == 0.5
        assert move.depth == 10
        assert move.thinking_time == 100
        assert move.notation == ""
    
    def test_aimove_with_notation(self):
        """测试带棋谱记号的 AIMove"""
        move = AIMove(
            from_pos="b3",
            to_pos="b5",
            piece="C",
            evaluation=-0.3,
            depth=15,
            thinking_time=250,
            notation="炮二进二"
        )
        
        assert move.notation == "炮二进二"


class TestStockfishServiceInit:
    """Stockfish 服务初始化测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_stockfish_service_init(self, mock_stockfish):
        """测试 Stockfish 服务初始化"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService(difficulty=5)
            
            assert service.difficulty == 5
            assert mock_stockfish.called
    
    @patch('ai_engine.services.Stockfish')
    def test_stockfish_service_default_difficulty(self, mock_stockfish):
        """测试默认难度等级"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            assert service.difficulty == 5
    
    @patch('ai_engine.services.Stockfish')
    def test_stockfish_service_difficulty_configs(self, mock_stockfish):
        """测试不同难度配置"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            
            # 测试低难度
            service_easy = StockfishService(difficulty=1)
            assert service_easy.difficulty == 1
            
            # 测试高难度
            service_hard = StockfishService(difficulty=10)
            assert service_hard.difficulty == 10
    
    def test_stockfish_not_installed(self):
        """测试 Stockfish 未安装的情况"""
        with patch('ai_engine.services.Stockfish', None):
            with pytest.raises(RuntimeError, match="python-stockfish 库未安装"):
                StockfishService()


class TestStockfishServiceGetBestMove:
    """Stockfish 服务获取最佳走棋测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_get_best_move(self, mock_stockfish):
        """测试获取最佳走棋"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_best_move.return_value = "e2e4"
        mock_engine.get_current_depth.return_value = 10
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            # Mock 内部方法
            service._parse_move = Mock(return_value=("e2", "e4"))
            service._get_evaluation = Mock(return_value=0.5)
            
            move = service.get_best_move("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1")
            
            assert isinstance(move, AIMove)
            assert move.from_pos == "e2"
            assert move.to_pos == "e4"
            assert move.evaluation == 0.5
            mock_engine.set_fen_position.assert_called_once()
    
    @patch('ai_engine.services.Stockfish')
    def test_get_best_move_with_time_limit(self, mock_stockfish):
        """测试带时间限制获取最佳走棋"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_best_move.return_value = "b3b5"
        mock_engine.get_current_depth.return_value = 8
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            service._parse_move = Mock(return_value=("b3", "b5"))
            service._get_evaluation = Mock(return_value=0.3)
            
            move = service.get_best_move(
                "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
                time_limit=500
            )
            
            assert isinstance(move, AIMove)
            # 验证使用了自定义时间限制
            mock_engine.get_best_move.assert_called_with(time=500)


class TestStockfishServiceHelpers:
    """Stockfish 服务辅助方法测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_parse_move_standard(self, mock_stockfish):
        """测试解析标准走棋"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            from_pos, to_pos = service._parse_move("e2e4")
            assert from_pos == "e2"
            assert to_pos == "e4"
    
    @patch('ai_engine.services.Stockfish')
    def test_parse_move_castling(self, mock_stockfish):
        """测试解析王车易位走棋"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            # 国际象棋王车易位（虽然中国象棋没有，但测试代码健壮性）
            from_pos, to_pos = service._parse_move("e1g1")
            assert from_pos == "e1"
            assert to_pos == "g1"
    
    @patch('ai_engine.services.Stockfish')
    def test_get_evaluation_positive(self, mock_stockfish):
        """测试获取正数评估分数"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_evaluation.return_value = "+50"
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            evaluation = service._get_evaluation()
            assert evaluation == 0.5  # 50 厘 = 0.5
    
    @patch('ai_engine.services.Stockfish')
    def test_get_evaluation_negative(self, mock_stockfish):
        """测试获取负数评估分数"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_evaluation.return_value = "-120"
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            evaluation = service._get_evaluation()
            assert evaluation == -1.2  # -120 厘 = -1.2
    
    @patch('ai_engine.services.Stockfish')
    def test_get_evaluation_mate(self, mock_stockfish):
        """测试获取将死评估分数"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_evaluation.return_value = "Mate +3"
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            evaluation = service._get_evaluation()
            assert evaluation == 10.0  # 将死返回最大评估
    
    @patch('ai_engine.services.Stockfish')
    def test_get_evaluation_mate_negative(self, mock_stockfish):
        """测试获取负数将死评估分数"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_evaluation.return_value = "Mate -2"
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            evaluation = service._get_evaluation()
            assert evaluation == -10.0  # 被将死返回最小评估


class TestStockfishServiceAdditionalMethods:
    """Stockfish 服务其他方法测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_get_top_moves(self, mock_stockfish):
        """测试获取多个最佳走棋"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_top_moves.return_value = ["e2e4", "d2d4", "b3b5"]
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            service._parse_move = Mock(return_value=("e2", "e4"))
            service._get_evaluation = Mock(return_value=0.5)
            
            top_moves = service.get_top_moves(
                "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
                num_moves=3
            )
            
            assert len(top_moves) == 3
            assert all(isinstance(move, AIMove) for move in top_moves)
    
    @patch('ai_engine.services.Stockfish')
    def test_is_game_over(self, mock_stockfish):
        """测试游戏结束检测"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            # 测试非结束局面
            mock_engine.is_move_correct.return_value = True
            result = service.is_game_over(
                "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
            )
            assert result is False
    
    @patch('ai_engine.services.Stockfish')
    def test_validate_move(self, mock_stockfish):
        """测试走棋验证"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.is_move_correct.return_value = True
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            is_valid = service.validate_move(
                "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
                "e2e4"
            )
            
            assert is_valid is True
            mock_engine.is_move_correct.assert_called_once()
    
    @patch('ai_engine.services.Stockfish')
    def test_validate_invalid_move(self, mock_stockfish):
        """测试无效走棋验证"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.is_move_correct.return_value = False
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            is_valid = service.validate_move(
                "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
                "e2e9"  # 无效走棋
            )
            
            assert is_valid is False


class TestDifficultyConfig:
    """难度配置测试"""
    
    def test_get_difficulty_config_valid(self):
        """测试获取有效难度配置"""
        for difficulty in range(1, 11):
            config = get_difficulty_config(difficulty)
            assert config is not None
            assert config.difficulty == difficulty
    
    def test_get_difficulty_config_default(self):
        """测试默认难度配置"""
        config = get_difficulty_config()
        assert config.difficulty == 5
    
    def test_get_difficulty_config_bounds(self):
        """测试难度边界"""
        # 最低难度
        config_min = get_difficulty_config(1)
        assert config_min.difficulty == 1
        
        # 最高难度
        config_max = get_difficulty_config(10)
        assert config_max.difficulty == 10
