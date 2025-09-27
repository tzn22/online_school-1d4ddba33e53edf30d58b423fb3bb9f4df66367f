from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from .models import Payment
from courses.models import Course

User = get_user_model()

class PaymentsTestCase(APITestCase):
    def setUp(self):
        # Создаем пользователей
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        self.student_user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        
        # Создаем курс
        self.course = Course.objects.create(
            title='Английский язык',
            description='Курс английского языка',
            price=Decimal('1000.00'),
            duration_hours=40,
            level='beginner'
        )
    
    def test_create_payment(self):
        """Тест создания платежа"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'student': self.student_user.id,
            'course': self.course.id,
            'amount': '1000.00',
            'currency': 'RUB',
            'payment_method': 'card',
            'description': 'Оплата курса'
        }
        
        response = self.client.post('/api/payments/payments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Payment.objects.filter(student=self.student_user).exists())
    
    def test_student_payment_access(self):
        """Тест доступа студента к своим платежам"""
        # Создаем платеж
        payment = Payment.objects.create(
            student=self.student_user,
            course=self.course,
            amount=Decimal('1000.00'),
            currency='RUB',
            status='paid',
            transaction_id='test_txn_123'
        )
        
        # Студент может видеть свой платеж
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(f'/api/payments/payments/{payment.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Другой студент не может видеть чужой платеж
        other_student = User.objects.create_user(
            username='other_student',
            email='other@test.com',
            password='testpass123',
            role='student'
        )
        self.client.force_authenticate(user=other_student)
        response = self.client.get(f'/api/payments/payments/{payment.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)