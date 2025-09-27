from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
import time

class Command(BaseCommand):
    help = 'Ожидание доступности базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Таймаут ожидания в секундах'
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        start_time = time.time()
        
        self.stdout.write('Ожидание доступности базы данных...')
        
        while time.time() - start_time < timeout:
            try:
                connection.ensure_connection()
                self.stdout.write(
                    self.style.SUCCESS('✅ База данных доступна!')
                )
                return
            except OperationalError:
                self.stdout.write('База данных недоступна, ждем...')
                time.sleep(1)
        
        self.stdout.write(
            self.style.ERROR('❌ Таймаут ожидания базы данных')
        )