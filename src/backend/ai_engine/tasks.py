"""
AI Engine Celery 异步任务

用于异步执行 AI 走棋、分析等耗时操作
"""
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .services import StockfishService
from .models import AIGame, AIAnalysis


@shared_task(bind=True, queue='ai', time_limit=30)
def get_ai_move_task(self, fen: str, difficulty: int = 5, time_limit: int = 2000, game_id: str = None):
    """
    获取 AI 走棋（异步任务）
    
    Args:
        fen: 棋局 FEN 字符串
        difficulty: 难度等级
        time_limit: 思考时间限制（毫秒）
        game_id: 游戏 ID（用于进度通知）
    
    Returns:
        dict: AI 走棋结果
    """
    engine = None
    try:
        # 发送思考中通知
        if game_id:
            send_ai_notification(game_id, 'ai_thinking', {
                'difficulty': difficulty,
                'estimated_time': time_limit
            })
        
        # 获取 AI 走棋
        engine = StockfishService(difficulty=difficulty)
        move = engine.get_best_move(fen, time_limit=time_limit)
        
        result = {
            'from_pos': move.from_pos,
            'to_pos': move.to_pos,
            'piece': move.piece,
            'evaluation': move.evaluation,
            'depth': move.depth,
            'thinking_time': move.thinking_time
        }
        
        # 发送走棋完成通知
        if game_id:
            send_ai_notification(game_id, 'ai_move', result)
        
        return result
    
    except Exception as e:
        # 记录错误
        self.update_state(state='FAILURE', meta={'error': str(e)})
        
        if game_id:
            send_ai_notification(game_id, 'ai_error', {'error': str(e)})
        
        raise
    
    finally:
        if engine:
            engine.cleanup()


@shared_task(bind=True, queue='ai', time_limit=30)
def get_ai_hint_task(self, fen: str, difficulty: int = 5, count: int = 3):
    """
    获取 AI 走棋提示（异步任务）
    
    Args:
        fen: 棋局 FEN 字符串
        difficulty: 难度等级
        count: 提示数量
    
    Returns:
        dict: 提示列表
    """
    engine = None
    try:
        engine = StockfishService(difficulty=difficulty)
        top_moves = engine.get_top_moves(fen, count=count)
        
        return {
            'hints': top_moves
        }
    
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
    
    finally:
        if engine:
            engine.cleanup()


@shared_task(bind=True, queue='ai', time_limit=30)
def analyze_position_task(self, fen: str, depth: int = 15, game_id: str = None, move_number: int = None):
    """
    分析棋局（异步任务）
    
    Args:
        fen: 棋局 FEN 字符串
        depth: 搜索深度
        game_id: 游戏 ID（可选，用于保存分析结果）
        move_number: 步数（可选）
    
    Returns:
        dict: 分析结果
    """
    engine = None
    try:
        engine = StockfishService(difficulty=5)
        evaluation = engine.evaluate_position(fen, depth=depth)
        
        result = {
            'score': evaluation['score'],
            'score_text': evaluation['score_text'],
            'best_move': evaluation['best_move'],
            'depth': evaluation['depth']
        }
        
        # 保存分析结果到数据库
        if game_id:
            try:
                game = AIGame.objects.get(id=game_id)
                AIAnalysis.objects.create(
                    game=game,
                    fen=fen,
                    move_number=move_number or 0,
                    evaluation_score=evaluation['score'],
                    evaluation_text=evaluation['score_text'],
                    best_move=evaluation['best_move'],
                    search_depth=evaluation['depth'],
                    thinking_time_ms=1000  # 估算值
                )
            except Exception as e:
                # 保存失败不影响返回结果
                pass
        
        return result
    
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
    
    finally:
        if engine:
            engine.cleanup()


def send_ai_notification(game_id: str, event_type: str, data: dict):
    """
    发送 AI 通知到 WebSocket
    
    Args:
        game_id: 游戏 ID
        event_type: 事件类型
        data: 事件数据
    """
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'ai_game_{game_id}',
            {
                'type': event_type,
                'data': data
            }
        )
    except Exception as e:
        # 通知失败不影响主流程
        pass
