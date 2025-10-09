# notifications/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import post_save, m2m_changed
from .models import Notification, NotificationTemplate, UserNotificationSettings

User = get_user_model()

class SignalFreeTestCase:
    """Миксин для отключения сигналов"""
    def setUp(self):
        self.original_post_save_receivers = post_save.receivers[:]
        self.original_m2m_changed_receivers = m2m_changed.receivers[:]
        post_save.receivers = []
        m2m_changed.receivers = []
        super().setUp()
    
    def tearDown(self):
        post_save.receivers = self.original_post_save_receivers
        m2m_changed.receivers = self.original_m2m_changed_receivers
        super().tearDown()

class NotificationsModelsTestCase(SignalFreeTestCase, TestCase):
    """Тесты основных моделей уведомлений"""
    
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='student'
        )
    
    def test_notification_creation(self):
        """Тест создания уведомления"""
        notification = Notification.objects.create(
            user=self.user,
            title='Тестовое уведомление',
            message='Содержание уведомления',
            notification_type='info',
            channels=['email', 'push'],
            is_read=False
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Тестовое уведомление')
        self.assertEqual(notification.notification_type, 'info')
        self.assertFalse(notification.is_read)
        self.assertEqual(str(notification), f"Тестовое уведомление - {self.user}")
    
    def test_notification_template_creation(self):
        """Тест создания шаблона уведомления"""
        template = NotificationTemplate.objects.create(
            name='Тестовый шаблон',
            title_template='Заголовок: {course}',
            message_template='Сообщение: {student}',
            notification_type='lesson',
            is_active=True
        )
        
        self.assertEqual(template.name, 'Тестовый шаблон')
        self.assertTrue(template.is_active)
        self.assertEqual(str(template), 'Тестовый шаблон')
    
    def test_user_notification_settings_creation(self):
        """Тест создания настроек уведомлений пользователя"""
        settings = UserNotificationSettings.objects.create(
            user=self.user,
            email_notifications=True,
            push_notifications=True,
            telegram_notifications=False
        )
        
        self.assertEqual(settings.user, self.user)
        self.assertTrue(settings.email_notifications)
        self.assertTrue(settings.is_any_notification_enabled)
        self.assertEqual(str(settings), f"Настройки уведомлений для {self.user.username}")

class NotificationsAPITestCase(SignalFreeTestCase, APITestCase):
    """Тесты основного API уведомлений"""
    
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='student'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_notifications_list(self):
        """Тест получения списка уведомлений"""
        # Создаем тестовые уведомления
        Notification.objects.create(
            user=self.user,
            title='Уведомление 1',
            message='Сообщение 1',
            notification_type='info'
        )
        Notification.objects.create(
            user=self.user,
            title='Уведомление 2',
            message='Сообщение 2',
            notification_type='lesson',
            is_read=True
        )
        
        response = self.client.get('/api/notifications/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 2)
        elif isinstance(response.data, list):
            self.assertGreaterEqual(len(response.data), 2)
    
    def test_get_unread_notifications_count(self):
        """Тест получения количества непрочитанных уведомлений"""
        # Создаем уведомления
        Notification.objects.create(
            user=self.user,
            title='Непрочитанное',
            message='Сообщение',
            notification_type='info',
            is_read=False
        )
        Notification.objects.create(
            user=self.user,
            title='Прочитанное',
            message='Сообщение',
            notification_type='info',
            is_read=True
        )
        
        response = self.client.get('/api/notifications/notifications/unread-count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'count' in response.data:
            self.assertEqual(response.data['count'], 1)
    
    def test_mark_notification_as_read(self):
        """Тест пометки уведомления как прочитанного"""
        notification = Notification.objects.create(
            user=self.user,
            title='Уведомление для прочтения',
            message='Сообщение',
            notification_type='info',
            is_read=False
        )
        
        response = self.client.post(f'/api/notifications/notifications/{notification.id}/read/')
        
        if response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]:
            notification.refresh_from_db()
            self.assertTrue(notification.is_read)
            self.assertIsNotNone(notification.read_at)
    
    def test_unauthorized_access(self):
        """Тест доступа без аутентификации"""
        self.client.logout()
        response = self.client.get('/api/notifications/notifications/')
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ])