from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import models  # Добавили этот импорт
from .models import Notification, NotificationTemplate, UserNotificationSettings, NotificationLog
from accounts.models import User
from .serializers import (
    NotificationSerializer, 
    NotificationCreateSerializer,
    NotificationTemplateSerializer, 
    UserNotificationSettingsSerializer,
    NotificationLogSerializer,
    BulkNotificationSerializer
)
from .services import NotificationService
from .permissions import IsNotificationOwner


class NotificationListView(generics.ListAPIView):
    """Список уведомлений пользователя"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'channel', 'is_read']
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали уведомления"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsNotificationOwner]
    
    def update(self, request, *args, **kwargs):
        # Разрешаем только обновление статуса прочтения
        notification = self.get_object()
        is_read = request.data.get('is_read')
        
        if is_read is not None:
            notification.is_read = is_read
            if is_read and not notification.read_at:
                notification.read_at = timezone.now()
            elif not is_read:
                notification.read_at = None
            notification.save()
            
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
        
        return Response({
            'error': 'Можно обновлять только поле is_read'
        }, status=status.HTTP_400_BAD_REQUEST)

class NotificationTemplateListView(generics.ListCreateAPIView):
    """Список шаблонов уведомлений"""
    queryset = NotificationTemplate.objects.filter(is_active=True)
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]

class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали шаблона уведомления"""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]

class UserNotificationSettingsView(generics.RetrieveUpdateAPIView):
    """Настройки уведомлений пользователя"""
    serializer_class = UserNotificationSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        settings, created = UserNotificationSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    """Отметить уведомление как прочитанное"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = NotificationSerializer(notification)
        return Response({
            'message': 'Уведомление отмечено как прочитанное',
            'notification': serializer.data
        })
    except Notification.DoesNotExist:
        return Response({
            'error': 'Уведомление не найдено'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    """Отметить все уведомления как прочитанные"""
    updated_count = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).update(
        is_read=True, 
        read_at=timezone.now()
    )
    
    return Response({
        'message': f'{updated_count} уведомлений отмечены как прочитанные'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """Получить количество непрочитанных уведомлений"""
    unread_count = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).count()
    
    return Response({
        'unread_count': unread_count
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_bulk_notification(request):
    """Массовая отправка уведомлений (только для админов)"""
    serializer = BulkNotificationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            notifications = NotificationService.send_bulk_notification(
                user_ids=serializer.validated_data.get('user_ids'),
                roles=serializer.validated_data.get('roles'),
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                notification_type=serializer.validated_data['notification_type'],
                channels=serializer.validated_data['channels']
            )
            
            return Response({
                'message': f'Отправлено {len(notifications)} уведомлений',
                'notifications_count': len(notifications)
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_notification(request):
    """Отправка тестового уведомления"""
    channel = request.data.get('channel', 'in_app')
    title = request.data.get('title', 'Тестовое уведомление')
    message = request.data.get('message', 'Это тестовое уведомление')
    
    try:
        notification = NotificationService.send_notification(
            user=request.user,
            title=title,
            message=message,
            notification_type='info',
            channels=[channel]
        )
        
        serializer = NotificationSerializer(notification)
        return Response({
            'message': 'Тестовое уведомление отправлено',
            'notification': serializer.data
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def notification_statistics(request):
    """Статистика уведомлений (только для админов)"""
    # Общая статистика
    total_notifications = Notification.objects.count()
    unread_notifications = Notification.objects.filter(is_read=False).count()
    
    # Статистика по типам
    type_stats = Notification.objects.values('notification_type').annotate(
        count=models.Count('id')
    ).order_by('-count')
    
    # Статистика по каналам
    channel_stats = Notification.objects.values('channel').annotate(
        count=models.Count('id')
    ).order_by('-count')
    
    # Статистика по дням
    daily_stats = Notification.objects.extra(
        select={'date': "DATE(created_at)"}
    ).values('date').annotate(
        count=models.Count('id')
    ).order_by('-date')[:30]  # Последние 30 дней
    
    return Response({
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'type_statistics': list(type_stats),
        'channel_statistics': list(channel_stats),
        'daily_statistics': list(daily_stats)
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_notifications(request):
    """Очистить уведомления пользователя"""
    notification_type = request.data.get('type', None)
    days_old = request.data.get('days_old', None)
    
    queryset = Notification.objects.filter(user=request.user)
    
    # Фильтр по типу
    if notification_type:
        queryset = queryset.filter(notification_type=notification_type)
    
    # Фильтр по давности
    if days_old:
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days_old)
        queryset = queryset.filter(created_at__lt=cutoff_date)
    
    deleted_count = queryset.count()
    queryset.delete()
    
    return Response({
        'message': f'Удалено {deleted_count} уведомлений'
    })