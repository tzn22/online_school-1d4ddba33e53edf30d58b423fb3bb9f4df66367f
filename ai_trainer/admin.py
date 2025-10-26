from django.contrib import admin
from django.utils.html import format_html
from .models import AITrainingSession

@admin.register(AITrainingSession)
class AITrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'level', 'completed', 'created_at')
    readonly_fields = ('created_at', 'evaluation')
    search_fields = ('user__username', 'level')

# Добавляем функционал в материалы занятий
try:
    from courses.models import LessonMaterial
    
    @admin.register(LessonMaterial)
    class LessonMaterialAdmin(admin.ModelAdmin):
        list_display = ['title', 'lesson', 'material_type', 'is_required', 'created_at']
        list_filter = ['material_type', 'is_required', 'created_at']
        search_fields = ['title', 'description', 'lesson__title']
        ordering = ['-created_at']
        readonly_fields = ['created_at']
        
        def ai_trainer_button(self, obj):
            return format_html(
                '<a class="button" href="{}" style="background-color: #2196F3; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Создать ИИ-тренажер</a>',
                f'../generate-ai-trainer/{obj.id}/'
            )
        ai_trainer_button.short_description = 'ИИ-тренажер'
        
        list_display = ['title', 'lesson', 'material_type', 'is_required', 'ai_trainer_button', 'created_at']

except ImportError:
    # Модель LessonMaterial не существует, пропускаем
    pass