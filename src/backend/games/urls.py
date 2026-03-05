"""
游戏对局 URL 路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GameViewSet, UserGamesViewSet

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'users/(?P<user_id>[^/.]+)/games', UserGamesViewSet, basename='user-games')

urlpatterns = [
    path('', include(router.urls)),
]
