from django.contrib import admin
from .models import AITrainingSession
from django.utils.html import format_html


@admin.register(AITrainingSession)
class AITrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'level', 'completed', 'created_at')
    readonly_fields = ('created_at', 'evaluation')
    search_fields = ('user__username', 'level')
try:
    from courses.models import Lesson
    
    @admin.register(Lesson)
    class LessonAdmin(admin.ModelAdmin):
        list_display = ['title', 'lesson_type', 'teacher', 'start_time', 'has_ai_trainer', 'created_at']
        list_filter = ['lesson_type', 'teacher', 'has_ai_trainer', 'start_time', 'is_completed']
        search_fields = ['title', 'description']
        ordering = ['-created_at']
        readonly_fields = ['created_at', 'updated_at', 'duration_minutes']
        
        def get_queryset(self, request):
            qs = super().get_queryset(request)
            return qs.select_related('teacher', 'group')
        
        def ai_trainer_button(self, obj):
            if hasattr(obj, 'has_ai_trainer') and obj.has_ai_trainer:
                return format_html(
                    '<a class="button" href="{}" style="background-color: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Сгенерировать ИИ-вопросы</a>',
                    f'../generate-ai-trainer/{obj.id}/'
                )
            else:
                return format_html(
                    '<a class="button" href="{}" style="background-color: #2196F3; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Создать ИИ-тренажер</a>',
                    f'../generate-ai-trainer/{obj.id}/'
                )
        ai_trainer_button.short_description = 'ИИ-тренажер'
        
        list_display = ['title', 'lesson_type', 'teacher', 'start_time', 'has_ai_trainer', 'ai_trainer_button', 'created_at']

except ImportError:
    # Модель Lesson не существует, пропускаем
    pass

# Также добавим функционал в материалы занятий
try:
    from courses.models import LessonMaterial
    
    @admin.register(LessonMaterial)
    class LessonMaterialAdmin(admin.ModelAdmin):
        list_display = ['title', 'lesson', 'material_type', 'is_required', 'has_ai_trainer', 'created_at']
        list_filter = ['material_type', 'is_required', 'created_at']
        search_fields = ['title', 'description', 'lesson__title']
        ordering = ['-created_at']
        readonly_fields = ['created_at']
        
        def ai_trainer_button(self, obj):
            if hasattr(obj, 'has_ai_trainer') and obj.has_ai_trainer:
                return format_html(
                    '<a class="button" href="{}" style="background-color: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Сгенерировать ИИ-вопросы</a>',
                    f'../generate-ai-trainer/{obj.id}/'
                )
            else:
                return format_html(
                    '<a class="button" href="{}" style="background-color: #2196F3; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Создать ИИ-тренажер</a>',
                    f'../generate-ai-trainer/{obj.id}/'
                )
        ai_trainer_button.short_description = 'ИИ-тренажер'
        
        list_display = ['title', 'lesson', 'material_type', 'is_required', 'has_ai_trainer', 'ai_trainer_button', 'created_at']

except ImportError:
    # Модель LessonMaterial не существует, пропускаем
    pass