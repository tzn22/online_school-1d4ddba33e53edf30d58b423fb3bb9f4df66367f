# livesmart/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db import models
from django.shortcuts import get_object_or_404
from .models import LiveSmartRoom, LiveSmartParticipant, LiveSmartRecording, LiveSmartSettings
from .serializers import (
    LiveSmartRoomSerializer,
    LiveSmartParticipantSerializer,
    LiveSmartRecordingSerializer,
    LiveSmartSettingsSerializer
)
from .services import LiveSmartService
from accounts.models import User
from courses.models import Lesson
from .permissions import IsRoomParticipant, IsRoomHost, IsRecordingOwner, IsSettingsOwner

# === API для комнат LiveSmart ===

class LiveSmartRoomListView(generics.ListAPIView):
    """Список комнат LiveSmart"""
    serializer_class = LiveSmartRoomSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'lesson__lesson_type', 'created_at']
    search_fields = ['room_name', 'lesson__title']
    ordering_fields = ['created_at', 'started_at', 'ended_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return LiveSmartRoom.objects.all()
        elif user.is_teacher:
            return LiveSmartRoom.objects.filter(lesson__teacher=user)
        elif user.is_student:
            return LiveSmartRoom.objects.filter(
                models.Q(lesson__group__students=user) |
                models.Q(lesson__student=user)
            )
        elif user.is_parent:
            children = user.children.all()
            return LiveSmartRoom.objects.filter(
                models.Q(lesson__group__students__in=children) |
                models.Q(lesson__student__in=children)
            )
        return LiveSmartRoom.objects.none()

class LiveSmartRoomDetailView(generics.RetrieveAPIView):
    """Детали комнаты LiveSmart"""
    queryset = LiveSmartRoom.objects.all()
    serializer_class = LiveSmartRoomSerializer
    permission_classes = [IsAuthenticated, IsRoomParticipant]

class LiveSmartRoomCreateView(generics.CreateAPIView):
    """Создание комнаты LiveSmart"""
    serializer_class = LiveSmartRoomSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class LiveSmartRoomUpdateView(generics.UpdateAPIView):
    """Обновление комнаты LiveSmart"""
    queryset = LiveSmartRoom.objects.all()
    serializer_class = LiveSmartRoomSerializer
    permission_classes = [IsAuthenticated, IsRoomHost]

# === API для участников ===

class LiveSmartParticipantListView(generics.ListAPIView):
    """Список участников комнаты"""
    serializer_class = LiveSmartParticipantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['role', 'is_present', 'joined_at']
    ordering_fields = ['joined_at', 'left_at', 'duration']
    ordering = ['role', 'joined_at']
    
    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        room = get_object_or_404(LiveSmartRoom, id=room_id)
        
        user = self.request.user
        if user.is_admin or room.lesson.teacher == user:
            return LiveSmartParticipant.objects.filter(room=room)
        elif user.is_student or user.is_parent:
            return LiveSmartParticipant.objects.filter(room=room, user=user)
        
        return LiveSmartParticipant.objects.none()

class LiveSmartParticipantDetailView(generics.RetrieveAPIView):
    """Детали участника комнаты"""
    queryset = LiveSmartParticipant.objects.all()
    serializer_class = LiveSmartParticipantSerializer
    permission_classes = [IsAuthenticated, IsRoomParticipant]

# === API для записей ===

class LiveSmartRecordingListView(generics.ListAPIView):
    """Список записей LiveSmart"""
    serializer_class = LiveSmartRecordingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public', 'uploaded_by', 'created_at']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'published_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return LiveSmartRecording.objects.all()
        elif user.is_teacher:
            return LiveSmartRecording.objects.filter(
                models.Q(is_public=True) |
                models.Q(room__lesson__teacher=user) |
                models.Q(uploaded_by=user)
            )
        elif user.is_student:
            return LiveSmartRecording.objects.filter(
                models.Q(is_public=True) |
                models.Q(room__lesson__group__students=user) |
                models.Q(room__lesson__student=user)
            )
        elif user.is_parent:
            children = user.children.all()
            return LiveSmartRecording.objects.filter(
                models.Q(is_public=True) |
                models.Q(room__lesson__group__students__in=children) |
                models.Q(room__lesson__student__in=children)
            )
        return LiveSmartRecording.objects.filter(is_public=True)

class LiveSmartRecordingDetailView(generics.RetrieveAPIView):
    """Детали записи LiveSmart"""
    queryset = LiveSmartRecording.objects.all()
    serializer_class = LiveSmartRecordingSerializer
    permission_classes = [IsAuthenticated, IsRecordingOwner]

class LiveSmartRecordingCreateView(generics.CreateAPIView):
    """Создание записи LiveSmart"""
    serializer_class = LiveSmartRecordingSerializer
    permission_classes = [IsAuthenticated, IsRoomHost]
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class LiveSmartRecordingUpdateView(generics.UpdateAPIView):
    """Обновление записи LiveSmart"""
    queryset = LiveSmartRecording.objects.all()
    serializer_class = LiveSmartRecordingSerializer
    permission_classes = [IsAuthenticated, IsRecordingOwner]

# === API для настроек ===

class LiveSmartSettingsView(generics.RetrieveUpdateAPIView):
    """Настройки LiveSmart пользователя"""
    serializer_class = LiveSmartSettingsSerializer
    permission_classes = [IsAuthenticated, IsSettingsOwner]
    
    def get_object(self):
        settings_obj, created = LiveSmartSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings_obj

# === API эндпоинты для управления встречами ===

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsRoomHost])
def create_livesmart_room(request):
    """Создание комнаты LiveSmart для занятия"""
    lesson_id = request.data.get('lesson_id')
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        # Проверка прав доступа
        if not (request.user.is_admin or lesson.teacher == request.user):
            return Response(
                {'error': 'Нет прав для создания комнаты для этого занятия'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Создаем комнату через сервис
        result = LiveSmartService().create_room(lesson, request.user)
        
        if result['success']:
            serializer = LiveSmartRoomSerializer(result['room'])
            return Response({
                'message': 'Комната LiveSmart успешно создана',
                'room': serializer.data,
                'join_url': result['join_url'],
                'host_url': result['host_url'],
                'room_password': result['room_password']
            })
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Занятие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsRoomHost])
def start_livesmart_room(request, room_id):
    """Начало встречи в комнате LiveSmart"""
    try:
        room = LiveSmartRoom.objects.get(id=room_id)
        
        # Проверка прав доступа
        if not (request.user.is_admin or room.lesson.teacher == request.user):
            return Response(
                {'error': 'Нет прав для начала этой встречи'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Начинаем встречу через сервис
        result = LiveSmartService().start_room(room)
        
        if result['success']:
            serializer = LiveSmartRoomSerializer(room)
            return Response({
                'message': 'Встреча начата',
                'room': serializer.data
            })
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except LiveSmartRoom.DoesNotExist:
        return Response(
            {'error': 'Комната не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsRoomHost])
def end_livesmart_room(request, room_id):
    """Завершение встречи в комнате LiveSmart"""
    try:
        room = LiveSmartRoom.objects.get(id=room_id)
        
        # Проверка прав доступа
        if not (request.user.is_admin or room.lesson.teacher == request.user):
            return Response(
                {'error': 'Нет прав для завершения этой встречи'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Завершаем встречу через сервис
        result = LiveSmartService().end_room(room)
        
        if result['success']:
            serializer = LiveSmartRoomSerializer(room)
            return Response({
                'message': 'Встреча завершена',
                'room': serializer.data,
                'participants_count': result['participants_count']
            })
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except LiveSmartRoom.DoesNotExist:
        return Response(
            {'error': 'Комната не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_livesmart_room(request, room_id):
    """Присоединение к комнате LiveSmart"""
    try:
        room = LiveSmartRoom.objects.get(id=room_id)
        
        # Присоединяемся через сервис
        result = LiveSmartService().join_room(room, request.user)
        
        if result['success']:
            return Response({
                'message': 'Успешно присоединились к встрече',
                'join_url': result['join_url'],
                'room_password': result['room_password'],
                'participant': LiveSmartParticipantSerializer(result['participant']).data
            })
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_403_FORBIDDEN
            )
            
    except LiveSmartRoom.DoesNotExist:
        return Response(
            {'error': 'Комната не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsRoomParticipant])
def get_livesmart_room_info(request, room_id):
    """Получение информации о комнате LiveSmart"""
    try:
        room = LiveSmartRoom.objects.get(id=room_id)
        
        # Получаем информацию через сервис
        room_info = LiveSmartService().get_room_info(room)
        
        if room_info:
            return Response({
                'room_info': room_info,
                'room': LiveSmartRoomSerializer(room).data
            })
        else:
            return Response(
                {'error': 'Не удалось получить информацию о комнате'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except LiveSmartRoom.DoesNotExist:
        return Response(
            {'error': 'Комната не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsRoomHost])
def create_livesmart_recording(request, room_id):
    """Создание записи комнаты LiveSmart"""
    try:
        room = LiveSmartRoom.objects.get(id=room_id)
        
        # Проверка прав доступа
        if not (request.user.is_admin or room.lesson.teacher == request.user):
            return Response(
                {'error': 'Нет прав для создания записи этой комнаты'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        recording_data = request.data
        recording = LiveSmartService().create_recording(room, recording_data)
        
        if recording:
            serializer = LiveSmartRecordingSerializer(recording)
            return Response({
                'message': 'Запись создана',
                'recording': serializer.data
            })
        else:
            return Response(
                {'error': 'Не удалось создать запись'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except LiveSmartRoom.DoesNotExist:
        return Response(
            {'error': 'Комната не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_livesmart_rooms(request):
    """Получение комнат пользователя"""
    user = request.user
    
    if user.is_admin:
        rooms = LiveSmartRoom.objects.all()
    elif user.is_teacher:
        rooms = LiveSmartRoom.objects.filter(lesson__teacher=user)
    elif user.is_student:
        rooms = LiveSmartRoom.objects.filter(
            models.Q(lesson__group__students=user) |
            models.Q(lesson__student=user)
        )
    elif user.is_parent:
        children = user.children.all()
        rooms = LiveSmartRoom.objects.filter(
            models.Q(lesson__group__students__in=children) |
            models.Q(lesson__student__in=children)
        )
    else:
        rooms = LiveSmartRoom.objects.none()
    
    serializer = LiveSmartRoomSerializer(rooms, many=True)
    return Response({
        'rooms': serializer.data,
        'count': rooms.count()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_upcoming_livesmart_rooms(request):
    """Получение предстоящих встреч пользователя"""
    user = request.user
    now = timezone.now()
    
    if user.is_admin:
        rooms = LiveSmartRoom.objects.filter(
            lesson__start_time__gte=now,
            status='scheduled'
        )
    elif user.is_teacher:
        rooms = LiveSmartRoom.objects.filter(
            lesson__teacher=user,
            lesson__start_time__gte=now,
            status='scheduled'
        )
    elif user.is_student:
        rooms = LiveSmartRoom.objects.filter(
            models.Q(lesson__group__students=user) |
            models.Q(lesson__student=user),
            lesson__start_time__gte=now,
            status='scheduled'
        )
    elif user.is_parent:
        children = user.children.all()
        rooms = LiveSmartRoom.objects.filter(
            models.Q(lesson__group__students__in=children) |
            models.Q(lesson__student__in=children),
            lesson__start_time__gte=now,
            status='scheduled'
        )
    else:
        rooms = LiveSmartRoom.objects.none()
    
    rooms = rooms.order_by('lesson__start_time')[:10]  # Первые 10 предстоящих встреч
    
    serializer = LiveSmartRoomSerializer(rooms, many=True)
    return Response({
        'upcoming_rooms': serializer.data,
        'count': rooms.count()
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def bulk_create_livesmart_rooms(request):
    """Массовое создание комнат LiveSmart"""
    lesson_ids = request.data.get('lesson_ids', [])
    
    created_rooms = []
    errors = []
    
    for lesson_id in lesson_ids:
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            
            # Создаем комнату через сервис
            result = LiveSmartService().create_room(lesson, request.user)
            
            if result['success']:
                created_rooms.append(result['room'])
            else:
                errors.append({
                    'lesson_id': lesson_id,
                    'error': result['error']
                })
                
        except Lesson.DoesNotExist:
            errors.append({
                'lesson_id': lesson_id,
                'error': 'Занятие не найдено'
            })
        except Exception as e:
            errors.append({
                'lesson_id': lesson_id,
                'error': str(e)
            })
    
    serializer = LiveSmartRoomSerializer(created_rooms, many=True)
    return Response({
        'message': f'Создано {len(created_rooms)} комнат',
        'rooms': serializer.data,
        'errors': errors
    })