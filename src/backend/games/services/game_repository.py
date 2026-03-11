"""
Game Repository - 游戏数据仓库

提供游戏数据的持久化操作：
- 游戏创建、查询、更新、删除
- 游戏状态管理
- 玩家游戏历史
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from django.utils import timezone

from games.models import Game, GameMove, GameStatus


class GameRepository:
    """游戏数据仓库类"""
    
    def create_game(
        self,
        game_type: str = 'online',
        fen_start: str = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        red_player_id: Optional[str] = None,
        black_player_id: Optional[str] = None,
        time_control_base: int = 600,
        time_control_increment: int = 0,
        is_rated: bool = True
    ) -> Optional[Game]:
        """
        创建游戏
        
        Args:
            game_type: 游戏类型
            fen_start: 初始 FEN
            red_player_id: 红方玩家 ID
            black_player_id: 黑方玩家 ID
            time_control_base: 基础时间
            time_control_increment: 每步加时
            is_rated: 是否评级
        
        Returns:
            Game 对象，失败返回 None
        """
        try:
            from users.models import User
            
            game = Game(
                game_type=game_type,
                status=GameStatus.PENDING,
                fen_start=fen_start,
                fen_current=fen_start,
                time_control_base=time_control_base,
                time_control_increment=time_control_increment,
                red_time_remaining=time_control_base,
                black_time_remaining=time_control_base,
                is_rated=is_rated
            )
            
            if red_player_id:
                game.red_player = User.objects.get(id=red_player_id)
            if black_player_id:
                game.black_player = User.objects.get(id=black_player_id)
            
            game.save()
            return game
            
        except Exception as e:
            return None
    
    def get_game_by_id(self, game_id: str) -> Optional[Game]:
        """
        根据 ID 获取游戏
        
        Args:
            game_id: 游戏 ID
        
        Returns:
            Game 对象，未找到返回 None
        """
        try:
            return Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return None
    
    def update_game_status(self, game_id: str, status: GameStatus) -> bool:
        """
        更新游戏状态
        
        Args:
            game_id: 游戏 ID
            status: 新状态
        
        Returns:
            bool: 是否成功
        """
        try:
            game = self.get_game_by_id(game_id)
            if not game:
                return False
            
            game.status = status
            game.save()
            return True
            
        except Exception:
            return False
    
    def update_fen(self, game_id: str, fen: str) -> bool:
        """
        更新 FEN
        
        Args:
            game_id: 游戏 ID
            fen: 新 FEN
        
        Returns:
            bool: 是否成功
        """
        try:
            game = self.get_game_by_id(game_id)
            if not game:
                return False
            
            game.fen_current = fen
            game.save()
            return True
            
        except Exception:
            return False
    
    def finish_game(
        self,
        game_id: str,
        winner: Optional[str],
        win_reason: str
    ) -> bool:
        """
        结束游戏
        
        Args:
            game_id: 游戏 ID
            winner: 获胜方 ('red', 'black', None)
            win_reason: 获胜原因
        
        Returns:
            bool: 是否成功
        """
        try:
            game = self.get_game_by_id(game_id)
            if not game:
                return False
            
            if winner == 'red':
                game.status = GameStatus.RED_WIN
            elif winner == 'black':
                game.status = GameStatus.BLACK_WIN
            elif winner == 'draw' or winner is None:
                game.status = GameStatus.DRAW
            
            game.winner = winner
            game.win_reason = win_reason
            game.finished_at = timezone.now()
            
            if game.started_at:
                game.duration = int((game.finished_at - game.started_at).total_seconds())
            
            game.save()
            return True
            
        except Exception:
            return False
    
    def get_player_games(self, player_id: str, limit: int = 50) -> List[Game]:
        """
        获取玩家游戏列表
        
        Args:
            player_id: 玩家 ID
            limit: 返回数量限制
        
        Returns:
            Game 列表
        """
        from django.db.models import Q
        
        return list(Game.objects.filter(
            Q(red_player_id=player_id) | Q(black_player_id=player_id)
        ).order_by('-created_at')[:limit])
    
    def get_active_games(self) -> List[Game]:
        """
        获取活跃游戏
        
        Returns:
            Game 列表
        """
        return list(Game.objects.filter(status=GameStatus.PLAYING))
    
    def get_recent_games(self, limit: int = 20) -> List[Game]:
        """
        获取最近游戏
        
        Args:
            limit: 返回数量限制
        
        Returns:
            Game 列表
        """
        return list(Game.objects.filter(
            status__in=[GameStatus.RED_WIN, GameStatus.BLACK_WIN, GameStatus.DRAW]
        ).order_by('-finished_at')[:limit])
    
    def delete_game(self, game_id: str) -> bool:
        """
        删除游戏
        
        Args:
            game_id: 游戏 ID
        
        Returns:
            bool: 是否成功
        """
        try:
            game = self.get_game_by_id(game_id)
            if not game:
                return False
            
            game.delete()
            return True
            
        except Exception:
            return False
    
    def record_move(
        self,
        game: Game,
        move_number: int,
        piece: str,
        from_pos: str,
        to_pos: str,
        captured: Optional[str] = None,
        is_check: bool = False,
        is_capture: bool = False,
        notation: str = '',
        san: str = ''
    ) -> Optional[GameMove]:
        """
        记录走棋
        
        Args:
            game: 游戏对象
            move_number: 走棋序号
            piece: 棋子类型
            from_pos: 起始位置
            to_pos: 目标位置
            captured: 被吃棋子
            is_check: 是否将军
            is_capture: 是否吃子
            notation: 中文记谱
            san: 标准记谱
        
        Returns:
            GameMove 对象，失败返回 None
        """
        try:
            move = GameMove.objects.create(
                game=game,
                move_number=move_number,
                piece=piece,
                from_pos=from_pos,
                to_pos=to_pos,
                captured=captured,
                is_check=is_check,
                is_capture=is_capture,
                notation=notation or f"{piece}{from_pos}-{to_pos}",
                san=san
            )
            return move
            
        except Exception:
            return None
    
    def get_game_moves(self, game_id: str) -> List[GameMove]:
        """
        获取游戏走棋历史
        
        Args:
            game_id: 游戏 ID
        
        Returns:
            GameMove 列表
        """
        try:
            game = self.get_game_by_id(game_id)
            if not game:
                return []
            
            return list(game.moves.order_by('move_number'))
            
        except Exception:
            return []
