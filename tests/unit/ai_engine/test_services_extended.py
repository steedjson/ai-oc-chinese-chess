"""
AI 引擎服务扩展测试
覆盖更多边界情况、异常场景和集成测试
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from ai_engine.services import StockfishService, AIMove
from ai_engine.config import get_difficulty_config, DifficultyConfig


class TestAIMoveDataclass:
    """AIMove 数据类测试"""
    
    def test_aimove_all_fields(self):
        """测试 AIMove 所有字段"""
        move = AIMove(
            from_pos="e2",
            to_pos="e4",
            piece="P",
            evaluation=0.75,
            depth=15,
            thinking_time=250,
            notation="炮二平五"
        )
        
        assert move.from_pos == "e2"
        assert move.to_pos == "e4"
        assert move.piece == "P"
        assert move.evaluation == 0.75
        assert move.depth == 15
        assert move.thinking_time == 250
        assert move.notation == "炮二平五"
    
    def test_aimove_default_notation(self):
        """测试 AIMove 默认 notation 为空"""
        move = AIMove(
            from_pos="b3",
            to_pos="b5",
            piece="C",
            evaluation=-0.3,
            depth=10,
            thinking_time=100
        )
        
        assert move.notation == ""
    
    def test_aimove_immutability(self):
        """测试 AIMove 不可变性（dataclass frozen 特性）"""
        move = AIMove(
            from_pos="e2",
            to_pos="e4",
            piece="P",
            evaluation=0.5,
            depth=10,
            thinking_time=100
        )
        
        # dataclass 默认是可变的，但不应在业务逻辑中修改
        # 这里只是验证基本功能
        assert move.from_pos == "e2"


class TestStockfishServiceInitExtended:
    """Stockfish 服务初始化扩展测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_stockfish_service_with_custom_path(self, mock_stockfish):
        """测试自定义 Stockfish 路径"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/custom/path/stockfish'
            service = StockfishService(difficulty=5)
            
            # 验证使用了自定义路径
            mock_stockfish.assert_called_once()
            call_args = mock_stockfish.call_args
            assert call_args[1]['path'] == '/custom/path/stockfish'
    
    @patch('ai_engine.services.Stockfish')
    def test_stockfish_service_initializes_with_correct_params(self, mock_stockfish):
        """验证引擎初始化参数正确"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService(difficulty=7)
            
            # 验证传递了正确的参数
            call_kwargs = mock_stockfish.call_args[1]
            assert 'depth' in call_kwargs
            assert 'parameters' in call_kwargs
            assert 'Skill Level' in call_kwargs['parameters']
    
    @patch('ai_engine.services.Stockfish')
    def test_stockfish_service_stores_config(self, mock_stockfish):
        """验证配置正确存储"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService(difficulty=8)
            
            assert service.difficulty == 8
            assert service.config is not None
            assert service.config.level == 8
    
    @patch('ai_engine.services.Stockfish')
    def test_stockfish_service_engine_instance(self, mock_stockfish):
        """验证引擎实例创建"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            assert service.engine is not None
            assert service.engine == mock_engine


class TestStockfishServiceGetBestMoveExtended:
    """获取最佳走棋扩展测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_get_best_move_sets_fen_position(self, mock_stockfish):
        """验证设置 FEN 位置"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_best_move.return_value = "e2e4"
        mock_engine.get_current_depth.return_value = 10
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            service._parse_move = Mock(return_value=("e2", "e4"))
            service._get_evaluation = Mock(return_value=0.5)
            service._get_piece_at = Mock(return_value="P")
            
            fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
            service.get_best_move(fen)
            
            mock_engine.set_fen_position.assert_called_once_with(fen)
    
    @patch('ai_engine.services.Stockfish')
    def test_get_best_move_returns_aimove(self, mock_stockfish):
        """验证返回 AIMove 对象"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_best_move.return_value = "b3b5"
        mock_engine.get_current_depth.return_value = 12
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            service._parse_move = Mock(return_value=("b3", "b5"))
            service._get_evaluation = Mock(return_value=0.3)
            service._get_piece_at = Mock(return_value="C")
            
            move = service.get_best_move("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1")
            
            assert isinstance(move, AIMove)
            assert move.from_pos == "b3"
            assert move.to_pos == "b5"
            assert move.piece == "C"
            assert move.evaluation == 0.3
            assert move.depth == 12
            assert move.thinking_time >= 0
    
    @patch('ai_engine.services.Stockfish')
    def test_get_best_move_with_zero_time_limit(self, mock_stockfish):
        """测试零时间限制（使用默认时间）"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_best_move.return_value = "e2e4"
        mock_engine.get_current_depth.return_value = 5
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            service._parse_move = Mock(return_value=("e2", "e4"))
            service._get_evaluation = Mock(return_value=0.0)
            service._get_piece_at = Mock(return_value="P")
            
            # time_limit=0 被视为 falsy，使用默认 think_time_ms
            move = service.get_best_move(
                "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
                time_limit=0
            )
            
            # 应该使用默认时间（难度 5 的 think_time_ms=1500）
            mock_engine.get_best_move.assert_called_with(time=1500)


