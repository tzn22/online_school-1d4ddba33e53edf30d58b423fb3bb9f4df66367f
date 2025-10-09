from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta
from .models import StudentProfile, TeacherProfile, Lead, StudentActivity, AnalyticsReport
from accounts.models import User
from courses.models import Course, Group, Lesson
from payments.models import Payment
from .serializers import (
    StudentProfileSerializer, 
    TeacherProfileSerializer,
    LeadSerializer,
    StudentActivitySerializer,
    AnalyticsReportSerializer,
    StudentPerformanceSerializer,
    TeacherPerformanceSerializer,
    FinancialReportSerializer,
    LeadReportSerializer
)
from .services import CRMService
from .permissions import IsAdminOrManager

class StudentProfileListCreateView(generics.ListCreateAPIView):
    """Список профилей студентов и создание нового профиля"""
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['education_level', 'target_language', 'language_level']
    search_fields = ['student__username', 'student__email', 'student__first_name', 'student__last_name']
    ordering_fields = ['created_at', 'updated_at']

class StudentProfileDetailView(generics.RetrieveUpdateAPIView):
    """Детали профиля студента"""
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

class TeacherProfileListCreateView(generics.ListCreateAPIView):
    """Список профилей преподавателей и создание нового профиля"""
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['degree', 'years_of_experience']
    search_fields = ['teacher__username', 'teacher__email', 'teacher__first_name', 'teacher__last_name']
    ordering_fields = ['created_at', 'updated_at']

class TeacherProfileDetailView(generics.RetrieveUpdateAPIView):
    """Детали профиля преподавателя"""
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

class LeadListCreateView(generics.ListCreateAPIView):
    """Список лидов и создание нового лида"""
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'source', 'assigned_to', 'interested_course']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

class LeadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали лида"""
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

class StudentActivityListView(generics.ListAPIView):
    """Список активностей студентов"""
    queryset = StudentActivity.objects.all()
    serializer_class = StudentActivitySerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'activity_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

class AnalyticsReportListView(generics.ListAPIView):
    """Список аналитических отчетов"""
    queryset = AnalyticsReport.objects.filter(is_published=True)
    serializer_class = AnalyticsReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['report_type']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']

class AnalyticsReportDetailView(generics.RetrieveAPIView):
    """Детали аналитического отчета"""
    queryset = AnalyticsReport.objects.all()
    serializer_class = AnalyticsReportSerializer
    permission_classes = [IsAuthenticated]

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrManager])
def convert_lead(request, lead_id):  # Это работает, если lead_id передается через URL
    """Конвертация лида в студента"""
    try:
        lead = Lead.objects.get(id=lead_id)
        if lead.status == 'converted':
            return Response({
                'error': 'Лид уже конвертирован'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        student = CRMService.convert_lead_to_student(lead)
        
        return Response({
            'message': 'Лид успешно конвертирован в студента',
            'student_id': student.id,
            'username': student.username
        })
    except Lead.DoesNotExist:
        return Response({
            'error': 'Лид не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrManager])
def student_performance(request, student_id):
    """Получение успеваемости студента"""
    try:
        student = User.objects.get(id=student_id, role='student')
        
        # Получаем параметры периода
        period_start = request.query_params.get('start_date')
        period_end = request.query_params.get('end_date')
        
        if period_start:
            period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
        if period_end:
            period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
        
        performance_data = CRMService.get_student_performance(
            student, period_start, period_end
        )
        
        serializer = StudentPerformanceSerializer(performance_data)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({
            'error': 'Студент не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrManager])
def teacher_performance(request, teacher_id):
    """Получение эффективности преподавателя"""
    try:
        teacher = User.objects.get(id=teacher_id, role='teacher')
        
        # Получаем параметры периода
        period_start = request.query_params.get('start_date')
        period_end = request.query_params.get('end_date')
        
        if period_start:
            period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
        if period_end:
            period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
        
        performance_data = CRMService.get_teacher_performance(
            teacher, period_start, period_end
        )
        
        serializer = TeacherPerformanceSerializer(performance_data)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({
            'error': 'Преподаватель не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def financial_report(request):
    """Генерация финансового отчета"""
    try:
        # Получаем параметры периода
        period_start = request.query_params.get('start_date')
        period_end = request.query_params.get('end_date')
        
        if not period_start or not period_end:
            return Response({
                'error': 'Необходимо указать start_date и end_date'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
        period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
        
        report_data = CRMService.generate_financial_report(period_start, period_end)
        
        serializer = FinancialReportSerializer(report_data)
        return Response(serializer.data)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def lead_report(request):
    """Генерация отчета по лидам"""
    try:
        # Получаем параметры периода
        period_start = request.query_params.get('start_date')
        period_end = request.query_params.get('end_date')
        
        if period_start:
            period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
        if period_end:
            period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
        
        report_data = CRMService.generate_lead_report(period_start, period_end)
        
        serializer = LeadReportSerializer(report_data)
        return Response(serializer.data)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def generate_analytics_report(request):
    """Генерация аналитического отчета"""
    try:
        report_type = request.data.get('report_type')
        title = request.data.get('title')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        if not all([report_type, title, period_start, period_end]):
            return Response({
                'error': 'Необходимо указать report_type, title, period_start и period_end'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
        period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
        
        # Генерируем данные в зависимости от типа отчета
        if report_type == 'student_performance':
            data = CRMService.generate_student_performance_report(period_start, period_end)
        elif report_type == 'teacher_performance':
            data = CRMService.generate_teacher_performance_report(period_start, period_end)
        elif report_type == 'financial':
            data = CRMService.generate_financial_report(period_start, period_end)
        elif report_type == 'marketing':
            data = CRMService.generate_lead_report(period_start, period_end)
        else:
            return Response({
                'error': 'Неподдерживаемый тип отчета'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем отчет
        report = AnalyticsReport.objects.create(
            title=title,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            data=data,
            generated_by=request.user
        )
        
        serializer = AnalyticsReportSerializer(report)
        return Response({
            'message': 'Отчет успешно сгенерирован',
            'report': serializer.data
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def dashboard_statistics(request):
    """Получение статистики для дашборда"""
    try:
        # Общая статистика
        total_students = User.objects.filter(role='student').count()
        total_teachers = User.objects.filter(role='teacher').count()
        total_courses = Course.objects.count()
        total_groups = Group.objects.count()
        
        # Финансовая статистика
        total_revenue = Payment.objects.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Активность за последние 30 дней
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_activities = StudentActivity.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('activity_type').annotate(
            count=Count('id')
        )
        
        # Лиды
        total_leads = Lead.objects.count()
        new_leads = Lead.objects.filter(status='new').count()
        
        stats = {
            'users': {
                'total_students': total_students,
                'total_teachers': total_teachers,
                'total_courses': total_courses,
                'total_groups': total_groups
            },
            'finance': {
                'total_revenue': float(total_revenue),
                'currency': 'RUB'
            },
            'activity': {
                'recent_activities': list(recent_activities),
                'period_days': 30
            },
            'leads': {
                'total_leads': total_leads,
                'new_leads': new_leads
            }
        }
        
        return Response(stats)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)