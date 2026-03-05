"""
AI Engine 配置模块

定义难度等级配置和参数
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class DifficultyConfig:
    """难度配置数据类"""
    level: int  # 难度等级 1-10
    name: str  # 难度名称
    elo: int  # Elo 分数
    skill_level: int  # Stockfish Skill Level (0-20)
    search_depth: int  # 搜索深度
    think_time_ms: int  # 思考时间（毫秒）
    threads: int  # 线程数
    hash_mb: int  # 哈希表大小（MB）


# 10 级难度配置
DIFFICULTY_LEVELS: Dict[int, DifficultyConfig] = {
    1: DifficultyConfig(
        level=1,
        name="入门",
        elo=400,
        skill_level=0,
        search_depth=5,
        think_time_ms=500,
        threads=1,
        hash_mb=64
    ),
    2: DifficultyConfig(
        level=2,
        name="新手",
        elo=600,
        skill_level=2,
        search_depth=7,
        think_time_ms=500,
        threads=1,
        hash_mb=64
    ),
    3: DifficultyConfig(
        level=3,
        name="初级",
        elo=800,
        skill_level=4,
        search_depth=9,
        think_time_ms=1000,
        threads=2,
        hash_mb=128
    ),
    4: DifficultyConfig(
        level=4,
        name="入门",
        elo=1000,
        skill_level=6,
        search_depth=11,
        think_time_ms=1000,
        threads=2,
        hash_mb=128
    ),
    5: DifficultyConfig(
        level=5,
        name="中级",
        elo=1200,
        skill_level=8,
        search_depth=13,
        think_time_ms=1500,
        threads=2,
        hash_mb=128
    ),
    6: DifficultyConfig(
        level=6,
        name="中级",
        elo=1400,
        skill_level=10,
        search_depth=15,
        think_time_ms=1500,
        threads=2,
        hash_mb=128
    ),
    7: DifficultyConfig(
        level=7,
        name="高级",
        elo=1600,
        skill_level=12,
        search_depth=17,
        think_time_ms=2000,
        threads=2,
        hash_mb=256
    ),
    8: DifficultyConfig(
        level=8,
        name="高级",
        elo=1800,
        skill_level=14,
        search_depth=19,
        think_time_ms=2000,
        threads=2,
        hash_mb=256
    ),
    9: DifficultyConfig(
        level=9,
        name="大师",
        elo=2000,
        skill_level=16,
        search_depth=21,
        think_time_ms=3000,
        threads=4,
        hash_mb=512
    ),
    10: DifficultyConfig(
        level=10,
        name="大师",
        elo=2200,
        skill_level=20,
        search_depth=25,
        think_time_ms=5000,
        threads=4,
        hash_mb=512
    ),
}


def get_difficulty_config(level: int) -> DifficultyConfig:
    """
    获取难度配置
    
    Args:
        level: 难度等级 (1-10)
    
    Returns:
        DifficultyConfig: 难度配置对象
    
    Raises:
        ValueError: 难度等级无效
    """
    if level < 1 or level > 10:
        raise ValueError(f"难度等级必须在 1-10 之间，当前为 {level}")
    
    return DIFFICULTY_LEVELS[level]


def get_all_difficulties() -> list:
    """
    获取所有难度配置
    
    Returns:
        list: 所有难度配置列表
    """
    return list(DIFFICULTY_LEVELS.values())
