"""
Unit tests for User model.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """User 模型测试"""
    
    def test_create_user_success(self):
        """测试成功创建用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('SecurePass123')
        assert user.elo_rating == 1500
        assert user.status == 'active'
        assert user.is_verified is False
        assert user.is_active is True
        assert user.id is not None
    
    def test_create_user_without_email_raises_error(self):
        """测试创建用户时缺少邮箱抛出错误"""
        with pytest.raises(ValueError, match='Users must have an email address'):
            User.objects.create_user(
                username='testuser',
                email=None,
                password='SecurePass123'
            )
    
    def test_create_user_without_username_raises_error(self):
        """测试创建用户时缺少用户名抛出错误"""
        with pytest.raises(ValueError, match='Users must have a username'):
            User.objects.create_user(
                username='',
                email='test@example.com',
                password='SecurePass123'
            )
    
    def test_create_superuser_success(self):
        """测试成功创建超级用户"""
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123'
        )
        
        assert superuser.username == 'admin'
        assert superuser.email == 'admin@example.com'
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        assert superuser.is_verified is True
    
    def test_create_superuser_without_is_staff_raises_error(self):
        """测试创建超级用户时 is_staff 必须为 True"""
        with pytest.raises(ValueError, match='Superuser must have is_staff=True'):
            User.objects.create_superuser(
                username='admin2',
                email='admin2@example.com',
                password='AdminPass123',
                is_staff=False
            )
    
    def test_create_superuser_without_is_superuser_raises_error(self):
        """测试创建超级用户时 is_superuser 必须为 True"""
        with pytest.raises(ValueError, match='Superuser must have is_superuser=True'):
            User.objects.create_superuser(
                username='admin3',
                email='admin3@example.com',
                password='AdminPass123',
                is_superuser=False
            )
    
    def test_user_email_unique_constraint(self):
        """测试邮箱唯一性约束"""
        User.objects.create_user(
            username='user1',
            email='unique@example.com',
            password='SecurePass123'
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='unique@example.com',
                password='SecurePass123'
            )
    
    def test_user_username_unique_constraint(self):
        """测试用户名唯一性约束"""
        User.objects.create_user(
            username='uniqueuser',
            email='email1@example.com',
            password='SecurePass123'
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='uniqueuser',
                email='email2@example.com',
                password='SecurePass123'
            )
    
    def test_user_password_hashed(self):
        """测试密码被哈希存储"""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='SecurePass123'
        )
        
        # 密码不应该是明文
        assert user.password != 'SecurePass123'
        assert user.password.startswith('pbkdf2_')  # Django 默认使用 PBKDF2
    
    def test_user_str_representation(self):
        """测试用户的字符串表示"""
        user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='SecurePass123'
        )
        
        assert str(user) == 'testuser3'
    
    def test_user_get_full_name(self):
        """测试获取用户全名"""
        user = User.objects.create_user(
            username='testuser4',
            email='test4@example.com',
            password='SecurePass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.get_full_name() == 'John Doe'
    
    def test_user_get_short_name(self):
        """测试获取用户短名"""
        user = User.objects.create_user(
            username='testuser5',
            email='test5@example.com',
            password='SecurePass123',
            first_name='John'
        )
        
        assert user.get_short_name() == 'John'
    
    def test_user_default_elo_rating(self):
        """测试用户默认 Elo 评分"""
        user = User.objects.create_user(
            username='testuser6',
            email='test6@example.com',
            password='SecurePass123'
        )
        
        assert user.elo_rating == 1500
    
    def test_user_default_status(self):
        """测试用户默认状态"""
        user = User.objects.create_user(
            username='testuser7',
            email='test7@example.com',
            password='SecurePass123'
        )
        
        assert user.status == 'active'
    
    def test_user_update_elo_rating(self):
        """测试更新用户 Elo 评分"""
        user = User.objects.create_user(
            username='testuser8',
            email='test8@example.com',
            password='SecurePass123'
        )
        
        user.elo_rating = 1600
        user.save()
        
        user.refresh_from_db()
        assert user.elo_rating == 1600
    
    def test_user_update_status(self):
        """测试更新用户状态"""
        user = User.objects.create_user(
            username='testuser9',
            email='test9@example.com',
            password='SecurePass123'
        )
        
        user.status = 'banned'
        user.save()
        
        user.refresh_from_db()
        assert user.status == 'banned'
    
    def test_user_soft_delete(self):
        """测试用户软删除"""
        user = User.objects.create_user(
            username='testuser10',
            email='test10@example.com',
            password='SecurePass123'
        )
        
        # 初始时 deleted_at 应该为 None
        assert user.deleted_at is None
        
        # 软删除（实际项目中会实现软删除逻辑）
        # 这里只是测试字段存在
        from django.utils import timezone
        user.deleted_at = timezone.now()
        user.save()
        
        user.refresh_from_db()
        assert user.deleted_at is not None
