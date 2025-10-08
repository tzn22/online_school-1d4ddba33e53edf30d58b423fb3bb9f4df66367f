import django_filters
from django.db import models
from .models import AITrainingSession


class AITrainingSessionFilter(django_filters.FilterSet):
    created_at = django_filters.DateFromToRangeFilter()

    class Meta:
        model = AITrainingSession
        fields = ['user', 'level', 'completed', 'created_at']
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }
