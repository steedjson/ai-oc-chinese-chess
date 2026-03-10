"""
残局挑战应用
"""
from django.apps import AppConfig


class PuzzlesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'puzzles'
    verbose_name = '残局挑战'
    
    def ready(self):
        """应用就绪时执行"""
        # 可以在这里导入信号处理等
        pass