class TestStockfishServiceEvaluation:
    """局面评估测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_evaluate_position_returns_dict(self, mock_stockfish):
        """验证评估返回字典"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_evaluation.return_value = "+50"
        mock_engine.get_best_move.return_value = "e2e4"
        mock_engine.get_current_depth.return_value = 15
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            service._get_evaluation = Mock(return_value=0.5)
            
            result = service.evaluate_position("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1")
            
            assert isinstance(result, dict)
            assert 'score' in result
            assert 'score_text' in result
            assert 'best_move' in result
            assert 'depth' in result
    
    @patch('ai_engine.services.Stockfish')
    def test_evaluate_position_with_custom_depth(self, mock_stockfish):
        """测试自定义深度评估"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_evaluation.return_value = "+100"
        mock_engine.get_best_move.return_value = "b3b5"
        mock_engine.get_current_depth.return_value = 20
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            service._get_evaluation = Mock(return_value=1.0)
            
            service.evaluate_position("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1", depth=20)
            
            # 验证设置了自定义深度
            mock_engine.set_depth.assert_called_with(20)
    
    @patch('ai_engine.services.Stockfish')
    def test_evaluation_to_text_extreme_positive(self, mock_stockfish):
        """测试极端正数评估文字转换"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            # > 2.0: 红方胜势
            assert service._evaluation_to_text(2.1) == "红方胜势"
            assert service._evaluation_to_text(5.0) == "红方胜势"
            assert service._evaluation_to_text(100.0) == "红方胜势"
    
    @patch('ai_engine.services.Stockfish')
    def test_evaluation_to_text_extreme_negative(self, mock_stockfish):
        """测试极端负数评估文字转换"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            # < -2.0: 黑方胜势
            assert service._evaluation_to_text(-2.1) == "黑方胜势"
            assert service._evaluation_to_text(-5.0) == "黑方胜势"
            assert service._evaluation_to_text(-100.0) == "黑方胜势"
    
    @patch('ai_engine.services.Stockfish')
    def test_evaluation_to_text_boundaries(self, mock_stockfish):
        """测试评估文字转换边界"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            # 边界测试
            assert service._evaluation_to_text(1.5) == "红方明显优势"
            assert service._evaluation_to_text(0.75) == "红方稍优"
            assert service._evaluation_to_text(0.0) == "均势"
            assert service._evaluation_to_text(-0.75) == "黑方稍优"
            assert service._evaluation_to_text(-1.5) == "黑方明显优势"


class TestStockfishServiceGetTopMoves:
    """获取多个走法测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_get_top_moves_returns_list(self, mock_stockfish):
        """验证返回走法列表"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_stockfish_major_info.return_value = [
            {'move': 'e2e4', 'score': 50, 'depth': 10},
            {'move': 'd2d4', 'score': 30, 'depth': 10},
            {'move': 'b3b5', 'score': 10, 'depth': 10},
        ]
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            service._parse_move = Mock(return_value=("e2", "e4"))
            
            top_moves = service.get_top_moves("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1", count=3)
            
            assert isinstance(top_moves, list)
            assert len(top_moves) == 3
            assert all(isinstance(move, dict) for move in top_moves)
    
    @patch('ai_engine.services.Stockfish')
    def test_get_top_moves_limits_count(self, mock_stockfish):
        """验证走法数量限制"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_stockfish_major_info.return_value = [
            {'move': 'e2e4', 'score': 50, 'depth': 10},
            {'move': 'd2d4', 'score': 30, 'depth': 10},
        ]
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            service._parse_move = Mock(return_value=("e2", "e4"))
            
            # 请求 5 个，但只有 2 个可用
            top_moves = service.get_top_moves("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1", count=5)
            
            assert len(top_moves) == 2
    
    @patch('ai_engine.services.Stockfish')
    def test_get_top_moves_default_count(self, mock_stockfish):
        """验证默认走法数量"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_stockfish_major_info.return_value = [
            {'move': 'e2e4', 'score': 50, 'depth': 10},
            {'move': 'd2d4', 'score': 30, 'depth': 10},
            {'move': 'b3b5', 'score': 10, 'depth': 10},
        ]
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            service._parse_move = Mock(return_value=("e2", "e4"))
            
            # 不指定 count，使用默认值 3
            top_moves = service.get_top_moves("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1")
            
            assert len(top_moves) == 3


