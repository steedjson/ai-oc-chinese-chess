"""
匹配系统 Django 模型测试
"""
import pytest
import uuid
from django.utils import timezone
from datetime import timedelta
from matchmaking.models import (
    MatchQueue,
    MatchHistory,
    PlayerRank,
    Season,
    MatchQueueStatus,
    MatchResult,
    RankSegment,
)


@pytest.mark.django_db
class TestMatchQueueModel:
    """测试 MatchQueue 模型"""
    
    def test_create_match_queue(self):
        """创建匹配队列记录"""
        queue = MatchQueue.objects.create(
            user_id='user123',
            game_type='online',
            rating=1500,
            search_range=100,
            status=MatchQueueStatus.SEARCHING
        )
        
        assert queue.user_id == 'user123'
        assert queue.game_type == 'online'
        assert queue.rating == 1500
        assert queue.status == MatchQueueStatus.SEARCHING
        assert queue.created_at is not None
    
    def test_queue_str(self):
        """测试字符串表示"""
        queue = MatchQueue.objects.create(
            user_id='user456',
            game_type='ranked',
            rating=1600,
            status=MatchQueueStatus.SEARCHING
        )
        
        queue_str = str(queue)
        assert 'user456' in queue_str
        assert 'ranked' in queue_str
    
    def test_is_timeout_false(self):
        """测试超时检查 - 未超时"""
        queue = MatchQueue.objects.create(
            user_id='user789',
            game_type='online',
            rating=1500,
            status=MatchQueueStatus.SEARCHING
        )
        
        # 刚创建，不应该超时（180 秒）
        assert queue.is_timeout() is False
    
    def test_get_wait_time(self):
        """测试获取等待时间"""
        import time
        queue = MatchQueue.objects.create(
            user_id='user111',
            game_type='online',
            rating=1500,
            status=MatchQueueStatus.SEARCHING
        )
        
        # 等待一小段时间
        time.sleep(0.01)
        
        wait_time = queue.get_wait_time()
        assert wait_time >= 0
    
    def test_mark_matched(self):
        """测试标记为已匹配"""
        game_id = uuid.uuid4()
        queue = MatchQueue.objects.create(
            user_id='user123',
            game_type='online',
            rating=1500,
            status=MatchQueueStatus.SEARCHING
        )
        
        queue.mark_matched('user456', game_id)
        
        assert queue.status == MatchQueueStatus.MATCHED
        assert queue.opponent_id == 'user456'
        assert queue.game_id == game_id
        assert queue.matched_at is not None
    
    def test_mark_cancelled(self):
        """测试标记为已取消"""
        queue = MatchQueue.objects.create(
            user_id='user123',
            game_type='online',
            rating=1500,
            status=MatchQueueStatus.SEARCHING
        )
        
        queue.mark_cancelled()
        
        assert queue.status == MatchQueueStatus.CANCELLED


@pytest.mark.django_db
class TestMatchHistoryModel:
    """测试 MatchHistory 模型"""
    
    def test_create_match_history(self):
        """创建匹配历史记录"""
        game_id = uuid.uuid4()
        history = MatchHistory.objects.create(
            user_id='user123',
            opponent_id='user456',
            game_id=game_id,
            user_rating=1500,
            opponent_rating=1480,
            rating_change=15,
            result=MatchResult.WIN,
            match_duration=120
        )
        
        assert history.user_id == 'user123'
        assert history.opponent_id == 'user456'
        assert history.game_id == game_id
        assert history.result == MatchResult.WIN
        assert history.rating_change == 15
    
    def test_history_str(self):
        """测试字符串表示"""
        game_id = uuid.uuid4()
        history = MatchHistory.objects.create(
            user_id='user123',
            opponent_id='user456',
            game_id=game_id,
            user_rating=1500,
            opponent_rating=1480,
            result=MatchResult.WIN
        )
        
        history_str = str(history)
        assert 'user123' in history_str
        assert 'user456' in history_str
    
    def test_get_rating_diff(self):
        """测试获取等级分差"""
        game_id = uuid.uuid4()
        history = MatchHistory.objects.create(
            user_id='user123',
            opponent_id='user456',
            game_id=game_id,
            user_rating=1500,
            opponent_rating=1600,
            result=MatchResult.LOSS
        )
        
        diff = history.get_rating_diff()
        assert diff == -100
    
    def test_is_win(self):
        """测试是否胜利"""
        game_id = uuid.uuid4()
        history = MatchHistory.objects.create(
            user_id='user123',
            opponent_id='user456',
            game_id=game_id,
            user_rating=1500,
            opponent_rating=1480,
            result=MatchResult.WIN
        )
        
        assert history.is_win() is True
        assert history.is_loss() is False
        assert history.is_draw() is False


