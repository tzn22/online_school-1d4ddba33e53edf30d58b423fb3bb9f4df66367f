from django.contrib import admin
from .models import AITrainingSession


@admin.register(AITrainingSession)
class AITrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'level', 'completed', 'created_at')
    readonly_fields = ('created_at', 'evaluation')
    search_fields = ('user__username', 'level')
