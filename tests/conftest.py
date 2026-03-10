"""
pytest configuration.
"""

import pytest
import os
import sys
import django
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent / 'src' / 'backend'
sys.path.insert(0, str(backend_dir))

# 设置 Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


@pytest.fixture(scope='session', autouse=True)
def setup_django():
    """设置 Django"""
    django.setup()


# 禁用测试数据库序列化以避免表不存在的问题
@pytest.fixture(scope='session')
def django_db_use_migrations():
    return True


@pytest.fixture
def api_client():
    """API 客户端"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def test_user(db):
    """测试用户夹具"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='SecurePass123'
    )
