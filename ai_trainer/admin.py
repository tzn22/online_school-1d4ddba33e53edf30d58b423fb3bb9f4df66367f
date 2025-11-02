from django.contrib import admin
from .models import AITrainerPrompt, AITrainingSession


@admin.register(AITrainerPrompt)
class AITrainerPromptAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'lesson', 'is_active', 'created_at')
    list_filter = ('is_active', 'course', 'lesson')
    search_fields = ('title', 'description', 'prompt_text')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('course', 'lesson', 'created_by')


@admin.register(AITrainingSession)
class AITrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'prompt', 'course', 'lesson', 'level', 'completed', 'created_at')
    readonly_fields = ('created_at', 'evaluation')
    search_fields = ('user__username', 'prompt__title', 'course__title', 'lesson__title')
    list_filter = ('completed', 'level', 'course', 'lesson')
