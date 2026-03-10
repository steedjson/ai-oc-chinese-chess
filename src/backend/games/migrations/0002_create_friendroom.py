# Generated manually on 2026-03-10
# Creates FriendRoom model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FriendRoom',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_code', models.CharField(max_length=10, unique=True, verbose_name='房间号')),
                ('status', models.CharField(choices=[('waiting', '等待中'), ('playing', '对局中'), ('finished', '已结束'), ('expired', '已过期')], default='waiting', max_length=20, verbose_name='房间状态')),
                ('expires_at', models.DateTimeField(verbose_name='过期时间')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='结束时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_friend_rooms', to=settings.AUTH_USER_MODEL, verbose_name='创建者')),
                ('game', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='friend_room', to='games.game', verbose_name='关联游戏')),
            ],
            options={
                'verbose_name': '好友对战房间',
                'verbose_name_plural': '好友对战房间',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['room_code'], name='games_frien_room_co_14b78b_idx'),
                    models.Index(fields=['status'], name='games_frien_status_1e93be_idx'),
                    models.Index(fields=['creator'], name='games_frien_creator_4eb3de_idx'),
                    models.Index(fields=['expires_at'], name='games_frien_expires_fe1df0_idx'),
                ],
            },
        ),
    ]
