from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """Отправка приветственного письма при регистрации"""
    if created and instance.email:
        subject = 'Добро пожаловать в онлайн-школу!'
        message = f'''
        Здравствуйте, {instance.get_full_name() or instance.username}!
        
        Спасибо за регистрацию в нашей онлайн-школе.
        Ваши учетные данные:
        Логин: {instance.username}
        Роль: {instance.get_role_display()}
        
        С уважением,
        Команда онлайн-школы
        '''
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