@pytest.mark.django_db
class TestPlayerRankModel:
    """测试 PlayerRank 模型"""
    
    def test_create_player_rank(self):
        """创建玩家段位记录"""
        rank = PlayerRank.objects.create(
            user_id='user123',
            rating=1500,
            segment=RankSegment.GOLD,
            season_id=1
        )
        
        assert rank.user_id == 'user123'
        assert rank.rating == 1500
        assert rank.segment == RankSegment.GOLD
        assert rank.season_id == 1
    
    def test_rank_str(self):
        """测试字符串表示"""
        rank = PlayerRank.objects.create(
            user_id='user123',
            rating=1600,
            segment=RankSegment.PLATINUM,
            season_id=1
        )
        
        rank_str = str(rank)
        assert 'user123' in rank_str
        # 避免递归，直接检查 segment 值
        assert rank.segment == RankSegment.PLATINUM
    
    def test_get_segment_display(self):
        """测试获取段位显示名称"""
        rank = PlayerRank.objects.create(
            user_id='user123',
            rating=1500,
            segment=RankSegment.GOLD,
            season_id=1
        )
        
        # 使用 get_segment_display() 方法
        segment_display = rank.get_segment_display()
        assert segment_display == '黄金'
    
    def test_get_win_rate(self):
        """测试获取胜率"""
        rank = PlayerRank.objects.create(
            user_id='user123',
            rating=1500,
            segment=RankSegment.GOLD,
            season_id=1,
            total_games=10,
            wins=6,
            losses=3,
            draws=1
        )
        
        win_rate = rank.get_win_rate()
        assert win_rate == 60.0
    
    def test_update_stats(self):
        """测试更新统计数据"""
        rank = PlayerRank.objects.create(
            user_id='user123',
            rating=1500,
            segment=RankSegment.GOLD,
            season_id=1,
            total_games=0,
            wins=0,
            losses=0,
            draws=0
        )
        
        rank.update_stats(MatchResult.WIN)
        
        assert rank.total_games == 1
        assert rank.wins == 1
    
    def test_update_rating(self):
        """测试更新等级分"""
        rank = PlayerRank.objects.create(
            user_id='user123',
            rating=1500,
            segment=RankSegment.GOLD,
            season_id=1,
            peak_rating=1500
        )
        
        rank.update_rating(1550)
        
        assert rank.rating == 1550
        assert rank.peak_rating == 1550
        assert rank.segment == RankSegment.PLATINUM  # 1550 应该是铂金


