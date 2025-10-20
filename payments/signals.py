from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import Payment, Subscription, Invoice, Refund
from accounts.models import User
from courses.models import Group, StudentProgress


# === 1️⃣ Автозачисление студента после успешной оплаты ===
@receiver(post_save, sender=Payment)
def enroll_student_after_payment(sender, instance, created, **kwargs):
    """Автоматическая запись студента на курс после успешной оплаты"""
    payment = instance

    if payment.status != 'paid':
        return  # Только при успешной оплате

    student = payment.student
    course = payment.course
    group = getattr(payment, 'group', None)

    # === Добавляем студента в группу ===
    if group:
        if student not in group.students.all():
            group.students.add(student)
            print(f"✅ Студент {student} добавлен в группу {group.title}")

    # === Создаём подписку, если нет активной ===
    if not Subscription.objects.filter(student=student, course=course, is_active=True).exists():
        sub = Subscription.objects.create(
            student=student,
            course=course,
            group=group,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=90)).date(),
            is_active=True
        )
        print(f"✅ Подписка создана для {student} на курс {course.title}")

    # === Создаём прогресс студента ===
    StudentProgress.objects.get_or_create(
        student=student,
        course=course,
        defaults={'completed_topics': [], 'test_results': {}}
    )

    # === Отправляем уведомление студенту ===
    if student.email:
        try:
            subject = 'Вы зачислены на курс!'
            message = f'''
            Здравствуйте, {student.get_full_name() or student.username}!
            
            Ваш платеж успешно обработан, и вы зачислены на курс "{course.title}".
            Период обучения: 3 месяца с момента оплаты.
            
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


# === 2️⃣ Уведомления по статусу платежа ===
@receiver(post_save, sender=Payment)
def notify_payment_status(sender, instance, created, **kwargs):
    """Уведомление о статусе платежа"""
    if not created and instance.status in ['paid', 'failed', 'refunded']:
        student = instance.student
        if student.email:
            try:
                if instance.status == 'paid':
                    subject = 'Платеж успешно обработан'
                    message = f'''
                    Здравствуйте, {student.get_full_name() or student.username}!
                    
                    Ваш платеж на сумму {instance.amount} {instance.currency} успешно обработан.
                    ID платежа: {instance.id}
                    Дата: {instance.paid_at.strftime('%d.%m.%Y %H:%M') if instance.paid_at else ''}
                    
                    Спасибо за оплату!
                    
                    С уважением,
                    Онлайн-школа
                    '''
                elif instance.status == 'failed':
                    subject = 'Ошибка при обработке платежа'
                    message = f'''
                    Здравствуйте, {student.get_full_name() or student.username}!
                    
                    Возникла ошибка при обработке вашего платежа на сумму {instance.amount} {instance.currency}.
                    Пожалуйста, попробуйте повторить оплату или свяжитесь с поддержкой.
                    
                    С уважением,
                    Онлайн-школа
                    '''
                else:  # refunded
                    subject = 'Возврат средств'
                    message = f'''
                    Здравствуйте, {student.get_full_name() or student.username}!
                    
                    Средства в размере {instance.amount} {instance.currency} были возвращены на ваш счет.
                    ID платежа: {instance.id}
                    
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


# === 3️⃣ Уведомление о создании подписки ===
@receiver(post_save, sender=Subscription)
def notify_subscription_created(sender, instance, created, **kwargs):
    """Уведомление о создании подписки"""
    if created:
        student = instance.student
        if student.email:
            try:
                subject = 'Подписка активирована'
                message = f'''
                Здравствуйте, {student.get_full_name() or student.username}!
                
                Ваша подписка на курс "{instance.course.title}" активирована.
                Период действия: с {instance.start_date} по {instance.end_date}
                
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


# === 4️⃣ Уведомление о создании счета ===
@receiver(post_save, sender=Invoice)
def notify_invoice_created(sender, instance, created, **kwargs):
    """Уведомление о создании счета"""
    if created and instance.student.email:
        student = instance.student
        try:
            subject = f'Счет #{instance.invoice_number}'
            message = f'''
            Здравствуйте, {student.get_full_name() or student.username}!
            
            Для вас создан счет #{instance.invoice_number} на сумму {instance.amount} {instance.currency}.
            Срок оплаты: {instance.due_date}
            Описание: {instance.description or 'Оплата обучения'}
            
            Пожалуйста, оплатите счет в установленный срок.
            
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


# === 5️⃣ Уведомление администраторам о возврате ===
@receiver(post_save, sender=Refund)
def notify_refund_request(sender, instance, created, **kwargs):
    """Уведомление о запросе возврата"""
    if created:
        admins = User.objects.filter(role='admin')
        for admin in admins:
            if admin.email:
                try:
                    subject = f'Новый запрос на возврат #{instance.id}'
                    message = f'''
                    Уважаемый администратор!
                    
                    Поступил новый запрос на возврат:
                    Студент: {instance.payment.student.get_full_name()}
                    Сумма: {instance.amount} {instance.payment.currency}
                    Причина: {instance.reason}
                    
                    Пожалуйста, рассмотрите запрос в ближайшее время.
                    
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
