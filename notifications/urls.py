from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    NotificationTemplateListView,
    NotificationTemplateDetailView,
    UserNotificationSettingsView,
    mark_notification_as_read,
    mark_all_as_read,
    get_unread_count,
    send_bulk_notification,
    send_test_notification,
    notification_statistics,
    clear_notifications
)

urlpatterns = [
    # Уведомления пользователя
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<int:notification_id>/read/', mark_notification_as_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', mark_all_as_read, name='mark-all-read'),
    path('notifications/unread-count/', get_unread_count, name='unread-count'),
    path('notifications/clear/', clear_notifications, name='clear-notifications'),
    
    # Шаблоны уведомлений
    path('templates/', NotificationTemplateListView.as_view(), name='notification-template-list'),
    path('templates/<int:pk>/', NotificationTemplateDetailView.as_view(), name='notification-template-detail'),
    
    # Настройки уведомлений
    path('settings/', UserNotificationSettingsView.as_view(), name='user-notification-settings'),
    
    # Админские функции
    path('bulk-send/', send_bulk_notification, name='send-bulk-notification'),
    path('test/', send_test_notification, name='send-test-notification'),
    path('statistics/', notification_statistics, name='notification-statistics'),
]
