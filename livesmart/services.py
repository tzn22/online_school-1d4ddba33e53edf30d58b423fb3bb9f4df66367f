# livesmart/services.py
from datetime import timedelta
import requests
import json
import uuid
from django.conf import settings
from django.utils import timezone
from .models import LiveSmartRoom, LiveSmartParticipant, LiveSmartRecording, LiveSmartSettings
from accounts.models import User
from courses.models import Lesson
import logging

logger = logging.getLogger(__name__)

class LiveSmartService:
    """Сервис для работы с LiveSmart API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'LIVESMART_API_KEY', '')
        self.api_secret = getattr(settings, 'LIVESMART_API_SECRET', '')
        self.base_url = getattr(settings, 'LIVESMART_API_URL', 'https://api.livesmart.com/v1')
        self.return_url = getattr(settings, 'LIVESMART_RETURN_URL', 'https://fluencyclub.fun/meeting-complete/')
    
    def get_auth_headers(self):
        """Получение заголовков аутентификации"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    def create_room(self, lesson, host_user=None):
        """Создание комнаты LiveSmart для занятия"""
        try:
            # Генерируем уникальный ID комнаты
            room_id = str(uuid.uuid4())
            
            # Получаем настройки пользователя
            if host_user:
                settings_obj, created = LiveSmartSettings.objects.get_or_create(user=host_user)
                max_participants = settings_obj.max_participants
                is_recording_enabled = settings_obj.is_recording_enabled
            else:
                max_participants = 50
                is_recording_enabled = False
            
            # Создаем данные комнаты
            room_data = {
                'name': f'Занятие: {lesson.title}',
                'description': lesson.description or f'Видеоурок по курсу {lesson.group.course.title if lesson.group else "индивидуальный"}',
                'start_time': lesson.start_time.isoformat() if lesson.start_time else None,
                'duration': lesson.duration_minutes,
                'max_participants': max_participants,
                'enable_recording': is_recording_enabled,
                'enable_chat': True,
                'enable_screen_sharing': True,
                'enable_whiteboard': True,
                'enable_polls': True,
                'password': self.generate_room_password(),
                'metadata': {
                    'lesson_id': lesson.id,
                    'course_title': lesson.group.course.title if lesson.group and lesson.group.course else '',
                    'teacher': lesson.teacher.get_full_name() if lesson.teacher else '',
                    'lesson_type': lesson.lesson_type,
                }
            }
            
            # Если LiveSmart API настроен, создаем комнату через API
            if self.api_key and self.api_secret:
                response = requests.post(
                    f'{self.base_url}/rooms',
                    headers=self.get_auth_headers(),
                    json=room_data
                )
                
                if response.status_code == 201:
                    api_response = response.json()
                    room_id = api_response.get('id', room_id)
                    join_url = api_response.get('join_url', '')
                    host_url = api_response.get('host_url', '')
                    room_password = api_response.get('password', room_data['password'])
                else:
                    logger.error(f"Ошибка создания комнаты в LiveSmart: {response.text}")
                    join_url = ''
                    host_url = ''
                    room_password = room_data['password']
            else:
                # Если API не настроен, создаем тестовые данные
                join_url = f'https://livesmart.com/join/{room_id}'
                host_url = f'https://livesmart.com/host/{room_id}'
                room_password = room_data['password']
            
            # Создаем комнату в нашей системе
            livesmart_room = LiveSmartRoom.objects.create(
                lesson=lesson,
                room_id=room_id,
                room_name=room_data['name'],
                join_url=join_url,
                host_url=host_url,
                room_password=room_password,
                max_participants=max_participants,
                is_recording_enabled=is_recording_enabled,
                status='scheduled'
            )
            
            # Добавляем участников
            self.add_participants_to_room(livesmart_room, lesson)
            
            logger.info(f"Создана комната LiveSmart: {livesmart_room.room_name}")
            
            return {
                'success': True,
                'room': livesmart_room,
                'join_url': join_url,
                'host_url': host_url,
                'room_password': room_password,
                'room_id': room_id
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания комнаты LiveSmart: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_participants_to_room(self, room, lesson):
        """Добавление участников в комнату LiveSmart"""
        try:
            participants = []
            
            # Добавляем преподавателя как хоста
            LiveSmartParticipant.objects.create(
                room=room,
                user=lesson.teacher,
                role='host',
                participant_id=f"host_{lesson.teacher.id}"
            )
            participants.append(lesson.teacher)
            
            # Добавляем студентов
            if lesson.lesson_type == 'group' and lesson.group:
                students = lesson.group.students.all()
            elif lesson.lesson_type == 'individual' and lesson.student:
                students = [lesson.student]
            else:
                students = []
            
            for student in students:
                if student not in participants:
                    LiveSmartParticipant.objects.create(
                        room=room,
                        user=student,
                        role='participant',
                        participant_id=f"participant_{student.id}"
                    )
                    participants.append(student)
            
            logger.info(f"Добавлено {len(participants)} участников в комнату {room.room_name}")
            
            return participants
            
        except Exception as e:
            logger.error(f"Ошибка добавления участников в комнату: {str(e)}")
            return []
    
    def start_room(self, room):
        """Начало встречи в комнате LiveSmart"""
        try:
            # Обновляем статус комнаты
            room.status = 'active'
            room.started_at = timezone.now()
            room.save()
            
            # Обновляем статус участников
            participants = LiveSmartParticipant.objects.filter(room=room)
            for participant in participants:
                if participant.role == 'host':
                    participant.is_present = True
                    participant.joined_at = timezone.now()
                    participant.save()
            
            # Если LiveSmart API настроен, запускаем встречу через API
            if self.api_key and self.api_secret:
                response = requests.post(
                    f'{self.base_url}/rooms/{room.room_id}/start',
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    logger.info(f"Комната {room.room_name} запущена через LiveSmart API")
                else:
                    logger.warning(f"Ошибка запуска комнаты через LiveSmart API: {response.text}")
            
            logger.info(f"Комната {room.room_name} активирована")
            
            return {
                'success': True,
                'room': room,
                'message': 'Комната активирована'
            }
            
        except Exception as e:
            logger.error(f"Ошибка активации комнаты: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def end_room(self, room):
        """Завершение встречи в комнате LiveSmart"""
        try:
            # Обновляем статус комнаты
            room.status = 'completed'
            room.ended_at = timezone.now()
            room.save()
            
            # Обновляем статус участников
            participants = LiveSmartParticipant.objects.filter(
                room=room,
                is_present=True
            )
            for participant in participants:
                participant.left_at = timezone.now()
                if participant.joined_at:
                    duration = participant.left_at - participant.joined_at
                    participant.duration = duration
                participant.is_present = False
                participant.save()
            
            # Если LiveSmart API настроен, завершаем встречу через API
            if self.api_key and self.api_secret:
                response = requests.post(
                    f'{self.base_url}/rooms/{room.room_id}/end',
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    logger.info(f"Комната {room.room_name} завершена через LiveSmart API")
                else:
                    logger.warning(f"Ошибка завершения комнаты через LiveSmart API: {response.text}")
            
            logger.info(f"Комната {room.room_name} завершена")
            
            return {
                'success': True,
                'room': room,
                'message': 'Комната завершена',
                'participants_count': participants.count()
            }
            
        except Exception as e:
            logger.error(f"Ошибка завершения комнаты: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def join_room(self, room, user):
        """Присоединение пользователя к комнате LiveSmart"""
        try:
            # Проверяем права доступа
            if not self.can_join_room(room, user):
                return {
                    'success': False,
                    'error': 'Нет прав для присоединения к этой комнате'
                }
            
            # Создаем или обновляем запись участника
            participant, created = LiveSmartParticipant.objects.get_or_create(
                room=room,
                user=user,
                defaults={
                    'role': 'participant' if user.is_student else 'host',
                    'participant_id': f"participant_{user.id}",
                    'joined_at': timezone.now(),
                    'is_present': True
                }
            )
            
            if not created:
                participant.joined_at = timezone.now()
                participant.is_present = True
                participant.save()
            
            # Если LiveSmart API настроен, получаем ссылку через API
            if self.api_key and self.api_secret:
                response = requests.post(
                    f'{self.base_url}/rooms/{room.room_id}/join',
                    headers=self.get_auth_headers(),
                    json={
                        'user_id': user.id,
                        'username': user.get_full_name() or user.username,
                        'role': participant.role
                    }
                )
                
                if response.status_code == 200:
                    api_response = response.json()
                    join_url = api_response.get('join_url', room.join_url)
                else:
                    join_url = room.join_url
                    logger.warning(f"Ошибка получения ссылки через LiveSmart API: {response.text}")
            else:
                join_url = room.join_url
            
            logger.info(f"Пользователь {user.username} присоединился к комнате {room.room_name}")
            
            return {
                'success': True,
                'join_url': join_url,
                'room_password': room.room_password,
                'participant': participant
            }
            
        except Exception as e:
            logger.error(f"Ошибка присоединения к комнате: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def can_join_room(self, room, user):
        """Проверка прав доступа к комнате"""
        lesson = room.lesson
        
        # Администратор может всё
        if user.is_admin:
            return True
        
        # Преподаватель может присоединяться к своим занятиям
        if user.is_teacher and lesson.teacher == user:
            return True
        
        # Студент может присоединяться к своим занятиям
        if user.is_student:
            if lesson.lesson_type == 'group' and lesson.group:
                return user in lesson.group.students.all()
            elif lesson.lesson_type == 'individual' and lesson.student:
                return user == lesson.student
        
        # Родитель может присоединяться к занятиям своих детей
        if user.is_parent:
            children = user.children.all()
            if lesson.lesson_type == 'group' and lesson.group:
                for child in children:
                    if child in lesson.group.students.all():
                        return True
            elif lesson.lesson_type == 'individual':
                for child in children:
                    if child == lesson.student:
                        return True
        
        return False
    
    def generate_room_password(self):
        """Генерация пароля для комнаты"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    def get_room_info(self, room):
        """Получение информации о комнате"""
        try:
            # Если LiveSmart API настроен, получаем информацию через API
            if self.api_key and self.api_secret:
                response = requests.get(
                    f'{self.base_url}/rooms/{room.room_id}',
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Ошибка получения информации о комнате через LiveSmart API: {response.text}")
            
            # Возвращаем информацию из нашей системы
            return {
                'id': room.room_id,
                'name': room.room_name,
                'status': room.status,
                'participants': [
                    {
                        'id': participant.participant_id,
                        'username': participant.user.get_full_name() or participant.user.username,
                        'role': participant.role,
                        'is_present': participant.is_present,
                        'joined_at': participant.joined_at.isoformat() if participant.joined_at else None,
                        'left_at': participant.left_at.isoformat() if participant.left_at else None,
                    }
                    for participant in room.participants.all()
                ],
                'recording_enabled': room.is_recording_enabled,
                'max_participants': room.max_participants,
                'created_at': room.created_at.isoformat(),
                'started_at': room.started_at.isoformat() if room.started_at else None,
                'ended_at': room.ended_at.isoformat() if room.ended_at else None,
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о комнате: {str(e)}")
            return None
    
    def create_recording(self, room, recording_data):
        """Создание записи комнаты"""
        try:
            recording = LiveSmartRecording.objects.create(
                recording_id=recording_data.get('id', str(uuid.uuid4())),
                room=room,
                title=recording_data.get('title', f'Запись занятия: {room.lesson.title}'),
                description=recording_data.get('description', ''),
                file_url=recording_data.get('file_url', ''),
                file_size=recording_data.get('file_size', 0),
                duration=recording_data.get('duration', timedelta(minutes=60)),
                is_public=recording_data.get('is_public', False),
                uploaded_by=room.lesson.teacher,
                published_at=timezone.now() if recording_data.get('is_public', False) else None
            )
            
            logger.info(f"Создана запись: {recording.title}")
            
            return recording
            
        except Exception as e:
            logger.error(f"Ошибка создания записи: {str(e)}")
            return None

# Глобальный экземпляр сервиса
livesmart_service = LiveSmartService()