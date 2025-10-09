# ai_trainer/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import post_save, m2m_changed
from unittest.mock import patch
from .models import *  # Замените на реальные модели

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

class AITrainerModelsTestCase(SignalFreeTestCase, TestCase):
    """Тесты моделей AI Trainer"""
    
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
    
    def test_ai_trainer_model(self):
        """Тест модели AI тренера"""
        # Замените на реальную модель
        pass
    
    def test_ai_session_model(self):
        """Тест модели сессии AI"""
        # Замените на реальную модель
        pass

