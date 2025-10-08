import django_filters
from django.db import models
from .models import Notification, NotificationTemplate, NotificationLog

class NotificationFilter(django_filters.FilterSet):
    class Meta:
        model = Notification
        fields = ['user', 'notification_type', 'is_read', 'is_sent', 'created_at']
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

class NotificationTemplateFilter(django_filters.FilterSet):
    class Meta:
        model = NotificationTemplate
        fields = ['notification_type', 'is_active', 'created_at']
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

class NotificationLogFilter(django_filters.FilterSet):
    class Meta:
        model = NotificationLog
        fields = ['user', 'notification_type', 'is_read', 'created_at']
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }
