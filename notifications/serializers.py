from rest_framework import serializers
from .models import Notification, NotificationTemplate, UserNotificationSettings, NotificationLog
from accounts.models import User

class NotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at', 'sent_at', 'read_at', 'user']

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['user', 'title', 'message', 'notification_type', 'channels']
    
    def validate(self, attrs):
        # Проверяем, что пользователь существует
        user = attrs.get('user')
        if not user:
            raise serializers.ValidationError('Пользователь обязателен')
        return attrs

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class UserNotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationSettings
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def validate_telegram_chat_id(self, value):
        if value and not value.startswith('-') and not value.isdigit():
            raise serializers.ValidationError('Неверный формат Telegram Chat ID')
        return value

class NotificationLogSerializer(serializers.ModelSerializer):
    notification_title = serializers.CharField(source='notification.title', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = '__all__'
        read_only_fields = ['created_at', 'sent_at']

# === НОВЫЕ СЕРИАЛИЗАТОРЫ ДЛЯ ПРЕПОДАВАТЕЛЯ ===

class BulkNotificationSerializer(serializers.Serializer):
    """Сериализатор для массовой отправки уведомлений"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    roles = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    notification_type = serializers.ChoiceField(
        choices=[choice[0] for choice in Notification.NOTIFICATION_TYPE_CHOICES]
    )
    channels = serializers.ListField(
        child=serializers.ChoiceField(
            choices=[choice[0] for choice in Notification.NOTIFICATION_CHANNEL_CHOICES]
        )
    )
    
    def validate(self, attrs):
        user_ids = attrs.get('user_ids', [])
        roles = attrs.get('roles', [])
        
        if not user_ids and not roles:
            raise serializers.ValidationError('Необходимо указать пользователей или роли')
        
        return attrs
