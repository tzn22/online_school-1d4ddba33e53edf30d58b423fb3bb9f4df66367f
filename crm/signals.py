from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import StudentProfile, TeacherProfile, Lead, StudentActivity
from accounts.models import User
from courses.models import Lesson, Attendance
from payments.models import Payment
from feedback.models import Feedback

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создание профиля при создании пользователя"""
    if created:
        if instance.role == 'student':
            StudentProfile.objects.get_or_create(student=instance)
        elif instance.role == 'teacher':
            TeacherProfile.objects.get_or_create(teacher=instance)

@receiver(post_save, sender=Lead)
def notify_lead_assignment(sender, instance, created, **kwargs):
    """Уведомление о назначении лида менеджеру"""
    if not created and instance.assigned_to and instance.assigned_to.email:
        try:
            subject = f'Новый лид назначен вам: {instance.first_name} {instance.last_name}'
            message = f'''
            Здравствуйте, {instance.assigned_to.get_full_name() or instance.assigned_to.username}!
            
            Вам назначен новый лид:
            Имя: {instance.first_name} {instance.last_name}
            Email: {instance.email}
            Телефон: {instance.phone or 'Не указан'}
            Интересующий курс: {instance.interested_course.title if instance.interested_course else 'Не указан'}
            Статус: {instance.get_status_display()}
            Источник: {instance.get_source_display()}
            
            Пожалуйста, свяжитесь с клиентом в ближайшее время.
            
            С уважением,
            CRM система
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.assigned_to.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Ошибка отправки email: {e}")

@receiver(post_save, sender=Lesson)
def track_lesson_scheduled(sender, instance, created, **kwargs):
    """Отслеживание запланированных занятий"""
    if created:
        # Отслеживаем для преподавателя
        from .services import CRMService
        CRMService.track_student_activity(
            student=instance.teacher,
            activity_type='lesson_scheduled',
            description=f'Запланировано занятие "{instance.title}"',
            related_object_id=instance.id
        )

@receiver(post_save, sender=Attendance)
def track_attendance(sender, instance, created, **kwargs):
    """Отслеживание посещаемости"""
    if created:
        from .services import CRMService
        if instance.status == 'present':
            activity_type = 'lesson_attended'
            description = f'Студент посетил занятие "{instance.lesson.title}"'
        else:
            activity_type = 'lesson_missed'
            description = f'Студент пропустил занятие "{instance.lesson.title}"'
        
        CRMService.track_student_activity(
            student=instance.student,
            activity_type=activity_type,
            description=description,
            related_object_id=instance.lesson.id
        )

@receiver(post_save, sender=Payment)
def track_payment(sender, instance, created, **kwargs):
    """Отслеживание платежей"""
    if not created and instance.status == 'paid':
        from .services import CRMService
        CRMService.track_student_activity(
            student=instance.student,
            activity_type='payment_made',
            description=f'Совершен платеж на сумму {instance.amount} {instance.currency}',
            related_object_id=instance.id
        )

@receiver(post_save, sender=Feedback)
def track_feedback(sender, instance, created, **kwargs):
    """Отслеживание отзывов"""
    if created:
        from .services import CRMService
        CRMService.track_student_activity(
            student=instance.student,
            activity_type='feedback_given',
            description=f'Оставлен отзыв: "{instance.title}"',
            related_object_id=instance.id
        )