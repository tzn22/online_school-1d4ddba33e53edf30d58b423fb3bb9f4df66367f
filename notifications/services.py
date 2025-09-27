import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Notification, NotificationLog, UserNotificationSettings
from accounts.models import User

logger = logging.getLogger(__name__)

class NotificationService:
    """Сервис для отправки уведомлений"""
    
    @staticmethod
    def send_notification(user, title, message, notification_type='info', channels=None):
        """Отправка уведомления пользователю"""
        if channels is None:
            channels = ['in_app']
        
        # Создаем уведомление в БД
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            channel=channels[0] if channels else 'in_app'
        )
        
        # Отправляем через указанные каналы
        for channel in channels:
            try:
                if channel == 'email':
                    NotificationService._send_email(user, title, message, notification)
                elif channel == 'telegram':
                    NotificationService._send_telegram(user, title, message, notification)
                elif channel == 'whatsapp':
                    NotificationService._send_whatsapp(user, title, message, notification)
                elif channel == 'sms':
                    NotificationService._send_sms(user, title, message, notification)
                elif channel == 'in_app':
                    # In-app уведомление уже создано
                    pass
                
                # Логируем успешную отправку
                NotificationLog.objects.create(
                    notification=notification,
                    channel=channel,
                    status='sent',
                    sent_at=timezone.now()
                )
                
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления через {channel}: {str(e)}")
                # Логируем ошибку
                NotificationLog.objects.create(
                    notification=notification,
                    channel=channel,
                    status='failed',
                    error_message=str(e)
                )
        
        return notification
    
    @staticmethod
    def _send_email(user, title, message, notification):
        """Отправка email уведомления"""
        # Проверяем настройки пользователя
        settings, created = UserNotificationSettings.objects.get_or_create(user=user)
        if not settings.email_notifications:
            return
        
        if user.email:
            try:
                send_mail(
                    subject=title,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                raise Exception(f"Ошибка отправки email: {str(e)}")
    
    @staticmethod
    def _send_telegram(user, title, message, notification):
        """Отправка Telegram уведомления"""
        # Проверяем настройки пользователя
        settings, created = UserNotificationSettings.objects.get_or_create(user=user)
        if not settings.telegram_notifications or not settings.telegram_chat_id:
            return
        
        # Здесь будет интеграция с Telegram Bot API
        # Пока заглушка
        logger.info(f"Telegram уведомление для {user.username}: {title}")
    
    @staticmethod
    def _send_whatsapp(user, title, message, notification):
        """Отправка WhatsApp уведомления"""
        # Проверяем настройки пользователя
        settings, created = UserNotificationSettings.objects.get_or_create(user=user)
        if not settings.whatsapp_notifications or not settings.whatsapp_phone:
            return
        
        # Здесь будет интеграция с WhatsApp Business API
        # Пока заглушка
        logger.info(f"WhatsApp уведомление для {user.username}: {title}")
    
    @staticmethod
    def _send_sms(user, title, message, notification):
        """Отправка SMS уведомления"""
        # Проверяем настройки пользователя
        settings, created = UserNotificationSettings.objects.get_or_create(user=user)
        if not settings.sms_notifications or not settings.sms_phone:
            return
        
        # Здесь будет интеграция с SMS провайдером
        # Пока заглушка
        logger.info(f"SMS уведомление для {user.username}: {title}")
    
    @staticmethod
    def send_bulk_notification(user_ids=None, roles=None, title=None, message=None, 
                             notification_type='info', channels=None):
        """Массовая отправка уведомлений"""
        if channels is None:
            channels = ['in_app']
        
        # Получаем пользователей
        users = User.objects.all()
        if user_ids:
            users = users.filter(id__in=user_ids)
        if roles:
            users = users.filter(role__in=roles)
        
        notifications = []
        for user in users:
            notification = NotificationService.send_notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                channels=channels
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def mark_as_read(notification_id, user):
        """Отметить уведомление как прочитанное"""
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save()
            return notification
        except Notification.DoesNotExist:
            return None
    
    @staticmethod
    def get_unread_count(user):
        """Получить количество непрочитанных уведомлений"""
        return Notification.objects.filter(user=user, is_read=False).count()