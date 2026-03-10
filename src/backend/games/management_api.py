"""
游戏管理 API - 管理端专用
提供管理员对游戏对局的管理功能
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.db.models import Q

from games.models import Game
from games.serializers_backup import GameListSerializer, GameDetailSerializer
from games.services.game_service import GameService
from .services.anomaly_detector import AnomalyDetector


class IsSuperAdmin(permissions.BasePermission):
    """仅允许超级管理员访问"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class GameManagementViewSet(viewsets.ViewSet):
    """游戏管理视图集 - 管理端专用"""
    
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        """获取所有对局"""
        return Game.objects.all().order_by('-created_at')
    
    def list(self, request):
        """
        获取所有游戏对局列表（管理端）
        支持搜索和过滤
        """
        queryset = self.get_queryset()
        
        # 搜索过滤
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(red_player__username__icontains=search) |
                Q(black_player__username__icontains=search) |
                Q(id__icontains=search)
            )
        
        # 状态过滤
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 异常对局过滤
        is_abnormal = request.query_params.get('abnormal')
        if is_abnormal == 'true':
            # 获取超过 2 小时的对局
            two_hours_ago = timezone.now() - timezone.timedelta(hours=2)
            queryset = queryset.filter(
                status='playing',
                started_at__lt=two_hours_ago
            )
        
        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        games = queryset[start:end]
        total = queryset.count()
        
        serializer = GameListSerializer(games, many=True, context={'request': request})
        
        return Response({
            'data': serializer.data,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    
    def retrieve(self, request, pk=None):
        """获取对局详情"""
        game = Game.objects.get(pk=pk)
        serializer = GameDetailSerializer(game, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def abort(self, request, pk=None):
        """
        中止对局
        管理员可以强制中止任意对局
        """
        game = Game.objects.get(pk=pk)
        
        if game.status not in ['playing', 'waiting']:
            raise ValidationError({'error': '对局已结束，无法中止'})
        
        # 获取中止原因
        reason = request.data.get('reason', '管理员强制中止')
        
        # 更新游戏状态
        game.status = 'aborted'
        game.finished_at = timezone.now()
        game.aborted_by = request.user
        game.abort_reason = reason
        
        # 计算持续时间
        if game.started_at:
            duration = (game.finished_at - game.started_at).total_seconds()
            game.duration = int(duration)
        
        game.save()
        
        # 记录日志
        from .models.game_log import GameLog
        GameLog.objects.create(
            game=game,
            operator=request.user,
            action='abort',
            details={'reason': reason}
        )
        
        # TODO: 通知双方玩家
        # 可以通过 WebSocket 或站内消息通知
        
        return Response({
            'success': True,
            'message': f'对局已中止，原因：{reason}'
        })
    
    @action(detail=False, methods=['post'])
    def clear_expired_waiting(self, request):
        """
        清理过期等待中的对局
        取消所有超过 15 分钟无人加入的"等待中"对局
        """
        fifteen_minutes_ago = timezone.now() - timezone.timedelta(minutes=15)
        
        expired_games = Game.objects.filter(
            status='waiting',
            created_at__lt=fifteen_minutes_ago
        )
        
        count = expired_games.count()
        
        # 批量更新
        expired_games.update(
            status='aborted',
            finished_at=timezone.now(),
            abort_reason='超时未开始'
        )
        
        # 记录日志
        from .models.game_log import GameLog
        for game in expired_games:
            GameLog.objects.create(
                game=game,
                operator=request.user,
                action='auto_abort',
                details={'reason': '超时未开始'}
            )
        
        return Response({
            'success': True,
            'count': count
        })
    
    @action(detail=False, methods=['get'])
    def anomalies(self, request):
        """
        获取异常对局列表
        检测超时、作弊嫌疑等异常情况
        """
        detector = AnomalyDetector()
        anomalies = detector.detect_all_anomalies()
        
        return Response({
            'data': anomalies,
            'total': len(anomalies)
        })
    
    @action(detail=True, methods=['post'])
    def mark_abnormal(self, request, pk=None):
        """
        标记对局为异常
        """
        game = Game.objects.get(pk=pk)
        reason = request.data.get('reason', '管理员标记')
        
        # 更新游戏标记
        game.is_abnormal = True
        game.abnormal_reason = reason
        game.save()
        
        # 记录日志
        GameLog.objects.create(
            game=game,
            operator=request.user,
            action='mark_abnormal',
            details={'reason': reason}
        )
        
        return Response({
            'success': True,
            'message': f'对局已标记为异常：{reason}'
        })
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        获取对局操作日志
        """
        from .models.game_log import GameLog
        
        game = Game.objects.get(pk=pk)
        logs = GameLog.objects.filter(game=game).order_by('-created_at')
        
        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        logs_page = logs[start:end]
        total = logs.count()
        
        return Response({
            'data': [log.to_dict() for log in logs_page],
            'total': total,
            'page': page,
            'page_size': page_size
        })
