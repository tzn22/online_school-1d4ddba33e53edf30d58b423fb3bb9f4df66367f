from django.contrib import admin
from .models import Feedback, FeedbackResponse, Survey, SurveyQuestion, SurveyResponse

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'student', 'feedback_type', 'rating', 'status', 
        'is_anonymous', 'created_at'
    ]
    list_filter = [
        'feedback_type', 'status', 'rating', 'is_anonymous', 'created_at'
    ]
    search_fields = [
        'title', 'content', 'student__username', 'student__email'
    ]
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Преподаватели видят отзывы о себе
        if hasattr(request.user, 'role') and request.user.role == 'teacher':
            return qs.filter(teacher=request.user)
        return qs.none()

@admin.register(FeedbackResponse)
class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ['feedback', 'responder', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = [
        'feedback__title', 'content', 'responder__username'
    ]
    readonly_fields = ['created_at']

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'target_audience', 'status', 'start_date', 'end_date'
    ]
    list_filter = ['status', 'target_audience', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']

class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 1
    ordering = ['order']

@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = [
        'survey', 'question_text', 'question_type', 'is_required', 'order'
    ]
    list_filter = ['question_type', 'is_required', 'survey']
    search_fields = ['question_text']
    ordering = ['survey', 'order']

@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['survey', 'respondent', 'submitted_at']
    list_filter = ['survey', 'submitted_at']
    search_fields = [
        'survey__title', 'respondent__username', 'respondent__email'
    ]
    readonly_fields = ['submitted_at']