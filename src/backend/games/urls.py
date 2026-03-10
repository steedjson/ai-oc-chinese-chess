"""
游戏对局 URL 路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    GameViewSet,
    UserGamesViewSet,
    FriendRoomViewSet,
    friend_room_join_view,
    friend_room_my_rooms_view,
    friend_room_active_rooms_view,
)
from .undo_views import UndoRequestView, UndoRespondView, UndoHistoryView
from .share_views import (
    GameShareCreateView,
    GameSharesListView,
    share_detail_view,
    ShareVerifyView,
    ShareDeactivateView,
    MySharesView,
)
from .spectator_views import SpectatorViewSet, get_spectator_info
from .chat_views import ChatMessageViewSet, send_chat_message, get_chat_history
from .ranking_views import (
    DailyLeaderboardView,
    WeeklyLeaderboardView,
    AllTimeLeaderboardView,
    UserRankingView,
    UserRankingStatsView,
    MyRankingView,
    refresh_ranking_cache,
    cleanup_expired_cache,
)
from .management_api import GameManagementViewSet

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'users/(?P<user_id>[^/.]+)/games', UserGamesViewSet, basename='user-games')
router.register(r'games', SpectatorViewSet, basename='spectator')
router.register(r'chat', ChatMessageViewSet, basename='chat')
router.register(r'management/games', GameManagementViewSet, basename='game-management')
# 注意：FriendRoomViewSet 不使用 router，而是使用独立的路由

urlpatterns = [
    path('', include(router.urls)),
    # 好友对战房间 - 独立端点 (具体路径在前，通配符在后)
    path('friend/create/', FriendRoomViewSet.as_view({'post': 'create'}), name='friend-room-create'),
    path('friend/join/', friend_room_join_view, name='friend-room-join'),
    path('friend/my-rooms/', friend_room_my_rooms_view, name='friend-room-my-rooms'),
    path('friend/active-rooms/', friend_room_active_rooms_view, name='friend-room-active-rooms'),
    # 支持两种路径格式：/friend/{room_code}/ 和 /friend/rooms/{room_code}/
    path('friend/<str:room_code>/', FriendRoomViewSet.as_view({'get': 'retrieve'}), name='friend-room-detail'),
    path('friend/rooms/<str:room_code>/', FriendRoomViewSet.as_view({'get': 'retrieve'}), name='friend-room-detail-rooms'),
    # 观战者详细信息
    path('games/<uuid:game_id>/spectators/<uuid:spectator_id>/', get_spectator_info, name='spectator-info'),
    # 聊天独立端点
    path('chat/games/<uuid:game_id>/send/', send_chat_message, name='send-chat-message'),
    path('chat/games/<uuid:game_id>/history/', get_chat_history, name='get-chat-history'),
    
    # 排行榜端点
    path('ranking/daily/', DailyLeaderboardView.as_view(), name='ranking-daily'),
    path('ranking/weekly/', WeeklyLeaderboardView.as_view(), name='ranking-weekly'),
    path('ranking/all-time/', AllTimeLeaderboardView.as_view(), name='ranking-all-time'),
    path('ranking/user/<str:user_id>/', UserRankingView.as_view(), name='ranking-user'),
    path('ranking/user/<str:user_id>/stats/', UserRankingStatsView.as_view(), name='ranking-user-stats'),
    path('ranking/my/', MyRankingView.as_view(), name='ranking-my'),
    
    # 管理端点
    path('ranking/admin/refresh-cache/', refresh_ranking_cache, name='ranking-refresh-cache'),
    path('ranking/admin/cleanup-cache/', cleanup_expired_cache, name='ranking-cleanup-cache'),
    
    # 悔棋功能端点
    path('games/<int:game_id>/undo/request/', UndoRequestView.as_view(), name='undo-request'),
    path('games/<int:game_id>/undo/respond/', UndoRespondView.as_view(), name='undo-respond'),
    path('games/<int:game_id>/undo/requests/', UndoHistoryView.as_view(), name='undo-history'),
    
    # 棋局分享功能端点
    path('games/<int:game_id>/share/', GameShareCreateView.as_view(), name='game-share-create'),
    path('games/<int:game_id>/shares/', GameSharesListView.as_view(), name='game-shares-list'),
    path('share/<str:token>/', share_detail_view, name='share-detail'),
    path('share/<str:token>/verify/', ShareVerifyView.as_view(), name='share-verify'),
    path('share/<int:share_id>/', ShareDeactivateView.as_view(), name='share-deactivate'),
    path('shares/my/', MySharesView.as_view(), name='my-shares'),
]
