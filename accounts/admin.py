from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, RegistrationProfile, SurveyQuestion, SurveyOption, SurveyResponse, LanguageTest, TestQuestion, TestOption, TestResult, ConsultationRequest

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'has_studied_language', 'is_staff', 'created_at')
    list_filter = ('role', 'has_studied_language', 'is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Персональная информация'), {
            'fields': ('first_name', 'last_name', 'email', 'birth_date', 'phone', 'avatar')
        }),
        (_('Права доступа'), {
            'fields': ('role', 'parent', 'has_studied_language', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'email', 'first_name', 'last_name', 'has_studied_language')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')

@admin.register(RegistrationProfile)
class RegistrationProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']

@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'question_type', 'is_required', 'order']
    list_filter = ['question_type', 'is_required']
    search_fields = ['question_text']

@admin.register(SurveyOption)
class SurveyOptionAdmin(admin.ModelAdmin):
    list_display = ['question', 'option_text', 'value']
    search_fields = ['option_text', 'question__question_text']

@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'created_at']
    list_filter = ['created_at', 'question']
    search_fields = ['user__username', 'question__question_text']

@admin.register(LanguageTest)
class LanguageTestAdmin(admin.ModelAdmin):
    list_display = ['title', 'duration_minutes', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']

from django.utils.html import format_html
@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'question_text', 'question_type', 'points', 'image_preview')
    list_filter = ('question_type', 'test')
    search_fields = ('question_text',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" />', obj.image.url)
        return "—"
    image_preview.short_description = 'Превью'

@admin.register(TestOption)
class TestOptionAdmin(admin.ModelAdmin):
    list_display = ['question', 'option_text', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['option_text', 'question__question_text']

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'test', 'score', 'percentage', 'level', 'completed_at']
    list_filter = ['level', 'completed_at', 'test']
    search_fields = ['user__username', 'test__title']

@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'language_level', 'status', 'requested_at']
    list_filter = ['status', 'language_level', 'requested_at']
    search_fields = ['name', 'email', 'phone']
    actions = ['mark_as_completed']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Отметить как завершенные"