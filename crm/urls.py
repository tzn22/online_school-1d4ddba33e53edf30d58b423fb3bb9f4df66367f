from django.urls import path
from .views import (
    StudentProfileListCreateView,
    StudentProfileDetailView,
    TeacherProfileListCreateView,
    TeacherProfileDetailView,
    LeadListCreateView,
    LeadDetailView,
    StudentActivityListView,
    AnalyticsReportListView,
    AnalyticsReportDetailView,
    convert_lead,
    student_performance,
    teacher_performance,
    financial_report,
    lead_report,
    generate_analytics_report,
    dashboard_statistics
)

urlpatterns = [
    # Профили студентов
    path('student-profiles/', StudentProfileListCreateView.as_view(), name='student-profile-list'),
    path('student-profiles/<int:pk>/', StudentProfileDetailView.as_view(), name='student-profile-detail'),
    
    # Профили преподавателей
    path('teacher-profiles/', TeacherProfileListCreateView.as_view(), name='teacher-profile-list'),
    path('teacher-profiles/<int:pk>/', TeacherProfileDetailView.as_view(), name='teacher-profile-detail'),
    
    # Лиды
    path('leads/', LeadListCreateView.as_view(), name='lead-list'),
    path('leads/<int:pk>/', LeadDetailView.as_view(), name='lead-detail'),
    path('leads/<int:lead_id>/convert/', convert_lead, name='convert-lead'),
    
    # Активность студентов
    path('student-activities/', StudentActivityListView.as_view(), name='student-activity-list'),
    
    # Аналитические отчеты
    path('reports/', AnalyticsReportListView.as_view(), name='analytics-report-list'),
    path('reports/<int:pk>/', AnalyticsReportDetailView.as_view(), name='analytics-report-detail'),
    path('reports/generate/', generate_analytics_report, name='generate-analytics-report'),
    
    # Специализированные отчеты
    path('reports/student-performance/<int:student_id>/', student_performance, name='student-performance'),
    path('reports/teacher-performance/<int:teacher_id>/', teacher_performance, name='teacher-performance'),
    path('reports/financial/', financial_report, name='financial-report'),
    path('reports/leads/', lead_report, name='lead-report'),
    
    # Дашборд
    path('dashboard/statistics/', dashboard_statistics, name='dashboard-statistics'),
]