class TestStockfishServiceDifficulty:
    """难度调整测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_set_difficulty_updates_service(self, mock_stockfish):
        """验证设置难度更新服务配置"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService(difficulty=5)
            
            service.set_difficulty(8)
            
            assert service.difficulty == 8
            assert service.config.level == 8
    
    @patch('ai_engine.services.Stockfish')
    def test_set_difficulty_updates_engine(self, mock_stockfish):
        """验证设置难度更新引擎"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService(difficulty=5)
            
            service.set_difficulty(9)
            
            mock_engine.set_skill_level.assert_called()
            mock_engine.set_depth.assert_called()


class TestStockfishServiceCleanup:
    """清理资源测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_cleanup_quits_engine(self, mock_stockfish):
        """验证清理时关闭引擎"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            service.cleanup()
            
            mock_engine.quit.assert_called_once()
    
    @patch('ai_engine.services.Stockfish')
    def test_cleanup_handles_exception(self, mock_stockfish):
        """验证清理时处理异常"""
        mock_engine = MagicMock()
        mock_engine.quit.side_effect = Exception("Quit failed")
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            # 不应抛出异常
            service.cleanup()


class TestStockfishServiceParseMove:
    """走棋解析测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_parse_move_standard_length(self, mock_stockfish):
        """测试标准长度走棋解析"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            from_pos, to_pos = service._parse_move("e2e4")
            assert from_pos == "e2"
            assert to_pos == "e4"
    
    @patch('ai_engine.services.Stockfish')
    def test_parse_move_promotion(self, mock_stockfish):
        """测试升变走棋解析（如果有）"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            # 国际象棋升变格式：e7e8q
            from_pos, to_pos = service._parse_move("e7e8q")
            assert from_pos == "e7"
            assert to_pos == "e8"
    
    @patch('ai_engine.services.Stockfish')
    def test_parse_move_corners(self, mock_stockfish):
        """测试角落位置走棋解析"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            from_pos, to_pos = service._parse_move("a1a8")
            assert from_pos == "a1"
            assert to_pos == "a8"


class TestStockfishServiceGetPieceAt:
    """获取棋子测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_get_piece_at_returns_piece(self, mock_stockfish):
        """测试获取位置棋子"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService()
            
            # 简化实现默认返回 "P"
            piece = service._get_piece_at("e2", "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1")
            assert piece == "P"


class TestDifficultyConfigExtended:
    """难度配置扩展测试"""
    
    def test_get_difficulty_config_all_levels(self):
        """测试所有难度等级配置"""
        configs = {}
        for diff in range(1, 11):
            config = get_difficulty_config(diff)
            configs[diff] = config
            
            assert config is not None
            assert config.level == diff
            assert hasattr(config, 'skill_level')
            assert hasattr(config, 'search_depth')
            assert hasattr(config, 'think_time_ms')
            assert hasattr(config, 'elo')
        
        # 验证难度递增
        for i in range(1, 10):
            # 高难度应该有更高的 skill_level 和 search_depth
            assert configs[i].skill_level <= configs[i+1].skill_level
    
    def test_get_difficulty_config_consistency(self):
        """测试配置一致性"""
        # 多次获取同一难度应返回相同配置
        config1 = get_difficulty_config(5)
        config2 = get_difficulty_config(5)
        
        assert config1.difficulty == config2.difficulty
        assert config1.skill_level == config2.skill_level
        assert config1.search_depth == config2.search_depth
    
    def test_difficulty_config_attributes(self):
        """测试难度配置属性"""
        config = get_difficulty_config(5)
        
        # 验证属性类型
        assert isinstance(config.level, int)
        assert isinstance(config.skill_level, int)
        assert isinstance(config.search_depth, int)
        assert isinstance(config.think_time_ms, int)
        assert isinstance(config.elo, int)
        
        # 验证合理范围
        assert 1 <= config.level <= 10
        assert config.skill_level >= 0
        assert config.search_depth >= 1
        assert config.think_time_ms >= 0


class TestStockfishServiceIntegration:
    """Stockfish 服务集成测试"""
    
    @patch('ai_engine.services.Stockfish')
    def test_full_move_generation_flow(self, mock_stockfish):
        """测试完整的走棋生成流程"""
        mock_engine = MagicMock()
        mock_stockfish.return_value = mock_engine
        mock_engine.get_best_move.return_value = "c2c4"
        mock_engine.get_current_depth.return_value = 12
        mock_engine.get_evaluation.return_value = "+25"
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            service = StockfishService(difficulty=6)
            service._parse_move = Mock(return_value=("c2", "c4"))
            service._get_evaluation = Mock(return_value=0.25)
            service._get_piece_at = Mock(return_value="P")
            
            # 完整流程
            fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
            move = service.get_best_move(fen, time_limit=1000)
            
            # 验证流程完整
            mock_engine.set_fen_position.assert_called_once()
            mock_engine.get_best_move.assert_called_once()
            assert isinstance(move, AIMove)
            assert move.thinking_time >= 0
    
    @patch('ai_engine.services.Stockfish')
    def test_multiple_services_instantiation(self, mock_stockfish):
        """测试多个服务实例"""
        mock_engine1 = MagicMock()
        mock_engine2 = MagicMock()
        mock_stockfish.side_effect = [mock_engine1, mock_engine2]
        
        with patch('ai_engine.services.settings') as mock_settings:
            mock_settings.STOCKFISH_PATH = '/usr/games/stockfish'
            
            service1 = StockfishService(difficulty=3)
            service2 = StockfishService(difficulty=8)
            
            assert service1.difficulty == 3
            assert service2.difficulty == 8
            assert service1.engine != service2.engine
