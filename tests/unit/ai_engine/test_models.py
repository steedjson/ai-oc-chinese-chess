"""
AI Engine 模型测试

测试 AI 对局、难度配置、分析结果等模型
"""
import pytest
from django.utils import timezone
from uuid import uuid4

from ai_engine.models import AIDifficulty, AIGame, AIAnalysis


@pytest.mark.django_db
class TestAIDifficultyModel:
    """AI 难度配置模型测试"""
    
    def test_create_difficulty(self):
        """测试创建难度配置"""
        difficulty = AIDifficulty.objects.create(
            level=5,
            name="中级",
            description="适合普通玩家",
            skill_level=8,
            search_depth=13,
            think_time_ms=1500,
            elo_estimate=1200
        )
        
        assert difficulty.level == 5
        assert difficulty.name == "中级"
        assert difficulty.elo_estimate == 1200
        assert difficulty.is_active is True
    
    def test_difficulty_str_representation(self):
        """测试难度配置的字符串表示"""
        difficulty = AIDifficulty.objects.create(
            level=3,
            name="初级",
            skill_level=4,
            search_depth=9,
            think_time_ms=1000,
            elo_estimate=800
        )
        
        assert str(difficulty) == "难度 3 - 初级 (800 Elo)"
    
    def test_difficulty_unique_level(self):
        """测试难度等级唯一性"""
        AIDifficulty.objects.create(
            level=7,
            name="高级",
            skill_level=12,
            search_depth=17,
            think_time_ms=2000,
            elo_estimate=1600
        )
        
        with pytest.raises(Exception):
            AIDifficulty.objects.create(
                level=7,  # 重复的等级
                name="高级 2",
                skill_level=12,
                search_depth=17,
                think_time_ms=2000,
                elo_estimate=1600
            )
    
    def test_difficulty_ordering(self):
        """测试难度配置按等级排序"""
        AIDifficulty.objects.create(level=5, name="中级", skill_level=8, search_depth=13, think_time_ms=1500, elo_estimate=1200)
        AIDifficulty.objects.create(level=1, name="入门", skill_level=0, search_depth=5, think_time_ms=500, elo_estimate=400)
        AIDifficulty.objects.create(level=10, name="大师", skill_level=20, search_depth=25, think_time_ms=5000, elo_estimate=2200)
        
        difficulties = list(AIDifficulty.objects.all())
        
        assert difficulties[0].level == 1
        assert difficulties[1].level == 5
        assert difficulties[2].level == 10


@pytest.mark.django_db
class TestAIGameModel:
    """AI 对局记录模型测试"""
    
    def test_create_ai_game(self):
        """测试创建 AI 对局"""
        from users.models import User
        
        # 创建测试用户
        player = User.objects.create_user(
            username='testplayer',
            email='test@example.com',
            password='testpass123'
        )
        
        game = AIGame.objects.create(
            player=player,
            ai_level=5,
            ai_side='black',
            fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_history=[],
            status='playing'
        )
        
        assert game.player == player
        assert game.ai_level == 5
        assert game.ai_side == 'black'
        assert game.status == 'playing'
        assert game.total_moves == 0
    
    def test_game_str_representation(self):
        """测试对局的字符串表示"""
        from users.models import User
        player = User.objects.create_user(username='testplayer2', email='test2@example.com', password='testpass123')
        
        game = AIGame.objects.create(
            player=player,
            ai_level=3,
            ai_side='red',
            fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_history=[],
            status='pending'
        )
        
        assert f"AI 对局 {game.id}" in str(game)
        assert "难度 3" in str(game)
    
    def test_game_status_choices(self):
        """测试对局状态选择"""
        from users.models import User
        valid_statuses = ['pending', 'playing', 'red_win', 'black_win', 'draw', 'aborted']
        
        for i, status in enumerate(valid_statuses):
            player = User.objects.create_user(username=f'testplayer{i}', email=f'test{i}@example.com', password='testpass123')
            game = AIGame.objects.create(
                player=player,
                ai_level=5,
                ai_side='black',
                fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
                fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
                move_history=[],
                status=status
            )
            assert game.status == status
    
    def test_game_finish(self):
        """测试对局结束"""
        from users.models import User
        player = User.objects.create_user(username='testplayer_finish', email='test_finish@example.com', password='testpass123')
        
        game = AIGame.objects.create(
            player=player,
            ai_level=5,
            ai_side='black',
            fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_history=[],
            status='playing'
        )
        
        # 更新对局为结束状态
        game.status = 'red_win'
        game.winner = 'red'
        game.finished_at = timezone.now()
        game.save()
        
        assert game.status == 'red_win'
        assert game.winner == 'red'
        assert game.finished_at is not None
    
    def test_game_move_history(self):
        """测试对局走棋历史"""
        from users.models import User
        player = User.objects.create_user(username='testplayer_history', email='test_history@example.com', password='testpass123')
        
        game = AIGame.objects.create(
            player=player,
            ai_level=5,
            ai_side='black',
            fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_history=[],
            status='playing'
        )
        
        # 添加走棋历史
        game.move_history = [
            {"from": "c1", "to": "c4", "piece": "C"},
            {"from": "h2", "to": "h5", "piece": "C"},
        ]
        game.total_moves = 2
        game.save()
        
        assert len(game.move_history) == 2
        assert game.total_moves == 2
    
    def test_game_performance_metrics(self):
        """测试对局性能指标"""
        from users.models import User
        player = User.objects.create_user(username='testplayer_perf', email='test_perf@example.com', password='testpass123')
        
        game = AIGame.objects.create(
            player=player,
            ai_level=5,
            ai_side='black',
            fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_history=[],
            status='playing'
        )
        
        # 更新性能指标
        game.avg_think_time_ms = 1500
        game.max_think_time_ms = 3000
        game.avg_search_depth = 13
        game.save()
        
        assert game.avg_think_time_ms == 1500
        assert game.max_think_time_ms == 3000
        assert game.avg_search_depth == 13


