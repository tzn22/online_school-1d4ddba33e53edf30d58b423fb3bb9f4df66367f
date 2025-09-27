from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Feedback

User = get_user_model()

class FeedbackTestCase(APITestCase):
    def setUp(self):
        # Создаем пользователей
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        self.teacher = User.objects.create_user(
            username='teacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        
        # Создаем отзыв
        self.feedback = Feedback.objects.create(
            student=self.student,
            teacher=self.teacher,
            feedback_type='teacher',
            title='Отличный преподаватель',
            content='Очень хороший преподаватель, все понятно объясняет',
            rating=5
        )
    
    def test_create_feedback(self):
        """Тест создания отзыва"""
        self.client.force_authenticate(user=self.student)
        
        data = {
            'teacher': self.teacher.id,
            'feedback_type': 'teacher',
            'title': 'Хороший урок',
            'content': 'Урок был очень полезным',
            'rating': 4
        }
        
        response = self.client.post('/api/feedback/feedback/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Feedback.objects.filter(title='Хороший урок').exists())
    
    def test_get_feedback_list(self):
        """Тест получения списка отзывов"""
        self.client.force_authenticate(user=self.student)
        
        response = self.client.get('/api/feedback/feedback/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_feedback_permissions(self):
        """Тест прав доступа к отзывам"""
        # Другой студент не может видеть чужие отзывы
        other_student = User.objects.create_user(
            username='other_student',
            email='other@test.com',
            password='testpass123',
            role='student'
        )
        self.client.force_authenticate(user=other_student)
        
        response = self.client.get(f'/api/feedback/feedback/{self.feedback.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)