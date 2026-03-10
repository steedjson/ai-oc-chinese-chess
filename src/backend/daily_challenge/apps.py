"""
每日挑战应用配置
"""

from django.apps import AppConfig


class DailyChallengeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'daily_challenge'
    verbose_name = '每日挑战'