@pytest.mark.django_db
class TestAIAnalysisModel:
    """AI 棋局分析结果模型测试"""
    
    def test_create_analysis(self):
        """测试创建分析结果"""
        from users.models import User
        player = User.objects.create_user(username='testplayer_analysis', email='test_analysis@example.com', password='testpass123')
        
        game = AIGame.objects.create(
            player=player,
            ai_level=5,
            ai_side='black',
            fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_history=[],
            status='playing'
        )
        
        analysis = AIAnalysis.objects.create(
            game=game,
            fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_number=1,
            evaluation_score=0.35,
            evaluation_text="红方稍优",
            best_move="c1c4",
            search_depth=15,
            thinking_time_ms=1500
        )
        
        assert analysis.game == game
        assert analysis.move_number == 1
        assert analysis.evaluation_score == 0.35
        assert analysis.evaluation_text == "红方稍优"
        assert analysis.best_move == "c1c4"
    
    def test_analysis_str_representation(self):
        """测试分析结果的字符串表示"""
        from users.models import User
        player = User.objects.create_user(username='testplayer_analysis2', email='test_analysis2@example.com', password='testpass123')
        
        game = AIGame.objects.create(
            player=player,
            ai_level=5,
            ai_side='black',
            fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_history=[],
            status='playing'
        )
        
        analysis = AIAnalysis.objects.create(
            game=game,
            fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_number=5,
            evaluation_score=0.5,
            evaluation_text="红方稍优",
            best_move="h2h5",
            search_depth=14,
            thinking_time_ms=1400
        )
        
        assert f"分析 {analysis.id}" in str(analysis)
        assert "第 5 步" in str(analysis)
    
    def test_analysis_top_moves(self):
        """测试顶级走法列表"""
        from users.models import User
        player = User.objects.create_user(username='testplayer_analysis3', email='test_analysis3@example.com', password='testpass123')
        
        game = AIGame.objects.create(
            player=player,
            ai_level=5,
            ai_side='black',
            fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            status='playing'
        )
        
        analysis = AIAnalysis.objects.create(
            game=game,
            fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_number=1,
            evaluation_score=0.35,
            evaluation_text="红方稍优",
            best_move="c1c4",
            search_depth=15,
            thinking_time_ms=1500,
            top_moves=[
                {"from": "c1", "to": "c4", "evaluation": 0.35},
                {"from": "h2", "to": "h5", "evaluation": 0.28},
                {"from": "b1", "to": "c3", "evaluation": 0.22},
            ]
        )
        
        assert len(analysis.top_moves) == 3
        assert analysis.top_moves[0]['from'] == 'c1'
        assert analysis.top_moves[0]['to'] == 'c4'
    
    def test_analysis_ordering(self):
        """测试分析结果按步数排序"""
        from users.models import User
        player = User.objects.create_user(username='testplayer_order', email='test_order@example.com', password='testpass123')
        
        game = AIGame.objects.create(
            player=player,
            ai_level=5,
            ai_side='black',
            fen_start="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            fen_current="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            move_history=[],
            status='playing'
        )
        
        AIAnalysis.objects.create(game=game, fen="fen1", move_number=3, evaluation_score=0.2, evaluation_text="均势", best_move="e2e4", search_depth=12, thinking_time_ms=1200)
        AIAnalysis.objects.create(game=game, fen="fen2", move_number=1, evaluation_score=0.0, evaluation_text="均势", best_move="c1c4", search_depth=10, thinking_time_ms=1000)
        AIAnalysis.objects.create(game=game, fen="fen3", move_number=5, evaluation_score=0.5, evaluation_text="红方稍优", best_move="h2h5", search_depth=14, thinking_time_ms=1400)
        
        analyses = list(AIAnalysis.objects.all())
        
        assert analyses[0].move_number == 1
        assert analyses[1].move_number == 3
        assert analyses[2].move_number == 5
