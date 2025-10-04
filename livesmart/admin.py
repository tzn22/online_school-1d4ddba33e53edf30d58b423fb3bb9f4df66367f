# livesmart/admin.py
from django.contrib import admin
from .models import LiveSmartRoom, LiveSmartParticipant, LiveSmartRecording, LiveSmartSettings

@admin.register(LiveSmartRoom)
class LiveSmartRoomAdmin(admin.ModelAdmin):
    list_display = ['room_name', 'lesson', 'status', 'max_participants', 'is_recording_enabled', 'created_at']
    list_filter = ['status', 'is_recording_enabled', 'created_at', 'lesson__lesson_type']
    search_fields = ['room_name', 'lesson__title', 'room_id']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'ended_at']

@admin.register(LiveSmartParticipant)
class LiveSmartParticipantAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'role', 'is_present', 'joined_at', 'left_at']
    list_filter = ['role', 'is_present', 'joined_at', 'left_at']
    search_fields = ['room__room_name', 'user__username', 'user__email']
    readonly_fields = ['joined_at', 'left_at', 'duration']

@admin.register(LiveSmartRecording)
class LiveSmartRecordingAdmin(admin.ModelAdmin):
    list_display = ['title', 'room', 'file_size', 'is_public', 'uploaded_by', 'created_at']
    list_filter = ['is_public', 'uploaded_by', 'created_at']
    search_fields = ['title', 'description', 'room__room_name']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'file_size']

@admin.register(LiveSmartSettings)
class LiveSmartSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_recording_enabled', 'max_participants', 'created_at']
    list_filter = ['is_recording_enabled', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']