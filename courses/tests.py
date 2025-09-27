from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Course, Group, Lesson, Attendance, Badge, StudentBadge, StudentProgress, TestResult, VideoLesson, LessonRecording, MeetingParticipant

User = get_user_model()

class CoursesTestCase(APITestCase):
    def setUp(self):
        # Создаем пользователей
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
        
        # Создаем курс
        self.course = Course.objects.create(
            title='Английский для начинающих',
            description='Базовый курс английского языка',
            price=1000.00,
            duration_hours=40,
            level='beginner'
        )
        
        # Создаем группу
        self.group = Group.objects.create(
            title='Группа 1',
            course=self.course,
            teacher=self.teacher_user,
            start_date='2024-01-01',
            end_date='2024-06-01'
        )
        self.group.students.add(self.student_user)
    
    def test_create_course(self):
        """Тест создания курса"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'title': 'Немецкий язык',
            'description': 'Курс немецкого языка',
            'price': 1500.00,
            'duration_hours': 30,
            'level': 'beginner'
        }
        
        response = self.client.post('/api/courses/courses/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Course.objects.filter(title='Немецкий язык').exists())
    
    def test_get_courses_list(self):
        """Тест получения списка курсов"""
        self.client.force_authenticate(user=self.student_user)
        
        response = self.client.get('/api/courses/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_lesson(self):
        """Тест создания занятия"""
        self.client.force_authenticate(user=self.teacher_user)
        
        import datetime
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        next_day = tomorrow + datetime.timedelta(hours=1)
        
        data = {
            'group': self.group.id,
            'teacher': self.teacher_user.id,
            'title': 'Урок 1',
            'description': 'Введение в курс',
            'lesson_type': 'group',
            'start_time': tomorrow.isoformat(),
            'end_time': next_day.isoformat()
        }
        
        response = self.client.post('/api/courses/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Lesson.objects.filter(title='Урок 1').exists())

class BadgesTestCase(APITestCase):
    def setUp(self):
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
        
        self.badge = Badge.objects.create(
            name='Отличник',
            description='Отличные результаты',
            badge_type='excellent'
        )
    
    def test_create_badge(self):
        """Тест создания бейджа"""
        self.client.force_authenticate(user=self.teacher_user)
        
        data = {
            'name': 'Участник',
            'description': 'Активное участие',
            'badge_type': 'participation'
        }
        
        response = self.client.post('/api/courses/badges/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Badge.objects.filter(name='Участник').exists())
    
    def test_award_badge_to_student(self):
        """Тест выдачи бейджа студенту"""
        self.client.force_authenticate(user=self.teacher_user)
        
        data = {
            'student_id': self.student_user.id,
            'badge_id': self.badge.id,
            'comment': 'Отличная работа!'
        }
        
        response = self.client.post('/api/courses/students/1/badges/award/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(StudentBadge.objects.filter(student=self.student_user, badge=self.badge).exists())

class VideoLessonsTestCase(APITestCase):
    def setUp(self):
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
        
        self.course = Course.objects.create(
            title='Английский для начинающих',
            description='Базовый курс',
            price=1000.00,
            level='beginner'
        )
        
        self.lesson = Lesson.objects.create(
            title='Урок 1',
            lesson_type='group',
            teacher=self.teacher_user,
            start_time='2024-01-01T10:00:00Z',
            end_time='2024-01-01T11:00:00Z'
        )
    
    def test_create_video_lesson(self):
        """Тест создания видеоурока"""
        self.client.force_authenticate(user=self.teacher_user)
        
        data = {
            'lesson_id': self.lesson.id
        }
        
        response = self.client.post('/api/courses/video-lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(VideoLesson.objects.filter(lesson=self.lesson).exists())
    
    def test_start_zoom_meeting(self):
        """Тест запуска Zoom встречи"""
        video_lesson = VideoLesson.objects.create(
            lesson=self.lesson,
            zoom_meeting_id='test123',
            zoom_join_url='https://zoom.us/j/test123',
            zoom_start_url='https://zoom.us/s/test123'
        )
        
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.post(f'/api/courses/lessons/{self.lesson.id}/start-meeting/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('meeting_data', response.data)