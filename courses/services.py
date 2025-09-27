# courses/services.py
import requests
import jwt
import time
from django.conf import settings
from django.utils import timezone
from .models import Lesson, VideoLesson, MeetingParticipant

class ZoomService:
    """Сервис для работы с Zoom API"""
    
    @staticmethod
    def get_access_token():
        """Получение токена для Zoom API (JWT)"""
        payload = {
            'iss': settings.ZOOM_API_KEY,
            'exp': int(round(time.time())) + 3600  # 1 hour
        }
        token = jwt.encode(payload, settings.ZOOM_API_SECRET, algorithm='HS256')
        return token
    
    @staticmethod
    def create_meeting(lesson):
        """Создание Zoom встречи"""
        if not all([settings.ZOOM_API_KEY, settings.ZOOM_API_SECRET]):
            # Тестовые данные для разработки
            return {
                'id': f'test_{lesson.id}',
                'join_url': f'https://zoom.us/j/test_{lesson.id}',
                'start_url': f'https://zoom.us/s/test_{lesson.id}',
                'password': '123456',
                'success': True
            }
        
        headers = {
            'Authorization': f'Bearer {ZoomService.get_access_token()}',
            'Content-Type': 'application/json'
        }
        
        meeting_data = {
            'topic': f'Занятие: {lesson.title}',
            'type': 2,  # Scheduled meeting
            'start_time': lesson.start_time.isoformat(),
            'duration': lesson.duration_minutes,
            'timezone': 'Europe/Moscow',
            'settings': {
                'host_video': True,
                'participant_video': True,
                'join_before_host': True,
                'mute_upon_entry': False,
                'waiting_room': False
            }
        }
        
        response = requests.post(
            f'https://api.zoom.us/v2/users/{settings.ZOOM_USER_ID}/meetings',
            headers=headers,
            json=meeting_data
        )
        
        if response.status_code == 201:
            data = response.json()
            return {
                'id': data.get('id'),
                'join_url': data.get('join_url'),
                'start_url': data.get('start_url'),
                'password': data.get('password', ''),
                'success': True
            }
        else:
            return {'success': False, 'error': response.text}
    
    @staticmethod
    def start_meeting(meeting_id):
        """Начать Zoom встречу"""
        # В реальности - запуск встречи через API
        return True
    
    @staticmethod
    def end_meeting(meeting_id):
        """Завершить Zoom встречу"""
        # В реальности - завершение встречи через API
        return True

class VideoLessonService:
    """Сервис для работы с видеоуроками"""
    
    @staticmethod
    def create_video_lesson(lesson):
        """Создание видеоурока с Zoom встречей"""
        # Создаем Zoom встречу
        meeting_data = ZoomService.create_meeting(lesson)
        
        if not meeting_data['success']:
            raise Exception(f"Не удалось создать Zoom встречу: {meeting_data.get('error')}")
        
        # Создаем запись видеоурока
        video_lesson = VideoLesson.objects.create(
            lesson=lesson,
            zoom_meeting_id=meeting_data['id'],
            zoom_join_url=meeting_data['join_url'],
            zoom_start_url=meeting_data['start_url'],
            meeting_password=meeting_data['password']
        )
        
        # Добавляем участников
        VideoLessonService.add_participants(lesson)
        
        return video_lesson
    
    @staticmethod
    def add_participants(lesson):
        """Добавление участников к занятию"""
        if lesson.lesson_type == 'group' and lesson.group:
            students = lesson.group.students.all()
        elif lesson.lesson_type == 'individual' and lesson.student:
            students = [lesson.student]
        else:
            students = []
        
        for student in students:
            MeetingParticipant.objects.get_or_create(
                lesson=lesson,
                user=student,
                defaults={
                    'role': 'participant',
                    'joined_at': lesson.start_time
                }
            )
    
    @staticmethod
    def start_lesson(lesson):
        """Начать занятие"""
        # Отмечаем участников как присутствующих
        participants = MeetingParticipant.objects.filter(lesson=lesson)
        for participant in participants:
            participant.joined_at = timezone.now()
            participant.is_present = True
            participant.save()
        
        # Отправляем уведомления
        VideoLessonService.send_start_notifications(lesson)
    
    @staticmethod
    def end_lesson(lesson):
        """Завершить занятие"""
        # Обновляем статус участников
        participants = MeetingParticipant.objects.filter(lesson=lesson, is_present=True)
        for participant in participants:
            participant.left_at = timezone.now()
            participant.duration = participant.left_at - participant.joined_at
            participant.is_present = False
            participant.save()
        
        # Отмечаем занятие как завершенное
        lesson.is_completed = True
        lesson.save()
    
    @staticmethod
    def send_start_notifications(lesson):
        """Отправка уведомлений о начале занятия"""
        from notifications.services import NotificationService
        
        if lesson.lesson_type == 'group' and lesson.group:
            participants = lesson.group.students.all()
        elif lesson.lesson_type == 'individual' and lesson.student:
            participants = [lesson.student]
        else:
            participants = []
        
        for participant in participants:
            NotificationService.send_notification(
                user=participant,
                title=f'Начало занятия: {lesson.title}',
                message=f'Занятие "{lesson.title}" начинается. Присоединяйтесь по ссылке.',
                notification_type='lesson',
                channels=['email', 'in_app', 'push']
            )