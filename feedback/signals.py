from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Feedback, FeedbackResponse, Survey, SurveyResponse

@receiver(post_save, sender=Feedback)
def notify_feedback_created(sender, instance, created, **kwargs):
    """Уведомление о создании отзыва"""
    if created:
        # Уведомляем преподавателя, если отзыв о нем
        if instance.teacher and instance.teacher.email:
            try:
                subject = f'Новый отзыв о вас: {instance.title}'
                message = f'''
                Здравствуйте, {instance.teacher.get_full_name() or instance.teacher.username}!
                
                Студент {instance.student.get_full_name() or instance.student.username} оставил отзыв о вас:
                Тема: {instance.title}
                Содержание: {instance.content}
                Оценка: {instance.rating if instance.rating else 'Не указана'}
                
                Пожалуйста, ознакомьтесь с отзывом в личном кабинете.
                
                С уважением,
                Онлайн-школа
                '''
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.teacher.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Ошибка отправки email: {e}")

@receiver(post_save, sender=FeedbackResponse)
def notify_feedback_response(sender, instance, created, **kwargs):
    """Уведомление об ответе на отзыв"""
    if created and not instance.is_internal:
        feedback = instance.feedback
        student = feedback.student
        
        if student.email:
            try:
                subject = f'Ответ на ваш отзыв: {feedback.title}'
                message = f'''
                Здравствуйте, {student.get_full_name() or student.username}!
                
                {instance.responder.get_full_name() or instance.responder.username} ответил на ваш отзыв:
                Тема: {feedback.title}
                Ответ: {instance.content}
                
                С уважением,
                Онлайн-школа
                '''
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [student.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Ошибка отправки email: {e}")

@receiver(post_save, sender=Survey)
def notify_survey_available(sender, instance, created, **kwargs):
    """Уведомление о доступности опроса"""
    if created and instance.status == 'active':
        # Здесь можно отправить уведомления пользователям
        pass

@receiver(post_save, sender=SurveyResponse)
def notify_survey_response(sender, instance, created, **kwargs):
    """Уведомление об ответе на опрос (для админов)"""
    if created:
        # Уведомляем администраторов
        from accounts.models import User
        admins = User.objects.filter(role='admin')
        
        for admin in admins:
            if admin.email:
                try:
                    subject = f'Новый ответ на опрос: {instance.survey.title}'
                    message = f'''
                    Уважаемый администратор!
                    
                    Получен новый ответ на опрос "{instance.survey.title}".
                    Респондент: {instance.respondent.get_full_name() if instance.respondent else 'Аноним'}
                    Дата: {instance.submitted_at.strftime('%d.%m.%Y %H:%M')}
                    
                    С уважением,
                    Система уведомлений
                    '''
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [admin.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Ошибка отправки email: {e}")