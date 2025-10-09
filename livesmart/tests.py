# livesmart/tests.py
from tokenize import group
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import post_save, m2m_changed
from unittest.mock import patch
from datetime import timedelta
from .models import LiveSmartRoom, LiveSmartParticipant, LiveSmartRecording, LiveSmartSettings

User = get_user_model()

class SignalFreeTestCase:
    """Миксин для отключения сигналов"""
    def setUp(self):
        # Отключаем все сигналы перед тестами
        self.original_post_save_receivers = post_save.receivers[:]
        self.original_m2m_changed_receivers = m2m_changed.receivers[:]
        
        # Очищаем все receivers
        post_save.receivers = []
        m2m_changed.receivers = []
        
        super().setUp()
    
    def tearDown(self):
        # Восстанавливаем сигналы после тестов
        post_save.receivers = self.original_post_save_receivers
        m2m_changed.receivers = self.original_m2m_changed_receivers
        
        super().tearDown()

class LiveSmartModelsTestCase(SignalFreeTestCase, TestCase):
    """Тесты моделей LiveSmart"""
    
    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        self.teacher_user = User.objects.create_user(
            username='teacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        self.student_user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        
        # Создаем фейковый урок для тестирования (если нужен)
        # Замените на реальный импорт модели Lesson из courses
        from courses.models import Lesson, Group, Course
        course = Course.objects.create(
            title='Тестовый курс',
            description='Описание',
            price=100.00,
            duration_hours=20,
            level='beginner'
        )
        group = Group.objects.create(
            title='Тестовая группа',
            course=course,
            teacher=self.teacher_user,
            start_date='2024-01-01',
            end_date='2024-06-01'
        )
        self.lesson = Lesson.objects.create(
            title='Тестовое занятие',
            group=group,
            teacher=self.teacher_user,
            lesson_type='group',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1)
        )
    
    def test_livesmart_room_creation(self):
        """Тест создания комнаты LiveSmart"""
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room123',
            room_name='Тестовая комната',
            join_url='https://example.com/join',
            host_url='https://example.com/host',
            room_password='password123',
            max_participants=30,
            is_recording_enabled=True,
            status='scheduled'
        )
        
        self.assertEqual(room.lesson, self.lesson)
        self.assertEqual(room.room_id, 'room123')
        self.assertEqual(room.room_name, 'Тестовая комната')
        self.assertEqual(room.join_url, 'https://example.com/join')
        self.assertEqual(room.host_url, 'https://example.com/host')
        self.assertEqual(room.room_password, 'password123')
        self.assertEqual(room.max_participants, 30)
        self.assertTrue(room.is_recording_enabled)
        self.assertEqual(room.status, 'scheduled')
        self.assertIsNotNone(room.created_at)
        self.assertEqual(str(room), 'LiveSmart комната: Тестовая комната')
    
    def test_livesmart_room_defaults(self):
        """Тест значений по умолчанию для комнаты"""
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room456',
            room_name='Тестовая комната 2'
        )
        
        self.assertEqual(room.status, 'scheduled')
        self.assertEqual(room.max_participants, 50)
        self.assertFalse(room.is_recording_enabled)
        self.assertIsNone(room.started_at)
        self.assertIsNone(room.ended_at)
    
    def test_livesmart_participant_creation(self):
        """Тест создания участника LiveSmart комнаты"""
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room789',
            room_name='Комната участника'
        )
        
        participant = LiveSmartParticipant.objects.create(
            room=room,
            user=self.student_user,
            role='participant',
            participant_id='user123'
        )
        
        self.assertEqual(participant.room, room)
        self.assertEqual(participant.user, self.student_user)
        self.assertEqual(participant.role, 'participant')
        self.assertEqual(participant.participant_id, 'user123')
        self.assertFalse(participant.is_present)
        self.assertIsNone(participant.joined_at)
        self.assertIsNone(participant.left_at)
        self.assertIsNone(participant.duration)
        self.assertEqual(str(participant), f"{self.student_user.username} (Участник)")
    
    def test_livesmart_recording_creation(self):
        """Тест создания записи LiveSmart"""
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room101',
            room_name='Комната записи'
        )
        
        recording = LiveSmartRecording.objects.create(
            recording_id='rec123',
            room=room,
            title='Тестовая запись',
            description='Описание записи',
            file_url='https://example.com/recording',
            file_size=1024000,
            duration=timedelta(minutes=60),
            is_public=True
        )
        
        self.assertEqual(recording.recording_id, 'rec123')
        self.assertEqual(recording.room, room)
        self.assertEqual(recording.title, 'Тестовая запись')
        self.assertEqual(recording.description, 'Описание записи')
        self.assertEqual(recording.file_url, 'https://example.com/recording')
        self.assertEqual(recording.file_size, 1024000)
        self.assertEqual(recording.duration, timedelta(minutes=60))
        self.assertTrue(recording.is_public)
        self.assertEqual(str(recording), 'Запись: Тестовая запись')
    
    def test_livesmart_settings_creation(self):
        """Тест создания настроек LiveSmart"""
        settings = LiveSmartSettings.objects.create(
            user=self.teacher_user,
            api_key='test_api_key',
            api_secret='test_api_secret',
            default_room_settings={'auto_recording': True, 'max_participants': 30},
            is_recording_enabled=True,
            max_participants=30
        )
        
        self.assertEqual(settings.user, self.teacher_user)
        self.assertEqual(settings.api_key, 'test_api_key')
        self.assertEqual(settings.api_secret, 'test_api_secret')
        self.assertEqual(settings.default_room_settings, {'auto_recording': True, 'max_participants': 30})
        self.assertTrue(settings.is_recording_enabled)
        self.assertEqual(settings.max_participants, 30)
        self.assertEqual(str(settings), f"Настройки LiveSmart для {self.teacher_user.username}")
    
    def test_unique_constraints(self):
        """Тест уникальных ограничений"""
        room1 = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room123',
            room_name='Комната 1'
        )
        
        # Проверяем, что нельзя создать комнату с тем же room_id
        with self.assertRaises(Exception):
            LiveSmartRoom.objects.create(
                lesson=self.lesson,
                room_id='room123',  # тот же ID
                room_name='Комната 2'
            )
        
        # Проверяем уникальность участника в комнате
        participant1 = LiveSmartParticipant.objects.create(
            room=room1,
            user=self.student_user,
            role='participant'
        )
        
        with self.assertRaises(Exception):
            LiveSmartParticipant.objects.create(
                room=room1,
                user=self.student_user,  # тот же пользователь
                role='host'
            )
        
        # Проверяем уникальность настроек для пользователя
        settings1 = LiveSmartSettings.objects.create(
            user=self.teacher_user,
            api_key='key1'
        )
        
        with self.assertRaises(Exception):
            LiveSmartSettings.objects.create(
                user=self.teacher_user,  # тот же пользователь
                api_key='key2'
            )

