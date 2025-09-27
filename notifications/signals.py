from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.utils import timezone  
from django.conf import settings
from .models import Notification, UserNotificationSettings
from accounts.models import User
from courses.models import Lesson
from payments.models import Payment

@receiver(post_save, sender=Notification)
def send_notification_via_channels(sender, instance, created, **kwargs):
    """Отправка уведомления через различные каналы"""
    if created and not instance.is_sent:
        from .services import NotificationService
        
        # Отправляем уведомление через сервис
        try:
            NotificationService.send_notification(
                user=instance.user,
                title=instance.title,
                message=instance.message,
                notification_type=instance.notification_type,
                channels=[instance.channel]
            )
            instance.is_sent = True
            instance.sent_at = timezone.now()
            instance.save()
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")

@receiver(post_save, sender=Lesson)
def notify_lesson_scheduled(sender, instance, created, **kwargs):
    """Уведомление о запланированном занятии"""
    if created:
        # Уведомляем студентов
        recipients = []
        
        if instance.lesson_type == 'group' and instance.group:
            recipients = list(instance.group.students.all())
        elif instance.lesson_type == 'individual' and instance.student:
            recipients = [instance.student]
        
        # Добавляем преподавателя
        if instance.teacher not in recipients:
            recipients.append(instance.teacher)
        
        for recipient in recipients:
            # Создаем уведомление
            Notification.objects.create(
                user=recipient,
                title='Новое занятие',
                message=f'Запланировано новое занятие "{instance.title}" на {instance.start_time.strftime("%d.%m.%Y %H:%M")}',
                notification_type='lesson',
                channel='in_app'
            )

@receiver(post_save, sender=Payment)
def notify_payment_status(sender, instance, created, **kwargs):
    """Уведомление о статусе платежа"""
    if not created and instance.status in ['paid', 'failed', 'refunded']:
        # Создаем уведомление
        if instance.status == 'paid':
            title = 'Платеж успешно обработан'
            message = f'Ваш платеж на сумму {instance.amount} {instance.currency} успешно обработан.'
            notification_type = 'payment'
        elif instance.status == 'failed':
            title = 'Ошибка при обработке платежа'
            message = f'Возникла ошибка при обработке вашего платежа на сумму {instance.amount} {instance.currency}.'
            notification_type = 'error'
        else:  # refunded
            title = 'Возврат средств'
            message = f'Средства в размере {instance.amount} {instance.currency} были возвращены на ваш счет.'
            notification_type = 'payment'
        
        Notification.objects.create(
            user=instance.student,
            title=title,
            message=message,
            notification_type=notification_type,
            channel='in_app'
        )

@receiver(post_save, sender=User)
def create_default_notification_settings(sender, instance, created, **kwargs):
    """Создание настроек уведомлений по умолчанию для нового пользователя"""
    if created:
        UserNotificationSettings.objects.get_or_create(user=instance)