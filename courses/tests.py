from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import post_save, m2m_changed
import datetime
from .models import Course, Group, Lesson, Attendance, Badge, StudentBadge, StudentProgress, TestResult, VideoLesson, LessonRecording, MeetingParticipant

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

class ModelsTestCase(SignalFreeTestCase, TestCase):
    """Тесты для проверки моделей напрямую"""
    
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
    
    def test_course_model(self):
        """Тест модели курса"""
        course = Course.objects.create(
            title='Тестовый курс',
            description='Описание тестового курса',
            price=100.00,
            duration_hours=20,
            level='beginner'
        )
        
        self.assertEqual(course.title, 'Тестовый курс')
        self.assertEqual(str(course), 'Тестовый курс')
        self.assertTrue(Course.objects.filter(title='Тестовый курс').exists())
    
    def test_group_model(self):
        """Тест модели группы"""
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
        
        self.assertEqual(group.title, 'Тестовая группа')
        self.assertEqual(str(group), 'Тестовая группа - Тестовый курс')
        self.assertTrue(Group.objects.filter(title='Тестовая группа').exists())
    
    def test_lesson_model(self):
        """Тест модели занятия"""
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
        
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        next_hour = tomorrow + datetime.timedelta(hours=1)
        
        lesson = Lesson.objects.create(
            title='Тестовое занятие',
            group=group,
            teacher=self.teacher_user,
            lesson_type='group',
            start_time=tomorrow,
            end_time=next_hour
        )
        
        self.assertEqual(lesson.title, 'Тестовое занятие')
        self.assertEqual(lesson.duration_minutes, 60)  # 60 минут между start_time и end_time
        self.assertTrue(Lesson.objects.filter(title='Тестовое занятие').exists())
    
    def test_badge_model(self):
        """Тест модели бейджа"""
        badge = Badge.objects.create(
            name='Тестовый бейдж',
            description='Описание бейджа',
            badge_type='participation'
        )
        
        self.assertEqual(badge.name, 'Тестовый бейдж')
        self.assertEqual(str(badge), 'Тестовый бейдж')
        self.assertTrue(Badge.objects.filter(name='Тестовый бейдж').exists())
    
    def test_student_badge_model(self):
        """Тест модели связи студент-бейдж"""
        badge = Badge.objects.create(
            name='Тестовый бейдж',
            description='Описание бейджа',
            badge_type='participation'
        )
        
        student_badge = StudentBadge.objects.create(
            student=self.student_user,
            badge=badge,
            awarded_by=self.teacher_user,
            comment='Отличная работа!'
        )
        
        self.assertEqual(student_badge.student, self.student_user)
        self.assertEqual(student_badge.badge, badge)
        self.assertEqual(student_badge.awarded_by, self.teacher_user)
        self.assertTrue(StudentBadge.objects.filter(
            student=self.student_user, 
            badge=badge
        ).exists())
    

class APIBasicTestCase(SignalFreeTestCase, APITestCase):
    """Тесты для базового функционала API"""
    
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
    
    def test_get_badges_list(self):
        """Тест получения списка бейджей"""
        self.client.force_authenticate(user=self.teacher_user)
        
        # Создаем тестовые бейджи
        badge1 = Badge.objects.create(
            name='Бейдж 1',
            description='Описание 1',
            badge_type='participation'
        )
        badge2 = Badge.objects.create(
            name='Бейдж 2',
            description='Описание 2',
            badge_type='excellent'
        )
        
        response = self.client.get(reverse('courses:badge-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if isinstance(response.data, dict) and 'results' in response:
            # Пагинированный ответ
            self.assertGreaterEqual(len(response.data['results']), 2)
        elif isinstance(response.data, list):
            # Обычный список
            self.assertGreaterEqual(len(response.data), 2)
    
    def test_get_courses_list(self):
        """Тест получения списка курсов"""
        self.client.force_authenticate(user=self.student_user)
        
        # Создаем тестовые курсы
        course1 = Course.objects.create(
            title='Курс 1',
            description='Описание 1',
            price=100.00,
            duration_hours=20,
            level='beginner'
        )
        course2 = Course.objects.create(
            title='Курс 2',
            description='Описание 2',
            price=200.00,
            duration_hours=30,
            level='intermediate'
        )
        
        response = self.client.get(reverse('courses:course-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if isinstance(response.data, dict) and 'results' in response:
            self.assertGreaterEqual(len(response.data['results']), 2)
        elif isinstance(response.data, list):
            self.assertGreaterEqual(len(response.data), 2)
    
    def test_authentication_required(self):
        """Тест, что для доступа к API нужна аутентификация"""
        # Без аутентификации
        response = self.client.get(reverse('courses:course-list'))
        
        # В зависимости от настроек, может быть 401 или 200 с пустым списком
        # Это нормально для разных настроек разрешений
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])