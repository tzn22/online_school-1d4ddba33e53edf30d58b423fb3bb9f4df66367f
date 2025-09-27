from rest_framework import serializers
from .models import ChatRoom, Message, MessageReadStatus, ChatSettings
from accounts.models import User

class ChatRoomSerializer(serializers.ModelSerializer):
    participants_data = serializers.SerializerMethodField(read_only=True)
    unread_messages_count = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ChatRoom
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_participants_data(self, obj):
        return [
            {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'avatar': user.avatar.url if user.avatar else None
            }
            for user in obj.participants.all()
        ]
    
    def get_unread_messages_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(
                is_read=False
            ).exclude(sender=request.user).count()
        return 0
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'id': last_msg.id,
                'content': last_msg.content,
                'sender': last_msg.sender.get_full_name() or last_msg.sender.username,
                'created_at': last_msg.created_at
            }
        return None

class MessageSerializer(serializers.ModelSerializer):
    sender_data = serializers.SerializerMethodField(read_only=True)
    reply_to_data = serializers.SerializerMethodField(read_only=True)
    is_read_by_me = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'sender', 'is_read', 'is_edited']
    
    def get_sender_data(self, obj):
        return {
            'id': obj.sender.id,
            'username': obj.sender.username,
            'full_name': obj.sender.get_full_name(),
            'avatar': obj.sender.avatar.url if obj.sender.avatar else None
        }
    
    def get_reply_to_data(self, obj):
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'content': obj.reply_to.content,
                'sender': obj.reply_to.sender.get_full_name() or obj.reply_to.sender.username
            }
        return None
    
    def get_is_read_by_me(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.read_statuses.filter(user=request.user).exists()
        return False

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['room', 'content', 'message_type', 'file', 'image', 'reply_to']
        read_only_fields = ['sender']
    
    def validate(self, attrs):
        content = attrs.get('content', '')
        file = attrs.get('file')
        image = attrs.get('image')
        message_type = attrs.get('message_type', 'text')
        
        # Проверка, что есть содержимое для текстового сообщения
        if message_type == 'text' and not content.strip():
            raise serializers.ValidationError('Текст сообщения не может быть пустым')
        
        # Проверка, что для файлового сообщения прикреплен файл
        if message_type == 'file' and not file:
            raise serializers.ValidationError('Необходимо прикрепить файл')
        
        # Проверка, что для изображения прикреплено изображение
        if message_type == 'image' and not image:
            raise serializers.ValidationError('Необходимо прикрепить изображение')
        
        return attrs

class ChatSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSettings
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class UnreadMessagesSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    unread_count = serializers.IntegerField()