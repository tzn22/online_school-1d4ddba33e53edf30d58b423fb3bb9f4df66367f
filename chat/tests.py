from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import ChatRoom, Message

User = get_user_model()

class ChatTestCase(APITestCase):
    def setUp(self):
        # Создаем пользователей
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123',
            role='student'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            role='student'
        )
        
        # Создаем чат
        self.chat_room = ChatRoom.objects.create(
            chat_type='private',
            created_by=self.user1
        )
        self.chat_room.participants.add(self.user1, self.user2)
    
    def test_create_private_chat(self):
        """Тест создания приватного чата"""
        self.client.force_authenticate(user=self.user1)
        
        data = {'user_id': self.user2.id}
        response = self.client.post('/api/chat/rooms/create-private/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('room', response.data)
    
    def test_send_message(self):
        """Тест отправки сообщения"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'room': self.chat_room.id,
            'content': 'Привет, как дела?',
            'message_type': 'text'
        }
        
        response = self.client.post('/api/chat/messages/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Message.objects.filter(content='Привет, как дела?').exists())
    
    def test_get_chat_messages(self):
        """Тест получения сообщений чата"""
        # Создаем сообщение
        Message.objects.create(
            room=self.chat_room,
            sender=self.user1,
            content='Тестовое сообщение'
        )
        
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f'/api/chat/messages/?room={self.chat_room.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)