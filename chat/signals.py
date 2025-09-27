from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Message, ChatRoom, ChatSettings
from accounts.models import User

@receiver(post_save, sender=Message)
def notify_new_message(sender, instance, created, **kwargs):
    """Уведомление о новом сообщении"""
    if created:
        room = instance.room
        sender_user = instance.sender
        
        # Получаем настройки чата для каждого участника
        for participant in room.participants.exclude(id=sender_user.id):
            # Проверяем настройки уведомлений
            chat_settings, created = ChatSettings.objects.get_or_create(user=participant)
            
            if chat_settings.notifications_enabled and chat_settings.message_notifications:
                # Отправляем email уведомление
                if participant.email:
                    try:
                        subject = f'Новое сообщение в чате'
                        message_content = f'''
                        Здравствуйте, {participant.get_full_name() or participant.username}!
                        
                        {sender_user.get_full_name() or sender_user.username} отправил новое сообщение в чат:
                        "{instance.content[:100]}{'...' if len(instance.content) > 100 else ''}"
                        
                        Перейдите в чат, чтобы ответить.
                        
                        С уважением,
                        Онлайн-школа
                        '''
                        
                        send_mail(
                            subject,
                            message_content,
                            settings.DEFAULT_FROM_EMAIL,
                            [participant.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        print(f"Ошибка отправки email: {e}")

@receiver(post_save, sender=ChatRoom)
def create_default_chat_settings(sender, instance, created, **kwargs):
    """Создание настроек чата по умолчанию для новых участников"""
    if created:
        # Создаем настройки чата для создателя
        ChatSettings.objects.get_or_create(user=instance.created_by)

@receiver(post_delete, sender=Message)
def cleanup_message_files(sender, instance, **kwargs):
    """Очистка файлов при удалении сообщения"""
    # Удаляем прикрепленные файлы
    if instance.file:
        try:
            instance.file.delete(save=False)
        except Exception as e:
            print(f"Ошибка удаления файла: {e}")
    
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception as e:
            print(f"Ошибка удаления изображения: {e}")