# livesmart/serializers.py
from rest_framework import serializers
from .models import LiveSmartRoom, LiveSmartParticipant, LiveSmartRecording, LiveSmartSettings
from accounts.models import User
from courses.models import Lesson

class LiveSmartRoomSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    teacher_name = serializers.CharField(source='lesson.teacher.get_full_name', read_only=True)
    course_title = serializers.CharField(source='lesson.group.course.title', read_only=True, allow_null=True)
    student_name = serializers.CharField(source='lesson.student.get_full_name', read_only=True, allow_null=True)
    duration_minutes = serializers.IntegerField(source='lesson.duration_minutes', read_only=True)
    
    class Meta:
        model = LiveSmartRoom
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'started_at', 'ended_at']

class LiveSmartParticipantSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    room_name = serializers.CharField(source='room.room_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = LiveSmartParticipant
        fields = '__all__'
        read_only_fields = ['joined_at', 'left_at', 'duration', 'participant_id']

class LiveSmartRecordingSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.room_name', read_only=True)
    lesson_title = serializers.CharField(source='room.lesson.title', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = LiveSmartRecording
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'published_at', 'file_size']

class LiveSmartSettingsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = LiveSmartSettings
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']