@pytest.mark.django_db
class TestSeasonModel:
    """测试 Season 模型"""
    
    def test_create_season(self):
        """创建赛季配置"""
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=90)
        
        season = Season.objects.create(
            name='2026 春季赛',
            season_number=1,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        assert season.name == '2026 春季赛'
        assert season.season_number == 1
        assert season.is_active is True
    
    def test_season_str(self):
        """测试字符串表示"""
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=90)
        
        season = Season.objects.create(
            name='2026 夏季赛',
            season_number=2,
            start_date=start_date,
            end_date=end_date
        )
        
        assert str(season) == '2026 夏季赛'
    
    def test_is_current_season(self):
        """测试是否为当前赛季"""
        start_date = timezone.now().date() - timedelta(days=10)
        end_date = timezone.now().date() + timedelta(days=80)
        
        season = Season.objects.create(
            name='当前赛季',
            season_number=1,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        assert season.is_current_season() is True
    
    def test_is_not_current_season(self):
        """测试是否不是当前赛季"""
        start_date = timezone.now().date() - timedelta(days=200)
        end_date = timezone.now().date() - timedelta(days=110)
        
        season = Season.objects.create(
            name='过去赛季',
            season_number=0,
            start_date=start_date,
            end_date=end_date,
            is_active=False
        )
        
        assert season.is_current_season() is False
    
    def test_days_remaining(self):
        """测试获取剩余天数"""
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=90)
        
        season = Season.objects.create(
            name='2026 赛季',
            season_number=1,
            start_date=start_date,
            end_date=end_date
        )
        
        remaining = season.days_remaining()
        assert 89 <= remaining <= 90


@pytest.mark.django_db
class TestMatchQueueQuerySet:
    """测试 MatchQueue 查询集"""
    
    def test_active_queues(self):
        """测试获取活跃队列"""
        # 创建活跃队列
        queue1 = MatchQueue.objects.create(
            user_id='user1',
            game_type='online',
            rating=1500,
            status=MatchQueueStatus.SEARCHING
        )
        
        # 创建已取消队列
        queue2 = MatchQueue.objects.create(
            user_id='user2',
            game_type='online',
            rating=1600,
            status=MatchQueueStatus.CANCELLED
        )
        
        # 获取活跃队列
        active = MatchQueue.objects.active()
        
        assert queue1 in active
        assert queue2 not in active
    
    def test_searching_queues(self):
        """测试获取搜索中队列"""
        queue1 = MatchQueue.objects.create(
            user_id='user1',
            game_type='online',
            rating=1500,
            status=MatchQueueStatus.SEARCHING
        )
        
        queue2 = MatchQueue.objects.create(
            user_id='user2',
            game_type='online',
            rating=1600,
            status=MatchQueueStatus.CANCELLED
        )
        
        searching = MatchQueue.objects.searching()
        
        assert queue1 in searching
        assert queue2 not in searching


@pytest.mark.django_db
class TestMatchHistoryQuerySet:
    """测试 MatchHistory 查询集"""
    
    def test_user_history(self):
        """测试获取用户历史"""
        user_id = 'user123'
        game_id1 = uuid.uuid4()
        game_id2 = uuid.uuid4()
        
        history1 = MatchHistory.objects.create(
            user_id=user_id,
            opponent_id='user456',
            game_id=game_id1,
            user_rating=1500,
            opponent_rating=1480,
            result=MatchResult.WIN
        )
        
        history2 = MatchHistory.objects.create(
            user_id='user999',
            opponent_id='user888',
            game_id=game_id2,
            user_rating=1600,
            opponent_rating=1580,
            result=MatchResult.LOSS
        )
        
        user_history = MatchHistory.objects.for_user(user_id)
        
        assert history1 in user_history
        assert history2 not in user_history
    
    def test_wins_only(self):
        """测试只获取胜利记录"""
        user_id = 'user123'
        game_id1 = uuid.uuid4()
        game_id2 = uuid.uuid4()
        
        win = MatchHistory.objects.create(
            user_id=user_id,
            opponent_id='user456',
            game_id=game_id1,
            user_rating=1500,
            opponent_rating=1480,
            result=MatchResult.WIN
        )
        
        loss = MatchHistory.objects.create(
            user_id=user_id,
            opponent_id='user789',
            game_id=game_id2,
            user_rating=1500,
            opponent_rating=1600,
            result=MatchResult.LOSS
        )
        
        wins = MatchHistory.objects.wins()
        
        assert win in wins
        assert loss not in wins
