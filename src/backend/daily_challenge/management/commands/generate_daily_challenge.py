"""
生成明日挑战的管理命令

使用方法:
    python manage.py generate_daily_challenge
    
可添加 --date 参数指定日期:
    python manage.py generate_daily_challenge --date 2026-03-07
"""

from django.core.management.base import BaseCommand
from datetime import date, timedelta
from daily_challenge.services import DailyChallengeService


class Command(BaseCommand):
    help = '生成每日挑战（默认生成明日挑战）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='指定日期 (YYYY-MM-DD)，默认为明天'
        )

    def handle(self, *args, **options):
        if options['date']:
            try:
                challenge_date = date.fromisoformat(options['date'])
            except ValueError:
                self.stderr.write(self.style.ERROR(f'无效的日期格式：{options["date"]}'))
                return
        else:
            challenge_date = date.today() + timedelta(days=1)

        self.stdout.write(f'正在生成 {challenge_date} 的每日挑战...')

        try:
            challenge = DailyChallengeService.generate_tomorrow_challenge()
            
            # 如果生成的日期不匹配，手动设置
            if challenge.date != challenge_date:
                challenge.date = challenge_date
                challenge.save()

            self.stdout.write(self.style.SUCCESS(f'✓ 挑战创建成功！'))
            self.stdout.write(f'  日期：{challenge.date}')
            self.stdout.write(f'  难度：{challenge.difficulty}')
            self.stdout.write(f'  星级：{challenge.stars}')
            self.stdout.write(f'  时间限制：{challenge.time_limit}秒')
            self.stdout.write(f'  最大步数：{challenge.max_moves}')
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'✗ 创建失败：{str(e)}'))
