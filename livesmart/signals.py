# livesmart/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import LiveSmartRoom, LiveSmartParticipant, LiveSmartRecording, LiveSmartSettings
from accounts.models import User
from courses.models import Lesson, Group
from payments.models import Payment
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Lesson)
def create_livesmart_room_for_lesson(sender, instance, created, **kwargs):
    """Создание комнаты LiveSmart при создании занятия"""
    if created:
        try:
            from .services import LiveSmartService
            
            # Создаем комнату через сервис
            result = LiveSmartService().create_room(instance)
            
            if result['success']:
                logger.info(f"Создана комната LiveSmart для занятия: {instance.title}")
            else:
                logger.error(f"Ошибка создания комнаты LiveSmart: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Ошибка создания комнаты LiveSmart для занятия {instance.id}: {str(e)}")

@receiver(post_save, sender=LiveSmartRoom)
def notify_room_created(sender, instance, created, **kwargs):
    """Уведомление о создании комнаты LiveSmart"""
    if created:
        try:
            lesson = instance.lesson
            recipients = []
            
            # Определяем получателей
            if lesson.lesson_type == 'group' and lesson.group:
                recipients = list(lesson.group.students.all())
            elif lesson.lesson_type == 'individual' and lesson.student:
                recipients = [lesson.student]
            
            # Добавляем преподавателя
            if lesson.teacher not in recipients:
                recipients.append(lesson.teacher)
            
            # Отправляем уведомления
            for recipient in recipients:
                if recipient.email:
                    try:
                        subject = f'Новое занятие: {lesson.title}'
                        message = f'''
                        Здравствуйте, {recipient.get_full_name() or recipient.username}!
                        
                        Запланировано новое занятие:
                        Тема: {lesson.title}
                        Тип: {lesson.get_lesson_type_display()}
                        Дата и время: {lesson.start_time.strftime('%d.%m.%Y %H:%M')}
                        Преподаватель: {lesson.teacher.get_full_name()}
                        Ссылка на LiveSmart: {instance.join_url or 'Не указана'}
                        Пароль встречи: {instance.room_password or 'Не требуется'}
                        
                        С уважением,
                        Онлайн-школа
                        '''
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [recipient.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        logger.error(f"Ошибка отправки email: {e}")
            
            logger.info(f"Отправлены уведомления о создании комнаты: {instance.room_name}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомлений о комнате {instance.id}: {str(e)}")

@receiver(post_save, sender=LiveSmartParticipant)
def notify_participant_joined(sender, instance, created, **kwargs):
    """Уведомление о присоединении участника к комнате"""
    if created and instance.is_present:
        try:
            user = instance.user
            lesson = instance.room.lesson
            
            # Отправляем уведомление преподавателю
            if lesson.teacher.email:
                try:
                    subject = f'Участник присоединился к занятию: {lesson.title}'
                    message = f'''
                    Здравствуйте, {lesson.teacher.get_full_name() or lesson.teacher.username}!
                    
                    {user.get_full_name() or user.username} присоединился к занятию "{lesson.title}".
                    Время присоединения: {instance.joined_at.strftime('%d.%m.%Y %H:%M')}
                    
                    С уважением,
                    Онлайн-школа
                    '''
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [lesson.teacher.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки email преподавателю: {e}")
            
            logger.info(f"Участник {user.username} присоединился к комнате {instance.room.room_name}")
            
        except Exception as e:
            logger.error(f"Ошибка уведомления о присоединении участника: {str(e)}")

@receiver(post_save, sender=LiveSmartRecording)
def notify_recording_created(sender, instance, created, **kwargs):
    """Уведомление о создании записи"""
    if created and instance.is_public:
        try:
            room = instance.room
            lesson = room.lesson
            recipients = []
            
            # Определяем получателей
            if lesson.lesson_type == 'group' and lesson.group:
                recipients = list(lesson.group.students.all())
            elif lesson.lesson_type == 'individual' and lesson.student:
                recipients = [lesson.student]
            
            # Добавляем преподавателя
            if lesson.teacher not in recipients:
                recipients.append(lesson.teacher)
            
            # Отправляем уведомления
            for recipient in recipients:
                if recipient.email:
                    try:
                        subject = f'Доступна запись занятия: {lesson.title}'
                        message = f'''
                        Здравствуйте, {recipient.get_full_name() or recipient.username}!
                        
                        Доступна запись занятия "{lesson.title}":
                        Название: {instance.title}
                        Длительность: {instance.duration}
                        Дата создания: {instance.created_at.strftime('%d.%m.%Y %H:%M')}
                        Ссылка на запись: {instance.file_url or 'Не указана'}
                        
                        С уважением,
                        Онлайн-школа
                        '''
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [recipient.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        logger.error(f"Ошибка отправки email: {e}")
            
            logger.info(f"Отправлены уведомления о записи: {instance.title}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомлений о записи {instance.id}: {str(e)}")

@receiver(post_save, sender=User)
def create_default_livesmart_settings(sender, instance, created, **kwargs):
    """Создание настроек LiveSmart по умолчанию для новых пользователей"""
    if created:
        try:
            LiveSmartSettings.objects.get_or_create(
                user=instance,
                defaults={
                    'is_recording_enabled': False,
                    'max_participants': 50,
                    'default_room_settings': {
                        'enable_chat': True,
                        'enable_screen_sharing': True,
                        'enable_whiteboard': True,
                        'enable_polls': True
                    }
                }
            )
            logger.info(f"Созданы настройки LiveSmart для пользователя: {instance.username}")
        except Exception as e:
            logger.error(f"Ошибка создания настроек LiveSmart для пользователя {instance.id}: {str(e)}")

@receiver(post_delete, sender=LiveSmartRoom)
def cleanup_livesmart_room(sender, instance, **kwargs):
    """Очистка данных при удалении комнаты LiveSmart"""
    try:
        # Удаляем участников
        instance.participants.all().delete()
        
        # Удаляем записи
        instance.recordings.all().delete()
        
        logger.info(f"Очищены данные комнаты LiveSmart: {instance.room_name}")
    except Exception as e:
        logger.error(f"Ошибка очистки данных комнаты LiveSmart {instance.id}: {str(e)}")

@receiver(post_delete, sender=LiveSmartRecording)
def cleanup_livesmart_recording_files(sender, instance, **kwargs):
    """Очистка файлов при удалении записи LiveSmart"""
    try:
        # Удаляем файл записи
        if instance.file:
            instance.file.delete(save=False)
        
        # Удаляем файл записи (если есть)
        if instance.recording_file:
            instance.recording_file.delete(save=False)
        
        logger.info(f"Очищены файлы записи LiveSmart: {instance.title}")
    except Exception as e:
        logger.error(f"Ошибка очистки файлов записи LiveSmart {instance.id}: {str(e)}")