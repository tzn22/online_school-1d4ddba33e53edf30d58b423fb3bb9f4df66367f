from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import StudentProfile, TeacherProfile, Lead

User = get_user_model()

class CRMTestCase(APITestCase):
    def setUp(self):
        # Создаем администратора
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        # Создаем студента
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        
        # Создаем преподавателя
        self.teacher = User.objects.create_user(
            username='teacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        
        # Создаем лид
        self.lead = Lead.objects.create(
            first_name='Иван',
            last_name='Иванов',
            email='ivan@test.com',
            phone='+79991234567',
            status='new',
            source='website'
        )
    
    def test_create_student_profile(self):
        """Тест создания профиля студента"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Профиль должен создаться автоматически при создании студента
        profile = StudentProfile.objects.filter(student=self.student)
        self.assertTrue(profile.exists())
    
    def test_create_teacher_profile(self):
        """Тест создания профиля преподавателя"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Профиль должен создаться автоматически при создании преподавателя
        profile = TeacherProfile.objects.filter(teacher=self.teacher)
        self.assertTrue(profile.exists())
    
    def test_lead_crud(self):
        """Тест CRUD операций с лидами"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Создание лида
        data = {
            'first_name': 'Петр',
            'last_name': 'Петров',
            'email': 'petr@test.com',
            'phone': '+79997654321',
            'status': 'new',
            'source': 'social_media'
        }
        
        response = self.client.post('/api/crm/leads/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Lead.objects.filter(email='petr@test.com').exists())
        
        # Получение списка лидов
        response = self.client.get('/api/crm/leads/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_lead_conversion(self):
        """Тест конвертации лида в студента"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(f'/api/crm/leads/{self.lead.id}/convert/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, 'converted')
        
        # Проверяем, что студент был создан
        student = User.objects.filter(email=self.lead.email, role='student')
        self.assertTrue(student.exists())