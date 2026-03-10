"""
游戏对局 API 视图
"""
from django.db import models
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Game, GameMove
from .serializers import (
    GameListSerializer,
    GameDetailSerializer,
    GameCreateSerializer,
    MoveCreateSerializer
)
from .timer_service import get_timer_service


class GameViewSet(viewsets.ModelViewSet):
    """游戏对局视图集"""
    
    queryset = Game.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """根据动作获取序列化器"""
        if self.action == 'create':
            return GameCreateSerializer
        elif self.action in ['retrieve', 'get_moves']:
            return GameDetailSerializer
        elif self.action == 'list':
            return GameListSerializer
        return GameDetailSerializer
    
    def get_queryset(self):
        """获取当前用户的对局"""
        user = self.request.user
        # 返回用户参与的所有对局（红方或黑方）
        return Game.objects.filter(
            models.Q(red_player=user) | models.Q(black_player=user)
        ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """创建新对局"""
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # 自动开始单机对局
        game = serializer.instance
        if game.game_type == 'single':
            game.status = 'playing'
            game.started_at = timezone.now()
            game.save()
            
            # 初始化计时器
            timer_service = get_timer_service()
            base_time = game.timeout_seconds or 7200  # 默认 2 小时
            timer_service.init_timer(game, base_time)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            GameDetailSerializer(game, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def retrieve(self, request, *args, **kwargs):
        """获取对局详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def moves(self, request, pk=None):
        """获取走棋历史"""
        game = self.get_object()
        moves = game.moves.all().order_by('move_number')
        serializer = GameMoveSerializer(moves, many=True)
        return Response({'moves': serializer.data})
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """提交走棋"""
        game = self.get_object()
        
        # 验证游戏状态
        if game.status != 'playing':
            raise ValidationError({'error': '游戏未进行中'})
        
        # 验证走棋
        move_serializer = MoveCreateSerializer(data=request.data)
        move_serializer.is_valid(raise_exception=True)
        
        from_pos = move_serializer.validated_data['from_pos']
        to_pos = move_serializer.validated_data['to_pos']
        
        # 使用规则引擎验证走棋
        from .engine import Board, MoveValidator, Move
        from .fen_service import FenService
        
        board = Board(game.fen_current)
        
        # 验证是否是当前玩家的回合
        expected_turn = 'w' if game.red_player == request.user else 'b'
        if board.turn != expected_turn:
            raise ValidationError({'error': '不是你的回合'})
        
        # 获取棋子
        piece = board.get_piece(from_pos)
        if not piece:
            raise ValidationError({'error': '起始位置没有棋子'})
        
        # 创建走棋对象
        move = Move(
            from_pos=from_pos,
            to_pos=to_pos,
            piece=piece,
            captured=board.get_piece(to_pos)
        )
        
        # 验证走棋合法性
        validator = MoveValidator(board)
        if not validator.is_valid_move(move):
            # 获取合法走法提示
            legal_moves = board.get_legal_moves_for_piece(from_pos)
            legal_positions = [m.to_pos for m in legal_moves]
            raise ValidationError({
                'error': '无效走棋',
                'legal_moves': legal_positions
            })
        
        # 执行走棋
        board.make_move(move)
        
        # 创建走棋记录
        game_move = GameMove.objects.create(
            game=game,
            move_number=game.move_count + 1,
            piece=piece,
            from_pos=from_pos,
            to_pos=to_pos,
            captured=move.captured,
            is_check=False,  # TODO: 检测将军
            is_capture=move.is_capture,
            fen_after=board.to_fen(),
            time_remaining=game.red_time_remaining if board.turn == 'b' else game.black_time_remaining
        )
        
        # 更新游戏状态
        game.fen_current = board.to_fen()
        game.turn = board.turn
        game.move_count += 1
        game.save()
        
        # 检查游戏结束（将死/困毙）
        # TODO: 实现游戏结束检测
        
        return Response({
            'success': True,
            'move': GameMoveSerializer(game_move).data,
            'fen': board.to_fen(),
            'turn': board.turn
        })
    
    @action(detail=True, methods=['put'])
    def status(self, request, pk=None):
        """更新对局状态"""
        game = self.get_object()
        
        new_status = request.data.get('status')
        if new_status not in ['pending', 'playing', 'red_win', 'black_win', 'draw', 'aborted']:
            raise ValidationError({'error': '无效的状态'})
        
        game.status = new_status
        
        # 如果游戏结束，记录结束时间
        if new_status in ['red_win', 'black_win', 'draw', 'aborted']:
            game.finished_at = timezone.now()
            
            # 计算持续时间
            if game.started_at:
                duration = (game.finished_at - game.started_at).total_seconds()
                game.duration = int(duration)
        
        game.save()
        
        return Response(GameDetailSerializer(game, context={'request': request}).data)
    
    def destroy(self, request, *args, **kwargs):
        """取消对局"""
        game = self.get_object()
        
        # 只能取消未开始或进行中的游戏
        if game.status not in ['pending', 'playing']:
            raise ValidationError({'error': '无法取消已结束的游戏'})
        
        game.status = 'aborted'
        game.finished_at = timezone.now()
        game.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserGamesViewSet(viewsets.ViewSet):
    """用户对局视图集"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request, user_id=None):
        """获取指定用户的对局列表"""
        # 只能查看自己的对局，除非是管理员
        if request.user.id != int(user_id) and not request.user.is_staff:
            return Response(
                {'error': '无权限查看他人对局'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        games = Game.objects.filter(
            red_player_id=user_id
        ).order_by('-created_at')
        
        serializer = GameListSerializer(games, many=True, context={'request': request})
        return Response({'games': serializer.data})