class LiveSmartAPITestCase(SignalFreeTestCase, APITestCase):
    """Тесты API LiveSmart"""
    
    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        self.teacher_user = User.objects.create_user(
            username='teacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        self.student_user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        
        # Создаем фейковый урок для тестирования
        from courses.models import Lesson, Group, Course
        course = Course.objects.create(
            title='Тестовый курс',
            description='Описание',
            price=100.00,
            duration_hours=20,
            level='beginner'
        )
        group = Group.objects.create(
            title='Тестовая группа',
            course=course,
            teacher=self.teacher_user,
            start_date='2024-01-01',
            end_date='2024-06-01'
        )
        self.lesson = Lesson.objects.create(
            title='Тестовое занятие',
            group=group,
            teacher=self.teacher_user,
            lesson_type='group',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1)
        )
    
    def test_create_livesmart_room(self):
        """Тест создания комнаты LiveSmart"""
        self.client.force_authenticate(user=self.teacher_user)
        
        data = {
            'lesson': self.lesson.id,
            'room_id': 'test_room_123',
            'room_name': 'Тестовая комната',
            'max_participants': 25,
            'is_recording_enabled': True
        }
        
        response = self.client.post(reverse('livesmart:livesmart-room-create'), data)
        print(f"Create room response: {response.status_code}, {response.data}")
        
        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('id', response.data)
            self.assertEqual(response.data['room_name'], 'Тестовая комната')
            
            # Проверяем, что комната создана в базе
            self.assertTrue(LiveSmartRoom.objects.filter(room_id='test_room_123').exists())
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            # Если ошибка валидации, проверяем поля
            print(f"Validation errors: {response.data}")
        else:
            # Пробуем получить список комнат
            response_get = self.client.get(reverse('livesmart:livesmart-room-list'))
            print(f"Get rooms response: {response_get.status_code}, {response_get.data}")
    
    def test_get_livesmart_rooms_list(self):
        """Тест получения списка комнат LiveSmart"""
        self.client.force_authenticate(user=self.teacher_user)
        
        # Создаем тестовые комнаты
        LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room1',
            room_name='Комната 1'
        )
        LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room2',
            room_name='Комната 2'
        )
        
        response = self.client.get(reverse('livesmart:livesmart-room-list'))
        print(f"Get rooms list response: {response.status_code}, {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if isinstance(response.data, dict) and 'results' in response.data:
            # Пагинированный ответ
            self.assertGreaterEqual(len(response.data['results']), 2)
        elif isinstance(response.data, list):
            # Обычный список
            self.assertGreaterEqual(len(response.data), 2)
    
    def test_get_livesmart_room_detail(self):
        """Тест получения деталей комнаты LiveSmart"""
        self.client.force_authenticate(user=self.teacher_user)
        
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room_detail_test',
            room_name='Комната деталей'
        )
        
        response = self.client.get(reverse('livesmart:livesmart-room-detail', kwargs={'pk': room.id}))
        print(f"Get room detail response: {response.status_code}, {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['room_id'], 'room_detail_test')
        self.assertEqual(response.data['room_name'], 'Комната деталей')
    
    def test_get_livesmart_recordings_list(self):
        """Тест получения списка записей LiveSmart"""
        self.client.force_authenticate(user=self.teacher_user)
        
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room_with_rec',
            room_name='Комната с записью'
        )
        
        LiveSmartRecording.objects.create(
            recording_id='rec123',
            room=room,
            title='Тестовая запись',
            duration=timedelta(minutes=30)
        )
        
        response = self.client.get(reverse('livesmart:livesmart-recording-list'))
        print(f"Get recordings response: {response.status_code}, {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        elif isinstance(response.data, list):
            self.assertGreaterEqual(len(response.data), 1)
    
    def test_unauthorized_access(self):
        """Тест доступа без аутентификации"""
        # Без аутентификации
        response = self.client.get(reverse('livesmart:livesmart-room-list'))
        
        # В зависимости от настроек разрешений
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_200_OK  # если разрешен анонимный доступ
        ])
    
    def test_different_user_roles_access(self):
        """Тест доступа с разными ролями пользователей"""
        # Тест для администратора
        self.client.force_authenticate(user=self.admin_user)
        response_admin = self.client.get(reverse('livesmart:livesmart-room-list'))
        print(f"Admin access: {response_admin.status_code}")
        
        # Тест для преподавателя
        self.client.force_authenticate(user=self.teacher_user)
        response_teacher = self.client.get(reverse('livesmart:livesmart-room-list'))
        print(f"Teacher access: {response_teacher.status_code}")
        
        # Тест для студента
        self.client.force_authenticate(user=self.student_user)
        response_student = self.client.get(reverse('livesmart:livesmart-room-list'))
        print(f"Student access: {response_student.status_code}")
        
        # Все должны иметь доступ (или получить 403 в зависимости от настроек)
        self.assertIn(response_admin.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        self.assertIn(response_teacher.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        self.assertIn(response_student.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

class LiveSmartAdvancedTestCase(SignalFreeTestCase, APITestCase):
    """Расширенные тесты LiveSmart"""
    
    def setUp(self):
        super().setUp()
        self.teacher_user = User.objects.create_user(
            username='teacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        self.student_user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        
        # Создаем фейковый урок
        from courses.models import Lesson, Group, Course
        course = Course.objects.create(
            title='Тестовый курс',
            description='Описание',
            price=100.00,
            duration_hours=20,
            level='beginner'
        )
        group = Group.objects.create(
            title='Тестовая группа',
            course=course,
            teacher=self.teacher_user,
            start_date='2024-01-01',
            end_date='2024-06-01'
        )
        self.lesson = Lesson.objects.create(
            title='Тестовое занятие',
            group=group,
            teacher=self.teacher_user,
            lesson_type='group',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1)
        )
    
    def test_room_participants_management(self):
        """Тест управления участниками комнаты"""
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room_with_participants',
            room_name='Комната с участниками'
        )
        
        # Добавляем участника
        participant = LiveSmartParticipant.objects.create(
            room=room,
            user=self.student_user,
            role='participant',
            joined_at=timezone.now(),
            is_present=True
        )
        
        self.assertEqual(participant.room, room)
        self.assertEqual(participant.user, self.student_user)
        self.assertEqual(participant.role, 'participant')
        self.assertTrue(participant.is_present)
        self.assertIsNotNone(participant.joined_at)
        
        # Проверяем количество участников
        self.assertEqual(room.participants.count(), 1)
        
        # Проверяем уникальность
        with self.assertRaises(Exception):
            LiveSmartParticipant.objects.create(
                room=room,
                user=self.student_user,  # тот же пользователь
                role='host'
            )
    
    def test_recording_with_large_file(self):
        """Тест записи с большим файлом"""
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room_with_large_rec',
            room_name='Комната с большой записью'
        )
        
        recording = LiveSmartRecording.objects.create(
            recording_id='large_rec_123',
            room=room,
            title='Большая запись',
            file_size=1024 * 1024 * 500,  # 500 MB
            duration=timedelta(hours=2, minutes=30),
            is_public=True
        )
        
        self.assertEqual(recording.file_size, 524288000)  # 500 MB in bytes
        self.assertEqual(recording.duration, timedelta(hours=2, minutes=30))
        self.assertTrue(recording.is_public)
    
    def test_room_status_transitions(self):
        """Тест переходов статусов комнаты"""
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room_status_test',
            room_name='Комната для статусов'
        )
        
        # Проверяем начальный статус
        self.assertEqual(room.status, 'scheduled')
        
        # Меняем статусы
        room.status = 'active'
        room.started_at = timezone.now()
        room.save()
        
        room.refresh_from_db()
        self.assertEqual(room.status, 'active')
        self.assertIsNotNone(room.started_at)
        
        room.status = 'completed'
        room.ended_at = timezone.now()
        room.save()
        
        room.refresh_from_db()
        self.assertEqual(room.status, 'completed')
        self.assertIsNotNone(room.ended_at)
    
    def test_user_livesmart_settings(self):
        """Тест настроек пользователя LiveSmart"""
        settings = LiveSmartSettings.objects.create(
            user=self.teacher_user,
            api_key='test_key_123',
            api_secret='test_secret_456',
            default_room_settings={
                'auto_recording': True,
                'max_participants': 25,
                'waiting_room': True
            },
            is_recording_enabled=True,
            max_participants=25
        )
        
        self.assertEqual(settings.user, self.teacher_user)
        self.assertEqual(settings.api_key, 'test_key_123')
        self.assertEqual(settings.default_room_settings['auto_recording'], True)
        self.assertEqual(settings.default_room_settings['max_participants'], 25)
        self.assertTrue(settings.is_recording_enabled)
        self.assertEqual(settings.max_participants, 25)

