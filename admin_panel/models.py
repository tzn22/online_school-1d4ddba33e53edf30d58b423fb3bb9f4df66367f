from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from accounts.models import User
from courses.models import Course, Group, Lesson
from payments.models import Payment

class AdminActionLog(models.Model):
    """Лог действий администраторов"""
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('delete', 'Удаление'),
        ('bulk_action', 'Массовое действие'),
        ('export', 'Экспорт'),
        ('import', 'Импорт'),
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
    ]
    
    admin_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='admin_actions',
        limit_choices_to={'role': 'admin'},
        verbose_name=_('Администратор')
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name=_('Тип действия')
    )
    model_name = models.CharField(
        max_length=100,
        verbose_name=_('Модель')
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('ID объекта')
    )
    description = models.TextField(
        verbose_name=_('Описание')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP адрес')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    
    class Meta:
        verbose_name = _('Лог действия администратора')
        verbose_name_plural = _('Логи действий администраторов')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['model_name', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.admin_user} - {self.get_action_type_display()} - {self.model_name}"

class ReportTemplate(models.Model):
    """Шаблоны отчетов"""
    REPORT_TYPE_CHOICES = [
        ('user', 'Пользователи'),
        ('course', 'Курсы'),
        ('payment', 'Платежи'),
        ('lesson', 'Занятия'),
        ('attendance', 'Посещаемость'),
        ('financial', 'Финансовый'),
        ('marketing', 'Маркетинг'),
        ('operational', 'Операционный'),
    ]
    
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('Название шаблона')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        verbose_name=_('Тип отчета')
    )
    template_file = models.FileField(
        upload_to='report_templates/',
        verbose_name=_('Файл шаблона')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_report_templates',
        limit_choices_to={'role': 'admin'},
        verbose_name=_('Создан пользователем')
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
        verbose_name = _('Шаблон отчета')
        verbose_name_plural = _('Шаблоны отчетов')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class GeneratedReport(models.Model):
    """Сгенерированные отчеты"""
    report_template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='generated_reports',
        verbose_name=_('Шаблон отчета')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Название отчета')
    )
    period_start = models.DateField(
        verbose_name=_('Начало периода')
    )
    period_end = models.DateField(
        verbose_name=_('Конец периода')
    )
    file = models.FileField(
        upload_to='generated_reports/',
        verbose_name=_('Файл отчета')
    )
    file_size = models.BigIntegerField(
        verbose_name=_('Размер файла (байты)')
    )
    generated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='generated_reports',
        limit_choices_to={'role': 'admin'},
        verbose_name=_('Сгенерирован пользователем')
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата генерации')
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name=_('Опубликован')
    )
    
    class Meta:
        verbose_name = _('Сгенерированный отчет')
        verbose_name_plural = _('Сгенерированные отчеты')
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_template', 'generated_at']),
            models.Index(fields=['generated_by', 'generated_at']),
            models.Index(fields=['is_published', 'generated_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.period_start} - {self.period_end})"

class MassEmailCampaign(models.Model):
    """Массовая email рассылка"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('scheduled', 'Запланирована'),
        ('sending', 'Отправляется'),
        ('completed', 'Завершена'),
        ('failed', 'Ошибка'),
        ('cancelled', 'Отменена'),
    ]
    
    name = models.CharField(
        max_length=255,
        verbose_name=_('Название кампании')
    )
    subject = models.CharField(
        max_length=255,
        verbose_name=_('Тема письма')
    )
    content = models.TextField(
        verbose_name=_('Содержание письма')
    )
    target_audience = models.CharField(
        max_length=20,
        choices=[
            ('all', 'Все пользователи'),
            ('students', 'Студенты'),
            ('teachers', 'Преподаватели'),
            ('parents', 'Родители'),
            ('admins', 'Администраторы'),
        ],
        default='all',
        verbose_name=_('Целевая аудитория')
    )
    custom_recipients = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Пользовательские получатели (ID)')
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Запланировано на')
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Отправлено')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Завершено')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Статус')
    )
    total_recipients = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Всего получателей')
    )
    sent_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Отправлено')
    )
    failed_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ошибок')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_campaigns',
        limit_choices_to={'role': 'admin'},
        verbose_name=_('Создан пользователем')
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
        verbose_name = _('Email кампания')
        verbose_name_plural = _('Email кампании')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['scheduled_at']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def success_rate(self):
        """Процент успешной доставки"""
        if self.sent_count > 0:
            return round((self.sent_count - self.failed_count) / self.sent_count * 100, 2)
        return 0

class SystemSetting(models.Model):
    """Системные настройки"""
    SETTING_TYPE_CHOICES = [
        ('boolean', 'Булево значение'),
        ('integer', 'Целое число'),
        ('float', 'Дробное число'),
        ('string', 'Строка'),
        ('text', 'Текст'),
        ('json', 'JSON'),
    ]
    
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Ключ настройки')
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Название настройки')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    setting_type = models.CharField(
        max_length=20,
        choices=SETTING_TYPE_CHOICES,
        default='string',
        verbose_name=_('Тип настройки')
    )
    value = models.TextField(
        blank=True,
        verbose_name=_('Значение')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Публичная настройка')
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Категория')
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
        verbose_name = _('Системная настройка')
        verbose_name_plural = _('Системные настройки')
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['category']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key})"
    
    def get_typed_value(self):
        """Получить значение в правильном типе"""
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'integer':
            try:
                return int(self.value)
            except ValueError:
                return 0
        elif self.setting_type == 'float':
            try:
                return float(self.value)
            except ValueError:
                return 0.0
        elif self.setting_type == 'json':
            import json
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        return self.value