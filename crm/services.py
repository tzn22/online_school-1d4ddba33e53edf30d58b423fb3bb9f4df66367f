from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from django.db import models
from datetime import datetime, timedelta
from .models import StudentProfile, TeacherProfile, Lead, StudentActivity, AnalyticsReport
from accounts.models import User
from courses.models import Course, Group, Lesson, Attendance
from payments.models import Payment, Subscription
from feedback.models import Feedback

class CRMService:
    """Сервис для работы с CRM функциями"""
    
    @staticmethod
    def create_student_profile(student):
        """Создание профиля студента"""
        profile, created = StudentProfile.objects.get_or_create(
            student=student
        )
        return profile
    
    @staticmethod
    def create_teacher_profile(teacher):
        """Создание профиля преподавателя"""
        profile, created = TeacherProfile.objects.get_or_create(
            teacher=teacher
        )
        return profile
    
    @staticmethod
    def track_student_activity(student, activity_type, description='', 
                             related_object_id=None, ip_address=None, user_agent=None):
        """Отслеживание активности студента"""
        activity = StudentActivity.objects.create(
            student=student,
            activity_type=activity_type,
            description=description,
            related_object_id=related_object_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return activity
    
    @staticmethod
    def convert_lead_to_student(lead):
        """Конвертация лида в студента"""
        # Создаем пользователя-студента
        username = f"{lead.first_name.lower()}_{lead.last_name.lower()}_{lead.id}"
        # Проверяем уникальность username
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}_{counter}"
            counter += 1
        
        student = User.objects.create_user(
            username=username,
            email=lead.email,
            first_name=lead.first_name,
            last_name=lead.last_name,
            role='student'
        )
        
        # Создаем профиль студента
        StudentProfile.objects.create(
            student=student,
            parent_email=lead.email,
            parent_phone=lead.phone
        )
        
        # Обновляем статус лида
        lead.status = 'converted'
        lead.converted_at = timezone.now()
        lead.save()
        
        return student
    
    @staticmethod
    def get_student_performance(student, period_start=None, period_end=None):
        """Получение успеваемости студента"""
        if not period_start:
            period_start = timezone.now() - timedelta(days=365)
        if not period_end:
            period_end = timezone.now()
        
        # Общее количество занятий
        total_lessons = Lesson.objects.filter(
            Q(group__students=student) | Q(student=student),
            start_time__range=[period_start, period_end]
        ).count()
        
        # Посещенные занятия
        attended_lessons = Attendance.objects.filter(
            student=student,
            status='present',
            lesson__start_time__range=[period_start, period_end]
        ).count()
        
        # Процент посещаемости
        attendance_rate = (attended_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        # Средняя оценка
        avg_rating = Feedback.objects.filter(
            student=student,
            rating__isnull=False
        ).aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Завершенные курсы
        completed_courses = Subscription.objects.filter(
            student=student,
            is_active=True
        ).count()
        
        # Общие платежи
        total_payments = Payment.objects.filter(
            student=student,
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'student_id': student.id,
            'student_name': student.get_full_name(),
            'total_lessons': total_lessons,
            'attended_lessons': attended_lessons,
            'attendance_rate': round(attendance_rate, 2),
            'average_rating': round(float(avg_rating), 2),
            'completed_courses': completed_courses,
            'total_payments': float(total_payments)
        }
    
    @staticmethod
    def get_teacher_performance(teacher, period_start=None, period_end=None):
        """Получение эффективности преподавателя"""
        if not period_start:
            period_start = timezone.now() - timedelta(days=365)
        if not period_end:
            period_end = timezone.now()
        
        # Группы преподавателя
        groups = Group.objects.filter(teacher=teacher)
        total_groups = groups.count()
        
        # Общее количество студентов
        total_students = groups.aggregate(
            total=Count('students')
        )['total'] or 0
        
        # Средняя оценка преподавателя
        avg_rating = Feedback.objects.filter(
            teacher=teacher,
            rating__isnull=False
        ).aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Проведенные занятия
        lessons_conducted = Lesson.objects.filter(
            teacher=teacher,
            start_time__range=[period_start, period_end]
        ).count()
        
        # Общий доход
        total_earnings = Payment.objects.filter(
            course__groups__teacher=teacher,
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'teacher_id': teacher.id,
            'teacher_name': teacher.get_full_name(),
            'total_groups': total_groups,
            'total_students': total_students,
            'average_rating': round(float(avg_rating), 2),
            'lessons_conducted': lessons_conducted,
            'total_earnings': float(total_earnings)
        }
    
    @staticmethod
    def generate_financial_report(period_start, period_end):
        """Генерация финансового отчета"""
        # Общий доход
        total_revenue = Payment.objects.filter(
            status='paid',
            paid_at__range=[period_start, period_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Количество платежей
        total_payments = Payment.objects.filter(
            status='paid',
            paid_at__range=[period_start, period_end]
        ).count()
        
        # Средний платеж
        average_payment = (float(total_revenue) / total_payments) if total_payments > 0 else 0
        
        # Доход по курсам
        revenue_by_course = Payment.objects.filter(
            status='paid',
            paid_at__range=[period_start, period_end]
        ).values('course__title').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Доход по месяцам
        revenue_by_month = Payment.objects.filter(
            status='paid',
            paid_at__range=[period_start, period_end]
        ).extra(
            select={'month': "DATE_TRUNC('month', paid_at)"}
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        return {
            'period_start': period_start,
            'period_end': period_end,
            'total_revenue': float(total_revenue),
            'total_payments': total_payments,
            'average_payment': round(average_payment, 2),
            'revenue_by_course': list(revenue_by_course),
            'revenue_by_month': list(revenue_by_month)
        }
    
    @staticmethod
    def generate_lead_report(period_start=None, period_end=None):
        """Генерация отчета по лидам"""
        if not period_start:
            period_start = timezone.now() - timedelta(days=365)
        if not period_end:
            period_end = timezone.now()
        
        # Общее количество лидов
        total_leads = Lead.objects.filter(
            created_at__range=[period_start, period_end]
        ).count()
        
        # Лиды по статусам
        leads_by_status = Lead.objects.filter(
            created_at__range=[period_start, period_end]
        ).values('status').annotate(
            count=Count('id')
        )
        
        # Лиды по источникам
        leads_by_source = Lead.objects.filter(
            created_at__range=[period_start, period_end]
        ).values('source').annotate(
            count=Count('id')
        )
        
        # Коэффициент конверсии
        converted_leads = Lead.objects.filter(
            status='converted',
            converted_at__range=[period_start, period_end]
        ).count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Среднее время конверсии
        converted_leads_with_time = Lead.objects.filter(
            status='converted',
            converted_at__range=[period_start, period_end],
            converted_at__isnull=False
        ).annotate(
            conversion_time=models.F('converted_at') - models.F('created_at')
        )
        
        avg_conversion_time = converted_leads_with_time.aggregate(
            avg=Avg('conversion_time')
        )['avg']
        
        average_conversion_days = avg_conversion_time.days if avg_conversion_time else 0
        
        return {
            'total_leads': total_leads,
            'leads_by_status': {item['status']: item['count'] for item in leads_by_status},
            'leads_by_source': {item['source']: item['count'] for item in leads_by_source},
            'conversion_rate': round(conversion_rate, 2),
            'average_conversion_time': average_conversion_days
        }