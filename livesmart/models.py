from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import datetime, timedelta

User = settings.AUTH_USER_MODEL

class LiveSmartRoom(models.Model):
    """Комната LiveSmart"""
    ROOM_STATUS_CHOICES = [
        ('scheduled', _('Запланирована')),
        ('active', _('Активна')),
        ('completed', _('Завершена')),
        ('cancelled', _('Отменена')),
    ]
    
    lesson = models.OneToOneField(
        'courses.Lesson',
        on_delete=models.CASCADE,
        related_name='livesmart_room',
        verbose_name=_('Занятие')
    )
    room_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('ID комнаты')
    )
    room_name = models.CharField(
        max_length=255,
        verbose_name=_('Название комнаты')
    )
    join_url = models.URLField(
        blank=True,
        verbose_name=_('Ссылка для присоединения')
    )
    host_url = models.URLField(
        blank=True,
        verbose_name=_('Ссылка для хоста')
    )
    room_password = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Пароль комнаты')
    )
    max_participants = models.PositiveIntegerField(
        default=50,
        verbose_name=_('Максимальное количество участников')
    )
    is_recording_enabled = models.BooleanField(
        default=False,
        verbose_name=_('Запись включена')
    )
    recording_url = models.URLField(
        blank=True,
        verbose_name=_('Ссылка на запись')
    )
    recording_file = models.FileField(
        upload_to='livesmart_recordings/',
        blank=True,
        null=True,
        verbose_name=_('Файл записи')
    )
    status = models.CharField(
        max_length=20,
        choices=ROOM_STATUS_CHOICES,
        default='scheduled',
        verbose_name=_('Статус комнаты')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала')
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания')
    )
    
    class Meta:
        verbose_name = _('Комната LiveSmart')
        verbose_name_plural = _('Комнаты LiveSmart')
        ordering = ['-created_at']
        app_label = 'livesmart'  # ← ДОБАВИЛИ ЭТО!
        indexes = [
            models.Index(fields=['lesson', 'status']),
            models.Index(fields=['room_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['started_at']),
            models.Index(fields=['ended_at']),
        ]
    
    def __str__(self):
        return f"LiveSmart комната: {self.room_name}"

class LiveSmartParticipant(models.Model):
    """Участник LiveSmart комнаты"""
    PARTICIPANT_ROLE_CHOICES = [
        ('host', _('Хост')),
        ('co_host', _('Ко-хост')),
        ('participant', _('Участник')),
        ('observer', _('Наблюдатель')),
    ]
    
    room = models.ForeignKey(
        LiveSmartRoom,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_('Комната')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь')
    )
    role = models.CharField(
        max_length=20,
        choices=PARTICIPANT_ROLE_CHOICES,
        default='participant',
        verbose_name=_('Роль')
    )
    joined_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Время присоединения')
    )
    left_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Время выхода')
    )
    duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_('Длительность участия')
    )
    is_present = models.BooleanField(
        default=False,
        verbose_name=_('Присутствовал')
    )
    participant_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('ID участника')
    )
    
    class Meta:
        verbose_name = _('Участник LiveSmart')
        verbose_name_plural = _('Участники LiveSmart')
        unique_together = ['room', 'user']
        ordering = ['role', 'joined_at']
        app_label = 'livesmart'  # ← ДОБАВИЛИ ЭТО!
        indexes = [
            models.Index(fields=['room', 'user']),
            models.Index(fields=['role']),
            models.Index(fields=['is_present']),
            models.Index(fields=['joined_at']),
            models.Index(fields=['left_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

class LiveSmartRecording(models.Model):
    """Запись LiveSmart комнаты"""
    recording_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('ID записи')
    )
    room = models.ForeignKey(
        LiveSmartRoom,
        on_delete=models.CASCADE,
        related_name='recordings',
        verbose_name=_('Комната')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Название записи')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание записи')
    )
    file_url = models.URLField(
        blank=True,
        verbose_name=_('Ссылка на файл')
    )
    file = models.FileField(
        upload_to='livesmart_recordings/',
        blank=True,
        null=True,
        verbose_name=_('Файл записи')
    )
    file_size = models.BigIntegerField(
        default=0,
        verbose_name=_('Размер файла (байты)')
    )
    duration = models.DurationField(
        verbose_name=_('Длительность записи')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Публичная запись')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Загрузил')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата публикации')
    )
    
    class Meta:
        verbose_name = _('Запись LiveSmart')
        verbose_name_plural = _('Записи LiveSmart')
        ordering = ['-created_at']
        app_label = 'livesmart'  # ← ДОБАВИЛИ ЭТО!
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['recording_id']),
            models.Index(fields=['is_public', 'created_at']),
            models.Index(fields=['uploaded_by', 'created_at']),
            models.Index(fields=['published_at']),
        ]
    
    def __str__(self):
        return f"Запись: {self.title}"

class LiveSmartSettings(models.Model):
    """Настройки LiveSmart"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='livesmart_settings',
        verbose_name=_('Пользователь')
    )
    api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('API ключ')
    )
    api_secret = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('API секрет')
    )
    default_room_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Настройки комнаты по умолчанию')
    )
    is_recording_enabled = models.BooleanField(
        default=False,
        verbose_name=_('Запись включена по умолчанию')
    )
    max_participants = models.PositiveIntegerField(
        default=50,
        verbose_name=_('Максимальное количество участников по умолчанию')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    
    class Meta:
        verbose_name = _('Настройки LiveSmart')
        verbose_name_plural = _('Настройки LiveSmart')
        ordering = ['-created_at']
        app_label = 'livesmart'  # ← ДОБАВИЛИ ЭТО!
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['api_key']),
            models.Index(fields=['is_recording_enabled']),
        ]
    
    def __str__(self):
        return f"Настройки LiveSmart для {self.user.get_full_name() or self.user.username}"