from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import AdminActionLog
from accounts.models import User
from courses.models import Course, Group, Lesson
from payments.models import Payment

User = get_user_model()

def log_admin_action(admin_user, action_type, model_name, object_id=None, description=""):
    """Логирование действия администратора"""
    try:
        AdminActionLog.objects.create(
            admin_user=admin_user,
            action_type=action_type,
            model_name=model_name,
            object_id=object_id,
            description=description
        )
    except Exception as e:
        print(f"Ошибка логирования действия администратора: {e}")

# === СИГНАЛЫ ДЛЯ ЛОГИРОВАНИЯ ДЕЙСТВИЙ ===

@receiver(post_save, sender=User)
def log_user_save(sender, instance, created, **kwargs):
    """Логирование создания/обновления пользователя"""
    # Здесь можно добавить логику для определения, кто выполнил действие
    pass

@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    """Логирование удаления пользователя"""
    pass

@receiver(post_save, sender=Course)
def log_course_save(sender, instance, created, **kwargs):
    """Логирование создания/обновления курса"""
    pass

@receiver(post_delete, sender=Course)
def log_course_delete(sender, instance, **kwargs):
    """Логирование удаления курса"""
    pass

@receiver(post_save, sender=Group)
def log_group_save(sender, instance, created, **kwargs):
    """Логирование создания/обновления группы"""
    pass

@receiver(post_delete, sender=Group)
def log_group_delete(sender, instance, **kwargs):
    """Логирование удаления группы"""
    pass

@receiver(post_save, sender=Lesson)
def log_lesson_save(sender, instance, created, **kwargs):
    """Логирование создания/обновления занятия"""
    pass

@receiver(post_delete, sender=Lesson)
def log_lesson_delete(sender, instance, **kwargs):
    """Логирование удаления занятия"""
    pass

@receiver(post_save, sender=Payment)
def log_payment_save(sender, instance, created, **kwargs):
    """Логирование создания/обновления платежа"""
    pass

@receiver(post_delete, sender=Payment)
def log_payment_delete(sender, instance, **kwargs):
    """Логирование удаления платежа"""
    pass