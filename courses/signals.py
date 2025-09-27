from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Lesson, Group, Attendance, VideoLesson, MeetingParticipant, HomeworkSubmission, SupportTicket
from accounts.models import User

@receiver(post_save, sender=Lesson)
def notify_lesson_created(sender, instance, created, **kwargs):
    """Уведомление о создании занятия"""
    if created and instance.start_time:
        # Отправляем уведомления студентам
        recipients = []
        
        if instance.lesson_type == 'group' and instance.group:
            # Групповое занятие
            recipients = list(instance.group.students.all())
        elif instance.lesson_type == 'individual' and instance.student:
            # Индивидуальное занятие
            recipients = [instance.student]
        
        # Добавляем преподавателя
        if instance.teacher not in recipients:
            recipients.append(instance.teacher)
        
        # Отправляем уведомления
        for recipient in recipients:
            if recipient.email:
                try:
                    subject = f'Новое занятие: {instance.title}'
                    message = f'''
                    Здравствуйте, {recipient.get_full_name() or recipient.username}!
                    
                    Запланировано новое занятие:
                    Тема: {instance.title}
                    Тип: {instance.get_lesson_type_display()}
                    Дата и время: {instance.start_time.strftime('%d.%m.%Y %H:%M')}
                    Преподаватель: {instance.teacher.get_full_name()}
                    Ссылка на Zoom: {instance.zoom_link or 'Не указана'}
                    
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
                    print(f"Ошибка отправки email: {e}")

@receiver(m2m_changed, sender=Group.students.through)
def notify_student_added_to_group(sender, instance, action, pk_set, **kwargs):
    """Уведомление о добавлении студента в группу"""
    if action == 'post_add':
        group = instance
        students = User.objects.filter(pk__in=pk_set)
        
        for student in students:
            if student.email:
                try:
                    subject = f'Вы добавлены в группу: {group.title}'
                    message = f'''
                    Здравствуйте, {student.get_full_name() or student.username}!
                    
                    Вы были добавлены в группу "{group.title}" курса "{group.course.title}".
                    Преподаватель: {group.teacher.get_full_name()}
                    Период обучения: с {group.start_date} по {group.end_date}
                    
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

@receiver(post_save, sender=Attendance)
def notify_attendance_marked(sender, instance, created, **kwargs):
    """Уведомление о выставленной посещаемости"""
    if created or kwargs.get('update_fields'):
        student = instance.student
        lesson = instance.lesson
        
        if student.email:
            try:
                status_text = instance.get_status_display()
                subject = f'Отметка посещаемости: {lesson.title}'
                message = f'''
                Здравствуйте, {student.get_full_name() or student.username}!
                
                По вашему занятию "{lesson.title}" выставлена отметка:
                Статус: {status_text}
                Комментарий: {instance.comment or 'Нет комментария'}
                
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

@receiver(post_save, sender=VideoLesson)
def create_zoom_meeting_for_lesson(sender, instance, created, **kwargs):
    """Создание Zoom встречи при создании видеоурока"""
    if created:
        # В реальности - создание Zoom встречи через API
        # Здесь просто уведомляем преподавателя
        teacher = instance.lesson.teacher
        if teacher.email:
            try:
                subject = f'Видеоурок создан: {instance.lesson.title}'
                message = f'''
                Здравствуйте, {teacher.get_full_name() or teacher.username}!
                
                Для занятия "{instance.lesson.title}" создана Zoom встреча:
                ID встречи: {instance.zoom_meeting_id}
                Ссылка для присоединения: {instance.zoom_join_url}
                Пароль: {instance.meeting_password}
                
                С уважением,
                Онлайн-школа
                '''
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [teacher.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Ошибка отправки email: {e}")

@receiver(post_save, sender=MeetingParticipant)
def notify_meeting_participation(sender, instance, created, **kwargs):
    """Уведомление об участии в встрече"""
    if created:
        user = instance.user
        lesson = instance.lesson
        
        if user.email:
            try:
                subject = f'Участие в занятии: {lesson.title}'
                message = f'''
                Здравствуйте, {user.get_full_name() or user.username}!
                
                Вы были добавлены в список участников занятия "{lesson.title}".
                Роль: {instance.get_role_display()}
                Время присоединения: {instance.joined_at.strftime('%d.%m.%Y %H:%M')}
                
                С уважением,
                Онлайн-школа
                '''
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Ошибка отправки email: {e}")

@receiver(post_save, sender=HomeworkSubmission)
def notify_homework_graded(sender, instance, created, **kwargs):
    """Уведомление об оценке домашнего задания"""
    if not created and instance.grade is not None:
        student = instance.student
        homework = instance.homework
        
        if student.email:
            try:
                subject = f'Оценка за задание: {homework.title}'
                message = f'''
                Здравствуйте, {student.get_full_name() or student.username}!
                
                За ваше задание "{homework.title}" выставлена оценка: {instance.grade}
                Комментарий преподавателя: {instance.feedback or 'Нет комментария'}
                
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

@receiver(post_save, sender=SupportTicket)
def notify_support_ticket_created(sender, instance, created, **kwargs):
    """Уведомление о создании тикета поддержки"""
    if created:
        user = instance.user
        
        if user.email:
            try:
                subject = f'Тикет поддержки создан: {instance.title}'
                message = f'''
                Здравствуйте, {user.get_full_name() or user.username}!
                
                Создан тикет поддержки:
                Тема: {instance.title}
                Статус: {instance.get_status_display()}
                Приоритет: {instance.get_priority_display()}
                
                С уважением,
                Служба поддержки
                '''
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Ошибка отправки email: {e}")