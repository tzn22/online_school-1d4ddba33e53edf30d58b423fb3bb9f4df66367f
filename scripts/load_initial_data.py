#!/usr/bin/env python
"""
Скрипт для загрузки начальных данных в базу данных
"""

import os
import django
from django.core.management import execute_from_command_line
import json

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from courses.models import Course
from notifications.models import NotificationTemplate

User = get_user_model()

def load_initial_data():
    """Загрузка начальных данных"""
    print("Загрузка начальных данных...")
    
    # Создание администратора
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin',
            first_name='Администратор',
            last_name='Системы'
        )
        print(f"Создан администратор: {admin.username}")
    
    # Создание тестовых курсов
    courses_data = [
        {
            'title': 'Английский для начинающих',
            'description': 'Базовый курс английского языка для новичков',
            'price': 1500.00,
            'duration_hours': 40,
            'level': 'beginner',
            'language': 'Английский',
            'is_active': True
        },
        {
            'title': 'Английский для среднего уровня',
            'description': 'Курс для тех, кто уже знает основы английского',
            'price': 2000.00,
            'duration_hours': 50,
            'level': 'intermediate',
            'language': 'Английский',
            'is_active': True
        },
        {
            'title': 'Бизнес английский',
            'description': 'Английский для делового общения',
            'price': 2500.00,
            'duration_hours': 30,
            'level': 'advanced',
            'language': 'Английский',
            'is_active': True
        }
    ]
    
    for course_data in courses_data:
        course, created = Course.objects.get_or_create(
            title=course_data['title'],
            defaults=course_data
        )
        if created:
            print(f"Создан курс: {course.title}")
    
    # Создание шаблонов уведомлений
    templates_data = [
        {
            'name': 'lesson_reminder',
            'title_template': 'Напоминание о занятии: {{ lesson.title }}',
            'message_template': 'Занятие "{{ lesson.title }}" начнется {{ lesson.start_time|date:"d.m.Y H:i" }}',
            'notification_type': 'lesson',
            'channels': '["email", "push", "telegram", "whatsapp"]',
            'is_active': True
        },
        {
            'name': 'payment_reminder',
            'title_template': 'Напоминание об оплате курса',
            'message_template': 'Пожалуйста, не забудьте оплатить курс "{{ course.title }}"',
            'notification_type': 'payment',
            'channels': '["email", "push", "telegram", "whatsapp"]',
            'is_active': True
        },
        {
            'name': 'homework_deadline',
            'title_template': 'Срок сдачи домашнего задания',
            'message_template': 'Срок сдачи ДЗ "{{ homework.title }}" истекает {{ homework.due_date|date:"d.m.Y" }}',
            'notification_type': 'homework',
            'channels': '["email", "push", "telegram", "whatsapp"]',
            'is_active': True
        }
    ]
    
    for template_data in templates_data:
        template, created = NotificationTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults=template_data
        )
        if created:
            print(f"Создан шаблон уведомления: {template.name}")
    
    print("Начальные данные загружены!")

if __name__ == '__main__':
    load_initial_data()