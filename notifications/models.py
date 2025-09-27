from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('info', _('Информация')),
        ('warning', _('Предупреждение')),
        ('error', _('Ошибка')),
        ('success', _('Успех')),
        ('lesson', _('Занятие')),
        ('payment', _('Платеж')),
        ('message', _('Сообщение')),
        ('system', _('Система')),
    ]
    
    NOTIFICATION_CHANNEL_CHOICES = [
        ('email', _('Email')),
        ('push', _('Push-уведомление')),
        ('telegram', _('Telegram')),
        ('whatsapp', _('WhatsApp')),
        ('sms', _('SMS')),
        ('in_app', _('В приложении')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Пользователь')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Заголовок')
    )
    message = models.TextField(
        verbose_name=_('Сообщение')
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='info',
        verbose_name=_('Тип уведомления')
    )
    channel = models.CharField(
        max_length=20,
        choices=NOTIFICATION_CHANNEL_CHOICES,
        default='in_app',
        verbose_name=_('Канал отправки')
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Прочитано')
    )
    is_sent = models.BooleanField(
        default=False,
        verbose_name=_('Отправлено')
    )
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('ID связанного объекта')
    )
    related_object_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Тип связанного объекта')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата отправки')
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата прочтения')
    )
    
    class Meta:
        verbose_name = _('Уведомление')
        verbose_name_plural = _('Уведомления')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user}"

class NotificationTemplate(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Название шаблона')
    )
    title_template = models.CharField(
        max_length=255,
        verbose_name=_('Шаблон заголовка')
    )
    message_template = models.TextField(
        verbose_name=_('Шаблон сообщения')
    )
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('info', _('Информация')),
            ('warning', _('Предупреждение')),
            ('error', _('Ошибка')),
            ('success', _('Успех')),
            ('lesson', _('Занятие')),
            ('payment', _('Платеж')),
            ('message', _('Сообщение')),
        ],
        default='info',
        verbose_name=_('Тип уведомления')
    )
    channels = models.JSONField(
        default=list,
        verbose_name=_('Каналы отправки')
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
        verbose_name = _('Шаблон уведомления')
        verbose_name_plural = _('Шаблоны уведомлений')
    
    def __str__(self):
        return self.name

class UserNotificationSettings(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name=_('Пользователь')
    )
    
    # Email уведомления
    email_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Email уведомления')
    )
    email_lesson_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Напоминания о занятиях по email')
    )
    email_payment_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о платежах по email')
    )
    
    # Push уведомления
    push_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Push-уведомления')
    )
    push_lesson_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Напоминания о занятиях push')
    )
    
    # Telegram
    telegram_notifications = models.BooleanField(
        default=False,
        verbose_name=_('Telegram уведомления')
    )
    telegram_chat_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Telegram Chat ID')
    )
    
    # WhatsApp
    whatsapp_notifications = models.BooleanField(
        default=False,
        verbose_name=_('WhatsApp уведомления')
    )
    whatsapp_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Номер WhatsApp')
    )
    
    # SMS
    sms_notifications = models.BooleanField(
        default=False,
        verbose_name=_('SMS уведомления')
    )
    sms_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Номер телефона для SMS')
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
        verbose_name = _('Настройки уведомлений')
        verbose_name_plural = _('Настройки уведомлений')
    
    def __str__(self):
        return f"Настройки уведомлений для {self.user}"

class NotificationLog(models.Model):
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('Уведомление')
    )
    channel = models.CharField(
        max_length=20,
        choices=[
            ('email', _('Email')),
            ('push', _('Push-уведомление')),
            ('telegram', _('Telegram')),
            ('whatsapp', _('WhatsApp')),
            ('sms', _('SMS')),
        ],
        verbose_name=_('Канал')
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('В ожидании')),
            ('sent', _('Отправлено')),
            ('failed', _('Ошибка')),
        ],
        default='pending',
        verbose_name=_('Статус')
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_('Сообщение об ошибке')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата отправки')
    )
    
    class Meta:
        verbose_name = _('Лог уведомления')
        verbose_name_plural = _('Логи уведомлений')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Лог {self.notification} - {self.channel}"