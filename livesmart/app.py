# livesmart/apps.py
from django.apps import AppConfig

class LivesmartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'livesmart'
    verbose_name = 'LiveSmart интеграция'
    
    def ready(self):
        import livesmart.signals  # noqa