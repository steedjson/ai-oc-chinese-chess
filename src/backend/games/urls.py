"""
游戏对局 URL 路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GameViewSet, UserGamesViewSet
from .spectator_views import SpectatorViewSet, get_spectator_info

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'users/(?P<user_id>[^/.]+)/games', UserGamesViewSet, basename='user-games')
router.register(r'games', SpectatorViewSet, basename='spectator')

urlpatterns = [
    path('', include(router.urls)),
    # 观战者详细信息
    path('games/<uuid:game_id>/spectators/<uuid:spectator_id>/', get_spectator_info, name='spectator-info'),
]
