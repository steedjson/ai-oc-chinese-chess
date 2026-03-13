"""
AI Engine 单元测试 - 难度配置测试

测试难度等级映射和配置参数
"""
import pytest
from ai_engine.config import DifficultyConfig, get_difficulty_config, DIFFICULTY_LEVELS


class TestDifficultyConfig:
    """难度配置测试"""
    
    def test_difficulty_level_1_beginner(self):
        """测试难度 1：入门级别（1320 Elo - Stockfish 最低）"""
        config = get_difficulty_config(1)
        
        assert config.level == 1
        assert config.name == "入门"
        assert config.elo == 1320
        assert config.skill_level == 0
        assert config.search_depth == 5
        assert config.think_time_ms == 500
        assert config.threads == 1
        assert config.hash_mb == 64
    
    def test_difficulty_level_5_intermediate(self):
        """测试难度 5：中级（1700 Elo）"""
        config = get_difficulty_config(5)
        
        assert config.level == 5
        assert config.name == "中级"
        assert config.elo == 1700
        assert config.skill_level == 8
        assert config.search_depth == 13
        assert config.think_time_ms == 1500
        assert config.threads == 2
        assert config.hash_mb == 128
    
    def test_difficulty_level_10_master(self):
        """测试难度 10：大师级别（2400 Elo）"""
        config = get_difficulty_config(10)
        
        assert config.level == 10
        assert config.name == "大师"
        assert config.elo == 2400
        assert config.skill_level == 20
        assert config.search_depth == 25
        assert config.think_time_ms == 5000
        assert config.threads == 4
        assert config.hash_mb == 512
    
    def test_all_difficulty_levels_exist(self):
        """测试所有 10 个难度等级都存在"""
        for level in range(1, 11):
            config = get_difficulty_config(level)
            assert config.level == level
            assert config.elo > 0
            assert config.skill_level >= 0
            assert config.skill_level <= 20
            assert config.search_depth >= 5
            assert config.search_depth <= 25
            assert config.think_time_ms >= 500
            assert config.think_time_ms <= 5000
    
    def test_difficulty_levels_elo_progression(self):
        """测试难度等级 Elo 分数递增"""
        configs = [get_difficulty_config(i) for i in range(1, 11)]
        
        for i in range(len(configs) - 1):
            assert configs[i].elo < configs[i + 1].elo, \
                f"Elo 应该在难度 {i+1} 到 {i+2} 之间递增"
    
    def test_difficulty_levels_depth_progression(self):
        """测试难度等级搜索深度递增"""
        configs = [get_difficulty_config(i) for i in range(1, 11)]
        
        for i in range(len(configs) - 1):
            assert configs[i].search_depth <= configs[i + 1].search_depth, \
                f"搜索深度应该在难度 {i+1} 到 {i+2} 之间递增或持平"
    
    def test_difficulty_levels_think_time_progression(self):
        """测试难度等级思考时间递增"""
        configs = [get_difficulty_config(i) for i in range(1, 11)]
        
        for i in range(len(configs) - 1):
            assert configs[i].think_time_ms <= configs[i + 1].think_time_ms, \
                f"思考时间应该在难度 {i+1} 到 {i+2} 之间递增或持平"
    
    def test_invalid_difficulty_level(self):
        """测试无效难度等级抛出异常"""
        with pytest.raises(ValueError):
            get_difficulty_config(0)
        
        with pytest.raises(ValueError):
            get_difficulty_config(11)
        
        with pytest.raises(ValueError):
            get_difficulty_config(-1)
    
    def test_difficulty_config_dataclass(self):
        """测试 DifficultyConfig 数据类"""
        config = DifficultyConfig(
            level=5,
            name="测试",
            elo=1200,
            skill_level=8,
            search_depth=13,
            think_time_ms=1500,
            threads=2,
            hash_mb=128
        )
        
        assert config.level == 5
        assert config.name == "测试"
        assert config.elo == 1200
        assert config.skill_level == 8
        assert config.search_depth == 13
        assert config.think_time_ms == 1500
        assert config.threads == 2
        assert config.hash_mb == 128
    
    def test_difficulty_levels_count(self):
        """测试难度等级总数为 10"""
        assert len(DIFFICULTY_LEVELS) == 10
