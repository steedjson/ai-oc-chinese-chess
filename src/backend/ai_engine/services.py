"""
AI Engine 服务模块

实现 Stockfish 引擎服务、走棋生成、局面评估等功能
"""
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from django.conf import settings

try:
    from stockfish import Stockfish
except ImportError:
    Stockfish = None

from .config import get_difficulty_config, DifficultyConfig


@dataclass
class AIMove:
    """AI 走棋数据类"""
    from_pos: str  # 起始位置
    to_pos: str  # 目标位置
    piece: str  # 棋子类型
    evaluation: float  # 局面评估分数
    depth: int  # 搜索深度
    thinking_time: int  # 思考时间（毫秒）
    notation: str = ""  # 棋谱记号（可选）


class StockfishService:
    """
    Stockfish 引擎服务类
    
    封装 Stockfish 引擎的调用，提供走棋生成、局面评估、走棋提示等功能
    """
    
    def __init__(self, difficulty: int = 5):
        """
        初始化 Stockfish 引擎
        
        Args:
            difficulty: 难度等级 (1-10)，默认为 5
        """
        if Stockfish is None:
            raise RuntimeError("python-stockfish 库未安装")
        
        self.difficulty = difficulty
        self.config = get_difficulty_config(difficulty)
        
        # 获取 Stockfish 路径
        stockfish_path = getattr(settings, 'STOCKFISH_PATH', '/usr/games/stockfish')
        
        # 初始化 Stockfish 引擎
        self.engine = Stockfish(
            path=stockfish_path,
            depth=self.config.search_depth,
            parameters={
                "Skill Level": self.config.skill_level,
                "Move Overhead": self.config.think_time_ms,
                "Threads": self.config.threads,
                "Hash": self.config.hash_mb,
                "UCI_LimitStrength": True,
                "UCI_Elo": self.config.elo,
            }
        )
    
    def get_best_move(self, fen: str, time_limit: Optional[int] = None) -> AIMove:
        """
        获取最佳走棋
        
        Args:
            fen: 棋局 FEN 字符串
            time_limit: 思考时间限制（毫秒），可选
        
        Returns:
            AIMove: AI 走棋结果
        """
        start_time = time.time()
        
        # 设置局面
        self.engine.set_fen_position(fen)
        
        # 获取最佳走棋
        if time_limit:
            best_move = self.engine.get_best_move(time=time_limit)
        else:
            best_move = self.engine.get_best_move(time=self.config.think_time_ms)
        
        thinking_time = int((time.time() - start_time) * 1000)
        
        # 解析走棋
        from_pos, to_pos = self._parse_move(best_move)
        
        # 获取评估分数
        evaluation = self._get_evaluation()
        
        # 获取搜索深度
        depth = self.engine.get_current_depth()
        
        return AIMove(
            from_pos=from_pos,
            to_pos=to_pos,
            piece=self._get_piece_at(from_pos, fen),
            evaluation=evaluation,
            depth=depth,
            thinking_time=thinking_time
        )
    
    def get_top_moves(self, fen: str, count: int = 3) -> List[Dict]:
        """
        获取多个候选走法（用于提示）
        
        Args:
            fen: 棋局 FEN 字符串
            count: 返回走法数量
        
        Returns:
            List[Dict]: 候选走法列表
        """
        self.engine.set_fen_position(fen)
        
        # 获取引擎详细信息
        info = self.engine.get_stockfish_major_info()
        
        top_moves = []
        for i in range(min(count, len(info))):
            move_info = info[i]
            from_pos, to_pos = self._parse_move(move_info['move'])
            
            top_moves.append({
                'from': from_pos,
                'to': to_pos,
                'evaluation': move_info.get('score', 0),
                'depth': move_info.get('depth', 0),
            })
        
        return top_moves
    
    def evaluate_position(self, fen: str, depth: Optional[int] = None) -> Dict:
        """
        评估当前局面
        
        Args:
            fen: 棋局 FEN 字符串
            depth: 搜索深度，可选
        
        Returns:
            Dict: 评估结果，包含 score, score_text, best_move, depth
        """
        self.engine.set_fen_position(fen)
        
        if depth:
            self.engine.set_depth(depth)
        
        evaluation = self._get_evaluation()
        best_move = self.engine.get_best_move()
        current_depth = self.engine.get_current_depth()
        
        return {
            'score': evaluation,
            'score_text': self._evaluation_to_text(evaluation),
            'best_move': best_move,
            'depth': current_depth
        }
    
    def set_difficulty(self, difficulty: int):
        """
        动态调整难度
        
        Args:
            difficulty: 新的难度等级
        """
        self.difficulty = difficulty
        self.config = get_difficulty_config(difficulty)
        
        self.engine.set_skill_level(self.config.skill_level)
        self.engine.set_depth(self.config.search_depth)
    
    def cleanup(self):
        """清理引擎资源"""
        if hasattr(self, 'engine') and self.engine:
            self.engine.quit()
    
    def _get_evaluation(self) -> float:
        """
        获取局面评估分数
        
        Returns:
            float: 评估分数（正数表示红方优势，负数表示黑方优势）
        """
        eval_info = self.engine.get_evaluation()
        
        if eval_info['type'] == 'cp':
            # 百分比分，转换为小数
            return eval_info['value'] / 100.0
        elif eval_info['type'] == 'mate':
            # 将死，返回极大值
            return 100.0 if eval_info['value'] > 0 else -100.0
        
        return 0.0
    
    def _evaluation_to_text(self, score: float) -> str:
        """
        将评估分数转换为文字描述
        
        Args:
            score: 评估分数
        
        Returns:
            str: 文字描述
        """
        if score > 2.0:
            return "红方胜势"
        elif score > 1.0:
            return "红方明显优势"
        elif score > 0.5:
            return "红方稍优"
        elif score > -0.5:
            return "均势"
        elif score > -1.0:
            return "黑方稍优"
        elif score > -2.0:
            return "黑方明显优势"
        else:
            return "黑方胜势"
    
    def _parse_move(self, move_str: str) -> tuple:
        """
        解析 UCI 格式走棋
        
        Args:
            move_str: UCI 格式走棋字符串（如 "e2e4"）
        
        Returns:
            tuple: (from_pos, to_pos)
        """
        from_pos = move_str[:2]
        to_pos = move_str[2:4]
        return from_pos, to_pos
    
    def _get_piece_at(self, pos: str, fen: str) -> str:
        """
        获取指定位置的棋子
        
        Args:
            pos: 位置（如 "e2"）
            fen: FEN 字符串
        
        Returns:
            str: 棋子类型
        """
        # 简化实现：根据 FEN 解析棋子
        # 实际实现需要完整的 FEN 解析逻辑
        return "P"  # 默认返回兵/卒
