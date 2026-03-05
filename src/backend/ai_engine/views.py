"""
AI Engine API 视图

提供 AI 对弈相关的 RESTful API 接口
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
import asyncio

from .models import AIGame, AIDifficulty, AIAnalysis
from .serializers import (
    AIGameSerializer, AIGameCreateSerializer,
    AIMoveRequestSerializer, AIMoveResponseSerializer,
    AIHintRequestSerializer, AIHintResponseSerializer,
    AIAnalysisRequestSerializer, AIAnalysisResponseSerializer,
    AIDifficultySerializer
)
from .services import StockfishService
from .engine_pool import get_engine_pool
from .config import get_all_difficulties


class AIGameListView(APIView):
    """
    AI 对局列表视图
    
    GET: 获取当前用户的 AI 对局列表
    POST: 创建新的 AI 对局
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取用户的 AI 对局列表"""
        # TODO: 实现用户过滤
        games = AIGame.objects.filter(status='playing').order_by('-created_at')[:20]
        serializer = AIGameSerializer(games, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def post(self, request):
        """创建新的 AI 对局"""
        serializer = AIGameCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # 设置玩家
            serializer.validated_data['player'] = request.user
            
            # 验证难度等级
            ai_level = serializer.validated_data.get('ai_level', 5)
            if ai_level < 1 or ai_level > 10:
                return Response({
                    'success': False,
                    'error': {'code': 'INVALID_DIFFICULTY', 'message': '难度等级必须在 1-10 之间'}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            game = serializer.save()
            
            return Response({
                'success': True,
                'data': AIGameSerializer(game).data,
                'message': 'AI 对局创建成功'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'error': {'code': 'VALIDATION_ERROR', 'message': '参数验证失败', 'details': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)


class AIGameDetailView(APIView):
    """
    AI 对局详情视图
    
    GET: 获取 AI 对局详情
    PUT: 更新 AI 对局状态
    DELETE: 取消 AI 对局
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, game_id):
        """获取 AI 对局详情"""
        game = get_object_or_404(AIGame, id=game_id)
        
        # 验证权限（只能查看自己的对局）
        if str(game.player_id) != str(request.user.id):
            return Response({
                'success': False,
                'error': {'code': 'PERMISSION_DENIED', 'message': '无权查看此对局'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AIGameSerializer(game)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, game_id):
        """更新 AI 对局状态"""
        game = get_object_or_404(AIGame, id=game_id)
        
        if str(game.player_id) != str(request.user.id):
            return Response({
                'success': False,
                'error': {'code': 'PERMISSION_DENIED', 'message': '无权修改此对局'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 更新对局状态
        status_data = request.data.get('status')
        if status_data:
            game.status = status_data
        
        winner = request.data.get('winner')
        if winner:
            game.winner = winner
            game.finished_at = timezone.now()
        
        game.save()
        
        return Response({
            'success': True,
            'data': AIGameSerializer(game).data
        })
    
    def delete(self, request, game_id):
        """取消 AI 对局"""
        game = get_object_or_404(AIGame, id=game_id)
        
        if str(game.player_id) != str(request.user.id):
            return Response({
                'success': False,
                'error': {'code': 'PERMISSION_DENIED', 'message': '无权删除此对局'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        if game.status not in ['pending', 'playing']:
            return Response({
                'success': False,
                'error': {'code': 'INVALID_STATUS', 'message': '只能取消未开始或进行中的对局'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        game.status = 'aborted'
        game.save()
        
        return Response({
            'success': True,
            'message': '对局已取消'
        }, status=status.HTTP_204_NO_CONTENT)


class AIMoveView(APIView):
    """
    AI 走棋视图
    
    POST: 请求 AI 走棋
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """请求 AI 走棋"""
        serializer = AIMoveRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': '参数验证失败', 'details': serializer.errors}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        fen = serializer.validated_data['fen']
        difficulty = serializer.validated_data['difficulty']
        time_limit = serializer.validated_data.get('time_limit', 2000)
        
        try:
            # 使用引擎池获取引擎
            # 注意：实际生产中应该使用异步 Celery 任务
            engine = StockfishService(difficulty=difficulty)
            move = engine.get_best_move(fen, time_limit=time_limit)
            engine.cleanup()
            
            return Response({
                'success': True,
                'data': {
                    'from_pos': move.from_pos,
                    'to_pos': move.to_pos,
                    'piece': move.piece,
                    'evaluation': move.evaluation,
                    'depth': move.depth,
                    'thinking_time': move.thinking_time
                }
            })
        
        except Exception as e:
            return Response({
                'success': False,
                'error': {'code': 'AI_ERROR', 'message': f'AI 走棋失败：{str(e)}'}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIHintView(APIView):
    """
    AI 走棋提示视图
    
    POST: 请求 AI 走棋提示
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """请求 AI 走棋提示"""
        serializer = AIHintRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': '参数验证失败', 'details': serializer.errors}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        fen = serializer.validated_data['fen']
        difficulty = serializer.validated_data['difficulty']
        count = serializer.validated_data.get('count', 3)
        
        try:
            engine = StockfishService(difficulty=difficulty)
            top_moves = engine.get_top_moves(fen, count=count)
            engine.cleanup()
            
            return Response({
                'success': True,
                'data': {
                    'hints': top_moves
                }
            })
        
        except Exception as e:
            return Response({
                'success': False,
                'error': {'code': 'AI_ERROR', 'message': f'获取提示失败：{str(e)}'}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIAnalyzeView(APIView):
    """
    AI 棋局分析视图
    
    POST: 请求 AI 分析棋局
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """请求 AI 分析棋局"""
        serializer = AIAnalysisRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': '参数验证失败', 'details': serializer.errors}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        fen = serializer.validated_data['fen']
        depth = serializer.validated_data.get('depth', 15)
        
        try:
            engine = StockfishService(difficulty=5)
            evaluation = engine.evaluate_position(fen, depth=depth)
            engine.cleanup()
            
            return Response({
                'success': True,
                'data': evaluation
            })
        
        except Exception as e:
            return Response({
                'success': False,
                'error': {'code': 'AI_ERROR', 'message': f'分析失败：{str(e)}'}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIDifficultyListView(APIView):
    """
    AI 难度列表视图
    
    GET: 获取所有难度等级配置
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """获取所有难度等级配置"""
        difficulties = get_all_difficulties()
        
        data = []
        for diff in difficulties:
            data.append({
                'level': diff.level,
                'name': diff.name,
                'description': f"{diff.elo} Elo",
                'elo_estimate': diff.elo,
                'skill_level': diff.skill_level,
                'search_depth': diff.search_depth,
                'think_time_ms': diff.think_time_ms
            })
        
        return Response({
            'success': True,
            'data': {'difficulties': data}
        })


class AIEngineStatusView(APIView):
    """
    AI 引擎状态视图
    
    GET: 获取引擎池状态
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取引擎池状态"""
        try:
            pool = get_engine_pool()
            
            return Response({
                'success': True,
                'data': {
                    'pool_size': pool.pool_size,
                    'available': pool.available.qsize(),
                    'in_use': len(pool.in_use)
                }
            })
        
        except Exception as e:
            return Response({
                'success': False,
                'error': {'code': 'STATUS_ERROR', 'message': f'获取状态失败：{str(e)}'}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
