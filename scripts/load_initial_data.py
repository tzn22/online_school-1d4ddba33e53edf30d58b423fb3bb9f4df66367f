#!/usr/bin/env python
"""
Скрипт для загрузки тестовых данных в проект
"""

import os
import django
from django.core.management import execute_from_command_line
import json
from datetime import datetime, timedelta
from django.utils import timezone

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, Group, Lesson
from payments.models import Payment
from accounts.models import User

User = get_user_model()

def load_initial_data():
    """Загрузка начальных тестовых данных"""
    print("Загрузка начальных тестовых данных...")
    
    # Создание администратора
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@fluencyclub.fun',
            password='admin',
            role='admin',
            first_name='Администратор',
            last_name='Системы'
        )
        print(f"✅ Создан администратор: {admin.username}")
    
    # Создание преподавателей
    teachers_data = [
        {
            'username': 'teacher1',
            'email': 'teacher1@fluencyclub.fun',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Иван',
            'last_name': 'Иванов',
        },
        {
            'username': 'teacher2',
            'email': 'teacher2@fluencyclub.fun',
            'password': 'teacher123',
            'role': 'teacher',
            'first_name': 'Мария',
            'last_name': 'Петрова',
        }
    ]
    
    for teacher_data in teachers:
        if not User.objects.filter(username=teacher_data['username']).exists():
            teacher = User.objects.create_user(**teacher_data)
            print(f"✅ Создан преподаватель: {teacher.username}")
    
    # Создание студентов
    students_data = [
        {
            'username': 'student1',
            'email': 'student1@fluencyclub.fun',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Алексей',
            'last_name': 'Смирнов',
            'has_studied_language': False
        },
        {
            'username': 'student2',
            'email': 'student2@fluencyclub.fun',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Елена',
            'last_name': 'Козлова',
            'has_studied_language': True
        },
        {
            'username': 'student3',
            'email': 'student3@fluencyclub.fun',
            'password': 'student123',
            'role': 'student',
            'first_name': 'Дмитрий',
            'last_name': 'Волков',
            'has_studied_language': True
        }
    ]
    
    for student_data in students:
        if not User.objects.filter(username=student_data['username']).exists():
            student = User.objects.create_user(**student_data)
            print(f"✅ Создан студент: {student.username}")
    
    # Создание курсов (если их нет)
    course_data = [
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
    
    for course_data in courses:
        course, created = Course.objects.get_or_create(
            title=course_data['title'],
            defaults=course_data
        )
        if created:
            print(f"✅ Создан курс: {course.title}")
    
    # Создание групп
    teachers = User.objects.filter(role='teacher')
    students = User.objects.filter(role='student')
    
    if teachers.exists() and students.exists():
        courses = Course.objects.all()
        
        for i, course in enumerate(courses):
            teacher = teachers[i % len(teachers)]
            
            group_data = {
                'title': f'Группа {course.get_level_display()} {i+1}',
                'course': course,
                'teacher': teacher,
                'start_date': timezone.now().date(),
                'end_date': (timezone.now() + timedelta(days=90)).date(),
                'is_active': True
            }
            
            group, created = Group.objects.get_or_create(
                title=group_data['title'],
                defaults=group_data
            )
            
            if created:
                # Добавляем студентов в группу
                group_students = list(students[:3])  # Первые 3 студента
                group.students.set(group_students)
                print(f"✅ Создана группа: {group.title} с {len(group_students)} студентами")
    
    # Создание занятий
    groups = Group.objects.filter(is_active=True)
    
    for group in groups:
        # Создаем несколько занятий
        for i in range(3):
            start_time = timezone.now() + timedelta(days=i*7, hours=10)
            end_time = start_time + timedelta(hours=1)
            
            lesson_data = {
                'group': group,
                'teacher': group.teacher,
                'title': f'Занятие {i+1}: {group.course.title}',
                'description': f'Описание занятия {i+1} курса {group.course.title}',
                'lesson_type': 'group',
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': 60
            }
            
            lesson, created = Lesson.objects.get_or_create(
                title=lesson_data['title'],
                start_time=lesson_data['start_time'],
                defaults=lesson_data
            )
            
            if created:
                print(f"✅ Создано занятие: {lesson.title}")
    
    # Создание платежей
    if students.exists() and courses.exists():
        for i, student in enumerate(students[:2]):  # Первые 2 студента
            course = courses[i % len(courses)]
            
            payment_data = {
                'student': student,
                'course': course,
                'amount': course.price,
                'currency': 'RUB',
                'status': 'paid',
                'payment_method': 'card',
                'description': f'Оплата курса: {course.title}'
            }
            
            payment, created = Payment.objects.get_or_create(
                student=student,
                course=course,
                defaults=payment_data
            )
            
            if created:
                payment.paid_at = timezone.now()
                payment.save()
                print(f"✅ Создан платеж: {student.username} - {course.title}")
    
    print("🎉 Все тестовые данные загружены!")

if __name__ == '__main__':
    load_initial_data()