from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth import get_user_model
from .models import AdminActionLog, ReportTemplate, GeneratedReport, MassEmailCampaign, SystemSetting
from accounts.models import User
from courses.models import Course, Group, Lesson, Attendance
from payments.models import Payment, Invoice
import json

User = get_user_model()

# === РАСШИРЕННЫЕ АДМИН ВОЗМОЖНОСТИ ===

@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    """Лог действий администраторов"""
    list_display = ['admin_user', 'action_type', 'model_name', 'object_id', 'created_at']
    list_filter = ['action_type', 'model_name', 'created_at', 'admin_user']
    search_fields = ['admin_user__username', 'description', 'model_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Запрещаем добавление вручную
    
    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем изменение

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Шаблоны отчетов"""
    list_display = ['name', 'report_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['report_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    """Сгенерированные отчеты"""
    list_display = ['title', 'report_template', 'period', 'generated_by', 'generated_at', 'is_published', 'download_link']
    list_filter = ['report_template__report_type', 'is_published', 'generated_at']
    search_fields = ['title', 'report_template__name']
    readonly_fields = ['generated_at', 'file_size']
    
    def period(self, obj):
        return f"{obj.period_start} - {obj.period_end}"
    period.short_description = 'Период'
    
    def download_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Скачать</a>', obj.file.url)
        return '-'
    download_link.short_description = 'Файл'

@admin.register(MassEmailCampaign)
class MassEmailCampaignAdmin(admin.ModelAdmin):
    """Массовая email рассылка"""
    list_display = ['name', 'subject', 'status', 'target_audience', 'total_recipients', 'sent_count', 'success_rate', 'created_at']
    list_filter = ['status', 'target_audience', 'created_at']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'completed_at']
    actions = ['send_campaign', 'cancel_campaign']
    
    def success_rate(self, obj):
        return f"{obj.success_rate}%"
    success_rate.short_description = 'Успешность'
    
    def send_campaign(self, request, queryset):
        # Здесь будет логика отправки кампании
        sent = 0
        for campaign in queryset:
            if campaign.status == 'draft' or campaign.status == 'scheduled':
                campaign.status = 'sending'
                campaign.save()
                sent += 1
        self.message_user(request, f'{sent} кампаний отправлено.')
    send_campaign.short_description = "Отправить выбранные кампании"
    
    def cancel_campaign(self, request, queryset):
        cancelled = 0
        for campaign in queryset:
            if campaign.status in ['draft', 'scheduled', 'sending']:
                campaign.status = 'cancelled'
                campaign.save()
                cancelled += 1
        self.message_user(request, f'{cancelled} кампаний отменено.')
    cancel_campaign.short_description = "Отменить выбранные кампании"

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    """Системные настройки"""
    list_display = ['name', 'key', 'setting_type', 'is_public', 'category', 'value_preview']
    list_filter = ['setting_type', 'is_public', 'category']
    search_fields = ['name', 'key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def value_preview(self, obj):
        if len(obj.value) > 50:
            return obj.value[:50] + '...'
        return obj.value
    value_preview.short_description = 'Значение'

# === КАСТОМНАЯ АДМИНКА С ДАШБОРДОМ ===

class CustomAdminSite(admin.AdminSite):
    """Кастомная админка с расширенными возможностями"""
    site_header = 'Административная панель онлайн-школы'
    site_title = 'Админка онлайн-школы'
    index_title = 'Панель управления'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('reports/', self.admin_view(self.reports_view), name='reports'),
            path('mass-email/', self.admin_view(self.mass_email_view), name='mass_email'),
            path('user-activity/', self.admin_view(self.user_activity_view), name='user_activity'),
            path('api/stats/', self.admin_view(self.api_stats), name='api_stats'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Дашборд администратора"""
        # Статистика пользователей
        user_stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'students': User.objects.filter(role='student').count(),
            'teachers': User.objects.filter(role='teacher').count(),
            'parents': User.objects.filter(role='parent').count(),
        }
        
        # Статистика курсов
        course_stats = {
            'total_courses': Course.objects.count(),
            'active_courses': Course.objects.filter(is_active=True).count(),
            'total_groups': Group.objects.count(),
            'active_groups': Group.objects.filter(is_active=True).count(),
        }
        
        # Статистика платежей
        payment_stats = {
            'total_payments': Payment.objects.count(),
            'paid_payments': Payment.objects.filter(status='paid').count(),
            'total_revenue': Payment.objects.filter(status='paid').aggregate(
                Sum('amount')
            )['amount__sum'] or 0,
        }
        
        # Статистика занятий
        lesson_stats = {
            'total_lessons': Lesson.objects.count(),
            'completed_lessons': Lesson.objects.filter(is_completed=True).count(),
            'today_lessons': Lesson.objects.filter(
                start_time__date=timezone.now().date()
            ).count(),
        }
        
        context = dict(
            self.each_context(request),
            user_stats=user_stats,
            course_stats=course_stats,
            payment_stats=payment_stats,
            lesson_stats=lesson_stats,
        )
        return render(request, 'admin/dashboard.html', context)
    
    def reports_view(self, request):
        """Страница отчетов"""
        context = dict(
            self.each_context(request),
        )
        return render(request, 'admin/reports.html', context)
    
    def mass_email_view(self, request):
        """Страница массовой рассылки"""
        if request.method == 'POST':
            # Здесь будет логика отправки массовых email
            messages.success(request, 'Массовая рассылка отправлена!')
            return HttpResponseRedirect('/admin/mass-email/')
        
        context = dict(
            self.each_context(request),
        )
        return render(request, 'admin/mass_email.html', context)
    
    def user_activity_view(self, request):
        """Страница активности пользователей"""
        context = dict(
            self.each_context(request),
        )
        return render(request, 'admin/user_activity.html', context)
    
    def api_stats(self, request):
        """API для получения статистики"""
        # Здесь будет возвращаться JSON с данными для графиков
        return JsonResponse({'status': 'ok'})

# === РЕГИСТРАЦИЯ МОДЕЛЕЙ ===

# Создаем инстанс кастомной админки
custom_admin_site = CustomAdminSite(name='custom_admin')

# Регистрируем модели в кастомной админке
custom_admin_site.register(AdminActionLog, AdminActionLogAdmin)
custom_admin_site.register(ReportTemplate, ReportTemplateAdmin)
custom_admin_site.register(GeneratedReport, GeneratedReportAdmin)
custom_admin_site.register(MassEmailCampaign, MassEmailCampaignAdmin)
custom_admin_site.register(SystemSetting, SystemSettingAdmin)

# Также регистрируем в стандартной админке для совместимости
admin.site.register(AdminActionLog, AdminActionLogAdmin)
admin.site.register(ReportTemplate, ReportTemplateAdmin)
admin.site.register(GeneratedReport, GeneratedReportAdmin)
admin.site.register(MassEmailCampaign, MassEmailCampaignAdmin)
admin.site.register(SystemSetting, SystemSettingAdmin)