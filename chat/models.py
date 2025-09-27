from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = settings.AUTH_USER_MODEL

class ChatRoom(models.Model):
    CHAT_TYPE_CHOICES = [
        ('private', _('Приватный чат')),
        ('group', _('Групповой чат')),
        ('support', _('Чат поддержки')),
    ]
    
    name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Название чата')
    )
    chat_type = models.CharField(
        max_length=20,
        choices=CHAT_TYPE_CHOICES,
        default='private',
        verbose_name=_('Тип чата')
    )
    participants = models.ManyToManyField(
        User,
        related_name='chat_rooms',
        verbose_name=_('Участники')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_chats',
        verbose_name=_('Создатель')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
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
        verbose_name = _('Чат')
        verbose_name_plural = _('Чаты')
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.name:
            return self.name
        participants_names = ', '.join([
            user.get_full_name() or user.username 
            for user in self.participants.all()[:3]
        ])
        return f"Чат: {participants_names}"

class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('text', _('Текст')),
        ('image', _('Изображение')),
        ('file', _('Файл')),
        ('system', _('Системное сообщение')),
    ]
    
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Чат')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('Отправитель')
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        verbose_name=_('Тип сообщения')
    )
    content = models.TextField(
        blank=True,
        verbose_name=_('Содержание')
    )
    file = models.FileField(
        upload_to='chat_files/',
        blank=True,
        null=True,
        verbose_name=_('Файл')
    )
    image = models.ImageField(
        upload_to='chat_images/',
        blank=True,
        null=True,
        verbose_name=_('Изображение')
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Прочитано')
    )
    is_edited = models.BooleanField(
        default=False,
        verbose_name=_('Отредактировано')
    )
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('Ответ на сообщение')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата отправки')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    
    class Meta:
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['sender', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..."

class MessageReadStatus(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_statuses',
        verbose_name=_('Сообщение')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_read_statuses',
        verbose_name=_('Пользователь')
    )
    read_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата прочтения')
    )
    
    class Meta:
        verbose_name = _('Статус прочтения сообщения')
        verbose_name_plural = _('Статусы прочтения сообщений')
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user} прочитал сообщение {self.message.id}"

class ChatSettings(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='chat_settings',
        verbose_name=_('Пользователь')
    )
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления включены')
    )
    message_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о сообщениях')
    )
    sound_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Звук включен')
    )
    typing_indicators = models.BooleanField(
        default=True,
        verbose_name=_('Индикаторы набора текста')
    )
    message_preview = models.BooleanField(
        default=True,
        verbose_name=_('Предпросмотр сообщений')
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
        verbose_name = _('Настройки чата')
        verbose_name_plural = _('Настройки чатов')
    
    def __str__(self):
        return f"Настройки чата для {self.user}"