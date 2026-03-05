# Generated migration for Spectator model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Spectator',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('watching', '观战中'), ('left', '已离开'), ('kicked', '被踢出')], default='watching', max_length=20)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('left_at', models.DateTimeField(blank=True, null=True)),
                ('duration', models.IntegerField(blank=True, help_text='观战时长（秒）', null=True)),
                ('is_anonymous', models.BooleanField(default=False, help_text='是否匿名观战')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spectators', to='games.game')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spectated_games', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'spectators',
                'ordering': ['-joined_at'],
            },
        ),
        migrations.AddIndex(
            model_name='spectator',
            index=models.Index(fields=['game', 'status'], name='spectators_game_st_8d0f2a_idx'),
        ),
        migrations.AddIndex(
            model_name='spectator',
            index=models.Index(fields=['user', 'status'], name='spectators_user_st_9e1f3b_idx'),
        ),
        migrations.AddIndex(
            model_name='spectator',
            index=models.Index(fields=['-joined_at'], name='spectators_joined_1a2b3c_idx'),
        ),
        migrations.AddConstraint(
            model_name='spectator',
            constraint=models.UniqueConstraint(fields=('game', 'user'), name='unique_spectator_per_game'),
        ),
    ]
