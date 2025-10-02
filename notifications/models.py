from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import datetime, timedelta

User = settings.AUTH_USER_MODEL

class NotificationTemplate(models.Model):
    """Шаблоны уведомлений"""
    NOTIFICATION_TYPE_CHOICES = [
        ('info', _('Информация')),
        ('warning', _('Предупреждение')),
        ('error', _('Ошибка')),
        ('success', _('Успех')),
        ('lesson', _('Занятие')),
        ('payment', _('Платеж')),
        ('message', _('Сообщение')),
        ('system', _('Система')),
        ('course', _('Курс')),
        ('attendance', _('Посещаемость')),
        ('homework', _('Домашнее задание')),
        ('test', _('Тест')),
        ('feedback', _('Обратная связь')),
        ('support', _('Поддержка')),
        ('admin', _('Административное')),
    ]
    
    NOTIFICATION_CHANNEL_CHOICES = [
        ('email', _('Email')),
        ('push', _('Push-уведомление')),
        ('telegram', _('Telegram')),
        ('whatsapp', _('WhatsApp')),
        ('sms', _('SMS')),
        ('in_app', _('В приложении')),
    ]
    
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
        choices=NOTIFICATION_TYPE_CHOICES,
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
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name

class Notification(models.Model):
    """Уведомления пользователей"""
    NOTIFICATION_TYPE_CHOICES = [
        ('info', _('Информация')),
        ('warning', _('Предупреждение')),
        ('error', _('Ошибка')),
        ('success', _('Успех')),
        ('lesson', _('Занятие')),
        ('payment', _('Платеж')),
        ('message', _('Сообщение')),
        ('system', _('Система')),
        ('course', _('Курс')),
        ('attendance', _('Посещаемость')),
        ('homework', _('Домашнее задание')),
        ('test', _('Тест')),
        ('feedback', _('Обратная связь')),
        ('support', _('Поддержка')),
        ('admin', _('Административное')),
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
    channels = models.JSONField(
        default=list,
        verbose_name=_('Каналы отправки')
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
            models.Index(fields=['is_sent']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['read_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user}"

# === НОВАЯ МОДЕЛЬ UserNotificationSettings ===

class UserNotificationSettings(models.Model):
    """Настройки уведомлений пользователя"""
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
    email_support_responses = models.BooleanField(
        default=True,
        verbose_name=_('Ответы службы поддержки по email')
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
    push_payment_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о платежах push')
    )
    push_support_responses = models.BooleanField(
        default=True,
        verbose_name=_('Ответы службы поддержки push')
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
    telegram_lesson_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Напоминания о занятиях в Telegram')
    )
    telegram_payment_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о платежах в Telegram')
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
    whatsapp_lesson_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Напоминания о занятиях в WhatsApp')
    )
    whatsapp_payment_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о платежах в WhatsApp')
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
    sms_lesson_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Напоминания о занятиях SMS')
    )
    sms_payment_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Уведомления о платежах SMS')
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
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['email_notifications']),
            models.Index(fields=['push_notifications']),
            models.Index(fields=['telegram_notifications']),
            models.Index(fields=['whatsapp_notifications']),
            models.Index(fields=['sms_notifications']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Настройки уведомлений для {self.user.get_full_name() or self.user.username}"
    
    @property
    def is_any_notification_enabled(self):
        """Проверка, включены ли какие-либо уведомления"""
        return (
            self.email_notifications or
            self.push_notifications or
            self.telegram_notifications or
            self.whatsapp_notifications or
            self.sms_notifications
        )

# Найди модель NotificationLog и исправи поле title:

class NotificationLog(models.Model):
    """Лог уведомлений"""
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('Уведомление')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь')
    )
    title = models.CharField(
        max_length=255,
        default='Нет заголовка',  # ← ДОБАВИЛИ ЗНАЧЕНИЕ ПО УМОЛЧАНИЮ
        verbose_name=_('Заголовок')
    )
    message = models.TextField(
        blank=True,
        default='',  # ← ДОБАВИЛИ ЗНАЧЕНИЕ ПО УМОЛЧАНИЮ
        verbose_name=_('Сообщение')
    )
    notification_type = models.CharField(
        max_length=20,
        choices=Notification.NOTIFICATION_TYPE_CHOICES,
        default='info',
        verbose_name=_('Тип уведомления')
    )
    channels = models.JSONField(
        default=list,
        verbose_name=_('Каналы отправки')
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Прочитано')
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
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_('Сообщение об ошибке')
    )
    
    class Meta:
        verbose_name = _('Лог уведомления')
        verbose_name_plural = _('Логи уведомлений')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['is_read', 'created_at']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['read_at']),
        ]
    
    def __str__(self):
        return f"Лог {self.notification.title} - {self.user.get_full_name() or self.user.username}"