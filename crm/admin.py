from django.contrib import admin
from .models import StudentProfile, TeacherProfile, Lead, StudentActivity, AnalyticsReport

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'education_level', 'school', 'grade', 
        'target_language', 'language_level', 'created_at'
    ]
    list_filter = [
        'education_level', 'target_language', 'language_level', 
        'created_at'
    ]
    search_fields = [
        'student__username', 'student__email', 'student__first_name', 
        'student__last_name', 'school'
    ]
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = [
        'teacher', 'degree', 'university', 'years_of_experience', 
        'created_at'
    ]
    list_filter = [
        'degree', 'years_of_experience', 'created_at'
    ]
    search_fields = [
        'teacher__username', 'teacher__email', 'teacher__first_name', 
        'teacher__last_name', 'university', 'specialization'
    ]
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'first_name', 'last_name', 'email', 'phone', 'status', 
        'source', 'assigned_to', 'created_at'
    ]
    list_filter = [
        'status', 'source', 'assigned_to', 'created_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'phone', 'notes'
    ]
    readonly_fields = ['created_at', 'updated_at', 'converted_at']
    date_hierarchy = 'created_at'

@admin.register(StudentActivity)
class StudentActivityAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'activity_type', 'description', 'created_at'
    ]
    list_filter = [
        'activity_type', 'created_at'
    ]
    search_fields = [
        'student__username', 'student__email', 'description'
    ]
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'report_type', 'period_start', 'period_end', 
        'generated_by', 'generated_at', 'is_published'
    ]
    list_filter = [
        'report_type', 'is_published', 'generated_at'
    ]
    search_fields = [
        'title', 'generated_by__username'
    ]
    readonly_fields = ['generated_at']
    date_hierarchy = 'generated_at'