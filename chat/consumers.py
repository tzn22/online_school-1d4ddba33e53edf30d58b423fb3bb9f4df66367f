import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, MessageReadStatus
from accounts.models import User

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
        else:
            # Присоединяемся к группам всех чатов пользователя
            user_rooms = await self.get_user_rooms()
            for room in user_rooms:
                await self.channel_layer.group_add(
                    f"chat_{room.id}",
                    self.channel_name
                )
            
            # Присоединяемся к группе пользователя для личных уведомлений
            await self.channel_layer.group_add(
                f"user_{self.user.id}",
                self.channel_name
            )
            
            await self.accept()
            
            # Отправляем статус "онлайн"
            await self.set_user_online(True)

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            # Покидаем все группы
            user_rooms = await self.get_user_rooms()
            for room in user_rooms:
                await self.channel_layer.group_discard(
                    f"chat_{room.id}",
                    self.channel_name
                )
            
            await self.channel_layer.group_discard(
                f"user_{self.user.id}",
                self.channel_name
            )
            
            # Отправляем статус "оффлайн"
            await self.set_user_online(False)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'message':
            await self.handle_new_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read':
            await self.handle_message_read(data)

    async def handle_new_message(self, data):
        """Обработка нового сообщения"""
        room_id = data.get('room_id')
        content = data.get('content')
        message_type = data.get('message_type', 'text')
        
        # Проверяем, что пользователь участник чата
        room = await self.get_room(room_id)
        if not room or not await self.is_user_in_room(room):
            return
        
        # Создаем сообщение
        message = await self.create_message(room, content, message_type)
        
        # Отправляем сообщение всем участникам чата
        await self.channel_layer.group_send(
            f"chat_{room_id}",
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': {
                        'id': message.sender.id,
                        'username': message.sender.username,
                        'full_name': message.sender.get_full_name(),
                    },
                    'room_id': room_id,
                    'created_at': message.created_at.isoformat(),
                    'message_type': message.message_type,
                }
            }
        )

    async def handle_typing(self, data):
        """Обработка индикатора набора текста"""
        room_id = data.get('room_id')
        is_typing = data.get('is_typing', False)
        
        # Отправляем статус набора текста другим участникам
        await self.channel_layer.group_send(
            f"chat_{room_id}",
            {
                'type': 'typing_indicator',
                'user': {
                    'id': self.user.id,
                    'username': self.user.username,
                    'full_name': self.user.get_full_name(),
                },
                'is_typing': is_typing,
                'room_id': room_id,
            }
        )

    async def handle_message_read(self, data):
        """Обработка прочтения сообщения"""
        message_id = data.get('message_id')
        room_id = data.get('room_id')
        
        # Отмечаем сообщение как прочитанное
        await self.mark_message_as_read(message_id)
        
        # Уведомляем других участников
        await self.channel_layer.group_send(
            f"chat_{room_id}",
            {
                'type': 'message_read',
                'message_id': message_id,
                'user_id': self.user.id,
                'room_id': room_id,
            }
        )

    async def chat_message(self, event):
        """Отправка сообщения клиенту"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message']
        }))

    async def typing_indicator(self, event):
        """Отправка индикатора набора текста"""
        # Не отправляем себе же
        if event['user']['id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'data': event
            }))

    async def message_read(self, event):
        """Отправка уведомления о прочтении сообщения"""
        await self.send(text_data=json.dumps({
            'type': 'read',
            'data': event
        }))

    @database_sync_to_async
    def get_user_rooms(self):
        return list(ChatRoom.objects.filter(participants=self.user, is_active=True))

    @database_sync_to_async
    def get_room(self, room_id):
        try:
            return ChatRoom.objects.get(id=room_id, is_active=True)
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def is_user_in_room(self, room):
        return room.participants.filter(id=self.user.id).exists()

    @database_sync_to_async
    def create_message(self, room, content, message_type):
        return Message.objects.create(
            room=room,
            sender=self.user,
            content=content,
            message_type=message_type
        )

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            if message.sender != self.user:
                MessageReadStatus.objects.get_or_create(
                    message=message,
                    user=self.user
                )
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def set_user_online(self, is_online):
        # Здесь можно реализовать логику отслеживания онлайн-статуса
        pass