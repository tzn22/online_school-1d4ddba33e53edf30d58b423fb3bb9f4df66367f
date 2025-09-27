from django.contrib import admin
from .models import ChatRoom, Message, MessageReadStatus, ChatSettings

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'chat_type', 'created_by', 'participant_count', 'is_active', 'created_at']
    list_filter = ['chat_type', 'is_active', 'created_at']
    search_fields = ['name', 'participants__username', 'participants__email']
    filter_horizontal = ['participants']
    readonly_fields = ['created_at', 'updated_at']
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Количество участников'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room', 'message_type', 'short_content', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'created_at', 'room']
    search_fields = ['content', 'sender__username', 'room__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Содержание'

@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'read_at']
    list_filter = ['read_at']
    search_fields = ['message__content', 'user__username']

@admin.register(ChatSettings)
class ChatSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'notifications_enabled', 'message_notifications', 'sound_enabled']
    list_filter = ['notifications_enabled', 'message_notifications', 'sound_enabled']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']