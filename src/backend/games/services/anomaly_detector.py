"""
异常检测服务
检测游戏对局中的异常情况：超时、作弊嫌疑等
"""
from typing import List, Dict, Any
from django.utils import timezone
from datetime import timedelta

from games.models import Game


class AnomalyDetector:
    """异常检测器"""
    
    # 配置常量
    MAX_GAME_DURATION_HOURS = 2  # 最大对局时长（小时）
    SUSPICIOUS_MOVE_TIME_SECONDS = 2  # 可疑走棋时间（秒）- 太快可能是作弊
    MIN_SUSPICIOUS_MOVES = 5  # 最少可疑走棋次数触发警报
    
    def __init__(self):
        pass
    
    def detect_all_anomalies(self) -> List[Dict[str, Any]]:
        """
        检测所有异常对局
        返回异常对局列表
        """
        anomalies = []
        
        # 1. 检测超时对局
        timeout_anomalies = self.detect_timeout_games()
        anomalies.extend(timeout_anomalies)
        
        # 2. 检测可疑走棋
        suspicious_anomalies = self.detect_suspicious_moves()
        anomalies.extend(suspicious_anomalies)
        
        # 3. 检测长时间无操作
        idle_anomalies = self.detect_idle_games()
        anomalies.extend(idle_anomalies)
        
        return anomalies
    
    def detect_timeout_games(self) -> List[Dict[str, Any]]:
        """
        检测超时对局
        对局时间超过 MAX_GAME_DURATION_HOURS 小时
        """
        timeout_threshold = timezone.now() - timedelta(hours=self.MAX_GAME_DURATION_HOURS)
        
        timeout_games = Game.objects.filter(
            status='playing',
            started_at__lt=timeout_threshold
        ).select_related('red_player', 'black_player')
        
        anomalies = []
        for game in timeout_games:
            duration_hours = (timezone.now() - game.started_at).total_seconds() / 3600
            
            anomalies.append({
                'game_id': game.id,
                'game': {
                    'id': game.id,
                    'red_player': game.red_player.username if game.red_player else '未知',
                    'black_player': game.black_player.username if game.black_player else '未知',
                    'status': game.status,
                    'started_at': game.started_at.isoformat() if game.started_at else None,
                },
                'anomaly_type': 'timeout',
                'severity': 'high',
                'description': f'对局时间过长，已持续 {duration_hours:.2f} 小时',
                'details': {
                    'duration_hours': duration_hours,
                    'threshold_hours': self.MAX_GAME_DURATION_HOURS,
                },
                'detected_at': timezone.now().isoformat()
            })
        
        return anomalies
    
    def detect_suspicious_moves(self) -> List[Dict[str, Any]]:
        """
        检测可疑走棋
        走棋时间过短可能是使用 AI 作弊
        """
        # 获取所有进行中的对局
        playing_games = Game.objects.filter(
            status='playing'
        ).prefetch_related('moves')
        
        anomalies = []
        
        for game in playing_games:
            moves = game.moves.all().order_by('created_at')
            
            if moves.count() < self.MIN_SUSPICIOUS_MOVES:
                continue
            
            suspicious_count = 0
            suspicious_moves = []
            
            for i, move in enumerate(moves):
                # 计算走棋时间（与上一步的时间差）
                if i > 0:
                    prev_move = moves[i - 1]
                    time_diff = (move.created_at - prev_move.created_at).total_seconds()
                    
                    if time_diff < self.SUSPICIOUS_MOVE_TIME_SECONDS:
                        suspicious_count += 1
                        suspicious_moves.append({
                            'move_number': move.move_number,
                            'time_diff': time_diff,
                            'from_pos': move.from_pos,
                            'to_pos': move.to_pos,
                        })
            
            # 如果可疑走棋次数超过阈值，标记为异常
            if suspicious_count >= self.MIN_SUSPICIOUS_MOVES:
                anomalies.append({
                    'game_id': game.id,
                    'game': {
                        'id': game.id,
                        'red_player': game.red_player.username if game.red_player else '未知',
                        'black_player': game.black_player.username if game.black_player else '未知',
                        'status': game.status,
                        'started_at': game.started_at.isoformat() if game.started_at else None,
                    },
                    'anomaly_type': 'suspicious_moves',
                    'severity': 'high',
                    'description': f'检测到 {suspicious_count} 次可疑走棋（走棋时间过短）',
                    'details': {
                        'suspicious_count': suspicious_count,
                        'threshold': self.MIN_SUSPICIOUS_MOVES,
                        'suspicious_moves': suspicious_moves[:10],  # 只返回前 10 个
                    },
                    'detected_at': timezone.now().isoformat()
                })
        
        return anomalies
    
    def detect_idle_games(self) -> List[Dict[str, Any]]:
        """
        检测长时间无操作的对局
        超过 30 分钟无走棋
        """
        idle_threshold = timezone.now() - timedelta(minutes=30)
        
        # 获取有走棋记录的对局
        games_with_moves = Game.objects.filter(
            status='playing',
            moves__isnull=False
        ).annotate(
            last_move_time=models.Max('moves__created_at')
        ).filter(
            last_move_time__lt=idle_threshold
        ).select_related('red_player', 'black_player')
        
        anomalies = []
        
        for game in games_with_moves:
            idle_minutes = (timezone.now() - game.last_move_time).total_seconds() / 60
            
            anomalies.append({
                'game_id': game.id,
                'game': {
                    'id': game.id,
                    'red_player': game.red_player.username if game.red_player else '未知',
                    'black_player': game.black_player.username if game.black_player else '未知',
                    'status': game.status,
                    'started_at': game.started_at.isoformat() if game.started_at else None,
                },
                'anomaly_type': 'idle',
                'severity': 'medium',
                'description': f'对局长时间无操作，已空闲 {idle_minutes:.1f} 分钟',
                'details': {
                    'idle_minutes': idle_minutes,
                    'threshold_minutes': 30,
                    'last_move_time': game.last_move_time.isoformat() if game.last_move_time else None,
                },
                'detected_at': timezone.now().isoformat()
            })
        
        return anomalies
    
    def detect_game_anomaly(self, game: Game) -> List[Dict[str, Any]]:
        """
        检测单个对局的异常
        """
        anomalies = []
        
        # 检查超时
        if game.status == 'playing' and game.started_at:
            duration_hours = (timezone.now() - game.started_at).total_seconds() / 3600
            if duration_hours > self.MAX_GAME_DURATION_HOURS:
                anomalies.append({
                    'game_id': game.id,
                    'anomaly_type': 'timeout',
                    'severity': 'high',
                    'description': f'对局时间过长，已持续 {duration_hours:.2f} 小时',
                })
        
        return anomalies
    
    def get_anomaly_statistics(self) -> Dict[str, Any]:
        """
        获取异常统计信息
        """
        all_anomalies = self.detect_all_anomalies()
        
        stats = {
            'total_anomalies': len(all_anomalies),
            'by_type': {},
            'by_severity': {
                'high': 0,
                'medium': 0,
                'low': 0,
            }
        }
        
        for anomaly in all_anomalies:
            # 按类型统计
            anomaly_type = anomaly['anomaly_type']
            stats['by_type'][anomaly_type] = stats['by_type'].get(anomaly_type, 0) + 1
            
            # 按严重程度统计
            severity = anomaly['severity']
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        return stats


# 需要导入 models
from django.db import models