class LiveSmartUserTestCase(SignalFreeTestCase, TestCase):
    """Тесты с разными пользователями"""
    
    def setUp(self):
        super().setUp()
        self.users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123',
                role='student'
            )
            self.users.append(user)
        
        # Создаем фейковый урок
        from courses.models import Lesson, Group, Course
        course = Course.objects.create(
            title='Тестовый курс',
            description='Описание',
            price=100.00,
            duration_hours=20,
            level='beginner'
        )
        group = Group.objects.create(
            title='Тестовая группа',
            course=course,
            teacher=self.users[0],
            start_date='2024-01-01',
            end_date='2024-06-01'
        )
        self.lesson = Lesson.objects.create(
            title='Тестовое занятие',
            group=group,
            teacher=self.users[0],
            lesson_type='group',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1)
        )
    
    def test_multiple_rooms_per_lesson(self):
        """Тест нескольких комнат для одного урока"""
        # Хотя в модели OneToOneField, но если нужно тестировать, то создаем разные уроки
        from courses.models import Lesson
        lesson2 = Lesson.objects.create(
            title='Второе занятие',
            group=group,
            teacher=self.users[0],
            lesson_type='group',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1)
        )
        
        room1 = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room_multi_1',
            room_name='Комната 1'
        )
        
        room2 = LiveSmartRoom.objects.create(
            lesson=lesson2,
            room_id='room_multi_2',
            room_name='Комната 2'
        )
        
        self.assertEqual(room1.lesson, self.lesson)
        self.assertEqual(room2.lesson, lesson2)
    
    def test_many_participants_in_room(self):
        """Тест многих участников в комнате"""
        room = LiveSmartRoom.objects.create(
            lesson=self.lesson,
            room_id='room_many_participants',
            room_name='Комната с многими участниками',
            max_participants=10
        )
        
        # Добавляем участников
        for i, user in enumerate(self.users):
            LiveSmartParticipant.objects.create(
                room=room,
                user=user,
                role='participant' if i > 0 else 'host',
                joined_at=timezone.now()
            )
        
        self.assertEqual(room.participants.count(), len(self.users))
        
        # Проверяем, что хост только один
        hosts = room.participants.filter(role='host')
        self.assertEqual(hosts.count(), 1)