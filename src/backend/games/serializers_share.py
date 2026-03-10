"""
棋局分享序列化器
"""
from rest_framework import serializers
from games.models import GameShare


class GameShareSerializer(serializers.ModelSerializer):
    """棋局分享序列化器"""
    
    shared_by_username = serializers.CharField(source='shared_by.username', read_only=True)
    share_url = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = GameShare
        fields = [
            'id', 'game_id', 'shared_by', 'shared_by_username',
            'share_token', 'share_type', 'has_password',
            'is_active', 'expires_at', 'view_count',
            'created_at', 'updated_at', 'description',
            'share_url', 'qr_code_url'
        ]
        read_only_fields = ['id', 'share_token', 'created_at', 'updated_at', 'view_count']
    
    def get_share_url(self, obj) -> str:
        """获取分享链接"""
        request = self.context.get('request')
        return obj.get_share_url(request)
    
    def get_qr_code_url(self, obj) -> str:
        """获取二维码 URL"""
        # 使用第三方 API 生成二维码
        share_url = obj.get_share_url()
        return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={share_url}"


class GameShareCreateSerializer(serializers.Serializer):
    """棋局分享创建序列化器"""
    
    SHARE_TYPE_CHOICES = [
        ('public', '公开分享'),
        ('private', '私密分享'),
        ('link', '链接分享'),
    ]
    
    share_type = serializers.ChoiceField(
        choices=SHARE_TYPE_CHOICES,
        default='public',
        help_text='分享类型'
    )
    
    password = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        default='',
        help_text='分享密码（私密分享需要）'
    )
    
    expiry_days = serializers.IntegerField(
        min_value=0,
        max_value=365,
        default=7,
        help_text='过期天数（0 表示永不过期）'
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        default='',
        help_text='分享说明'
    )
    
    def validate(self, attrs):
        """验证数据"""
        share_type = attrs.get('share_type')
        password = attrs.get('password')
        
        # 私密分享必须有密码
        if share_type == 'private' and not password:
            raise serializers.ValidationError("私密分享必须设置密码")
        
        return attrs
