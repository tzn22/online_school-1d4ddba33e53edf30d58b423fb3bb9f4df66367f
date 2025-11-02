import django_filters
from django.db import models
from .models import AITrainingSession
from courses.models import Course, Lesson
from ai_trainer.models import AITrainerPrompt

class AITrainingSessionFilter(django_filters.FilterSet):
    created_at = django_filters.DateFromToRangeFilter()
    prompt = django_filters.ModelChoiceFilter(queryset=AITrainerPrompt.objects.all())
    course = django_filters.ModelChoiceFilter(queryset=Course.objects.all())
    lesson = django_filters.ModelChoiceFilter(queryset=Lesson.objects.all())

    class Meta:
        model = AITrainingSession
        fields = ['user', 'level', 'completed', 'prompt', 'course', 'lesson', 'created_at']
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }
