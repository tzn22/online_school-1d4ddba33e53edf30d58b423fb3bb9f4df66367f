from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone  # Добавили этот импорт
from .models import ChatRoom, Message, MessageReadStatus, ChatSettings
from accounts.models import User
from .serializers import (
    ChatRoomSerializer, 
    MessageSerializer, 
    MessageCreateSerializer,
    ChatSettingsSerializer,
    UnreadMessagesSerializer
)
from .permissions import IsChatParticipant


class ChatRoomListCreateView(generics.ListCreateAPIView):
    """Список чатов и создание нового чата"""
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['chat_type', 'is_active']
    search_fields = ['name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(participants=user, is_active=True).distinct()
    
    def perform_create(self, serializer):
        room = serializer.save(created_by=self.request.user)
        # Добавляем создателя в участники, если он не добавлен автоматически
        if self.request.user not in room.participants.all():
            room.participants.add(self.request.user)

class ChatRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали чата"""
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated, IsChatParticipant]
    
    def perform_destroy(self, instance):
        # Мягкое удаление - деактивируем чат
        instance.is_active = False
        instance.save()

class MessageListCreateView(generics.ListCreateAPIView):
    """Список сообщений и создание нового сообщения"""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['room', 'message_type', 'is_read']
    ordering_fields = ['created_at']
    ordering = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        room_id = self.request.query_params.get('room', None)
        
        if room_id:
            # Проверяем, что пользователь участник чата
            room = get_object_or_404(ChatRoom, id=room_id, participants=user)
            queryset = Message.objects.filter(room=room)
            
            # Отмечаем сообщения как прочитанные
            unread_messages = queryset.filter(is_read=False).exclude(sender=user)
            for message in unread_messages:
                MessageReadStatus.objects.get_or_create(
                    message=message,
                    user=user,
                    defaults={'read_at': timezone.now()}
                )
                # Обновляем флаг is_read если все участники прочитали
                if message.read_statuses.count() >= room.participants.count() - 1:
                    message.is_read = True
                    message.save()
            
            return queryset
        return Message.objects.none()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer
    
    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        # Создаем статус прочтения для отправителя
        MessageReadStatus.objects.create(
            message=message,
            user=self.request.user
        )

class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали сообщения"""
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            # Только отправитель может редактировать сообщение
            return [IsAuthenticated()]
        elif self.request.method == 'DELETE':
            # Только отправитель или админ могут удалить сообщение
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def update(self, request, *args, **kwargs):
        message = self.get_object()
        if message.sender != request.user and not request.user.is_admin:
            return Response({
                'error': 'Только отправитель может редактировать сообщение'
            }, status=status.HTTP_403_FORBIDDEN)
        
        message.is_edited = True
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        if message.sender != request.user and not request.user.is_admin:
            return Response({
                'error': 'Только отправитель или админ могут удалить сообщение'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().destroy(request, *args, **kwargs)

class ChatSettingsView(generics.RetrieveUpdateAPIView):
    """Настройки чата пользователя"""
    serializer_class = ChatSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        settings, created = ChatSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_messages(request):
    """Получить количество непрочитанных сообщений по чатам"""
    user = request.user
    
    # Получаем все чаты пользователя
    user_rooms = ChatRoom.objects.filter(participants=user, is_active=True)
    
    unread_data = []
    for room in user_rooms:
        unread_count = Message.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=user).count()
        
        if unread_count > 0:
            unread_data.append({
                'room_id': room.id,
                'room_name': room.name or f"Чат {room.id}",
                'unread_count': unread_count
            })
    
    serializer = UnreadMessagesSerializer(unread_data, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_as_read(request):
    """Отметить сообщения как прочитанные"""
    room_id = request.data.get('room_id')
    message_ids = request.data.get('message_ids', [])
    
    try:
        room = ChatRoom.objects.get(id=room_id, participants=request.user)
        
        if message_ids:
            messages = Message.objects.filter(
                id__in=message_ids,
                room=room
            ).exclude(sender=request.user)
        else:
            # Отмечаем все непрочитанные сообщения в чате
            messages = Message.objects.filter(
                room=room,
                is_read=False
            ).exclude(sender=request.user)
        
        # Создаем статусы прочтения
        for message in messages:
            MessageReadStatus.objects.get_or_create(
                message=message,
                user=request.user,
                defaults={'read_at': timezone.now()}
            )
        
        # Обновляем флаги is_read
        updated_count = 0
        for message in messages:
            if message.read_statuses.count() >= room.participants.count() - 1:
                message.is_read = True
                message.save()
                updated_count += 1
        
        return Response({
            'message': f'Отмечено {len(messages)} сообщений как прочитанные',
            'updated_messages': updated_count
        })
        
    except ChatRoom.DoesNotExist:
        return Response({
            'error': 'Чат не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_private_chat(request):
    """Создать приватный чат с пользователем"""
    user_id = request.data.get('user_id')
    
    try:
        other_user = User.objects.get(id=user_id)
        
        # Проверяем, существует ли уже чат между этими пользователями
        existing_room = ChatRoom.objects.filter(
            chat_type='private',
            participants=request.user
        ).filter(
            participants=other_user
        ).annotate(
            participant_count=Count('participants')
        ).filter(
            participant_count=2
        ).first()
        
        if existing_room:
            serializer = ChatRoomSerializer(existing_room)
            return Response({
                'message': 'Чат уже существует',
                'room': serializer.data
            })
        
        # Создаем новый чат
        room = ChatRoom.objects.create(
            chat_type='private',
            created_by=request.user
        )
        room.participants.add(request.user, other_user)
        
        serializer = ChatRoomSerializer(room)
        return Response({
            'message': 'Приватный чат создан',
            'room': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_participants(request, room_id):
    """Получить список участников чата"""
    try:
        room = ChatRoom.objects.get(id=room_id, participants=request.user)
        participants = room.participants.all()
        
        participants_data = [
            {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'email': user.email,
                'avatar': user.avatar.url if user.avatar else None,
                'is_online': False,  # Можно интегрировать с WebSocket для онлайн-статуса
                'last_seen': user.last_login
            }
            for user in participants
        ]
        
        return Response({
            'room_id': room.id,
            'participants': participants_data
        })
        
    except ChatRoom.DoesNotExist:
        return Response({
            'error': 'Чат не найден или у вас нет доступа'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_participant_to_chat(request, room_id):
    """Добавить участника в чат"""
    user_id = request.data.get('user_id')
    
    try:
        room = ChatRoom.objects.get(id=room_id, created_by=request.user)
        user = User.objects.get(id=user_id)
        
        if user in room.participants.all():
            return Response({
                'message': 'Пользователь уже в чате'
            })
        
        room.participants.add(user)
        
        return Response({
            'message': f'Пользователь {user.get_full_name() or user.username} добавлен в чат'
        })
        
    except ChatRoom.DoesNotExist:
        return Response({
            'error': 'Чат не найден или вы не являетесь создателем'
        }, status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_participant_from_chat(request, room_id):
    """Удалить участника из чата"""
    user_id = request.data.get('user_id')
    
    try:
        room = ChatRoom.objects.get(id=room_id, created_by=request.user)
        
        if user_id == request.user.id:
            return Response({
                'error': 'Нельзя удалить себя из чата'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(id=user_id)
        room.participants.remove(user)
        
        return Response({
            'message': f'Пользователь {user.get_full_name() or user.username} удален из чата'
        })
        
    except ChatRoom.DoesNotExist:
        return Response({
            'error': 'Чат не найден или вы не являетесь создателем'
        }, status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)