"""
游戏对局 URL 路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GameViewSet, UserGamesViewSet
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
from .views.friend_room_views import (
    FriendRoomViewSet,
    friend_room_join_view,
    friend_room_my_rooms_view,
    friend_room_active_rooms_view,
)

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'users/(?P<user_id>[^/.]+)/games', UserGamesViewSet, basename='user-games')
router.register(r'games', SpectatorViewSet, basename='spectator')
router.register(r'chat', ChatMessageViewSet, basename='chat')
router.register(r'management/games', GameManagementViewSet, basename='game-management')
router.register(r'friend/rooms', FriendRoomViewSet, basename='friend-room')

urlpatterns = [
    path('', include(router.urls)),
    # 好友对战房间
    path('friend/create/', friend_room_my_rooms_view, name='friend-room-create'),
    path('friend/join/', friend_room_join_view, name='friend-room-join'),
    path('friend/my-rooms/', friend_room_my_rooms_view, name='friend-room-my-rooms'),
    path('friend/active-rooms/', friend_room_active_rooms_view, name='friend-room-active-rooms'),
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
]
