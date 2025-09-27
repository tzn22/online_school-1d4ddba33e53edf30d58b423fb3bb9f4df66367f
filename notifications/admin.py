from django.contrib import admin
from .models import Notification, NotificationTemplate, UserNotificationSettings, NotificationLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'channel', 'is_read', 'is_sent', 'created_at']
    list_filter = ['notification_type', 'channel', 'is_read', 'is_sent', 'created_at']
    search_fields = ['title', 'message', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'sent_at', 'read_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Ограничиваем просмотр уведомлений только для суперпользователей
        return qs.none()

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'is_active', 'created_at']
    list_filter = ['notification_type', 'is_active', 'created_at']
    search_fields = ['name', 'title_template']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserNotificationSettings)
class UserNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_notifications', 'push_notifications', 
        'telegram_notifications', 'whatsapp_notifications'
    ]
    list_filter = [
        'email_notifications', 'push_notifications', 
        'telegram_notifications', 'whatsapp_notifications'
    ]
    search_fields = ['user__username', 'user__email', 'telegram_chat_id']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'channel', 'status', 'created_at']
    list_filter = ['channel', 'status', 'created_at']
    search_fields = ['notification__title', 'error_message']
    readonly_fields = ['created_at', 'sent_at']