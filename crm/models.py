from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = settings.AUTH_USER_MODEL

class StudentProfile(models.Model):
    """Расширенный профиль студента"""
    student = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Студент')
    )
    
    # Образовательная информация
    education_level = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Уровень образования')
    )
    school = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Школа/Университет')
    )
    grade = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Класс/Курс')
    )
    
    # Языковые навыки
    native_language = models.CharField(
        max_length=50,
        default='Русский',
        verbose_name=_('Родной язык')
    )
    target_language = models.CharField(
        max_length=50,
        default='Английский',
        verbose_name=_('Целевой язык')
    )
    language_level = models.CharField(
        max_length=20,
        choices=[
            ('a1', 'A1 - Начальный'),
            ('a2', 'A2 - Элементарный'),
            ('b1', 'B1 - Средний'),
            ('b2', 'B2 - Выше среднего'),
            ('c1', 'C1 - Продвинутый'),
            ('c2', 'C2 - Владение на уровне носителя'),
        ],
        blank=True,
        verbose_name=_('Уровень языка')
    )
    
    # Контактная информация родителей
    parent_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Имя родителя')
    )
    parent_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Телефон родителя')
    )
    parent_email = models.EmailField(
        blank=True,
        verbose_name=_('Email родителя')
    )
    
    # Предпочтения
    preferred_learning_time = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Предпочтительное время занятий')
    )
    learning_goals = models.TextField(
        blank=True,
        verbose_name=_('Цели обучения')
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
        verbose_name = _('Профиль студента')
        verbose_name_plural = _('Профили студентов')
    
    def __str__(self):
        return f"Профиль {self.student.get_full_name() or self.student.username}"

class TeacherProfile(models.Model):
    """Расширенный профиль преподавателя"""
    teacher = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_('Преподаватель')
    )
    
    # Образование
    degree = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Ученая степень')
    )
    university = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Университет')
    )
    specialization = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Специализация')
    )
    
    # Опыт работы
    years_of_experience = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Лет опыта')
    )
    teaching_experience = models.TextField(
        blank=True,
        verbose_name=_('Опыт преподавания')
    )
    
    # Языки
    languages_spoken = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Знание языков')
    )
    certificates = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Сертификаты')
    )
    
    # Предметы
    subjects = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Предметы преподавания')
    )
    teaching_methods = models.TextField(
        blank=True,
        verbose_name=_('Методики преподавания')
    )
    
    # Доступность
    available_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Доступное время')
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
        verbose_name = _('Профиль преподавателя')
        verbose_name_plural = _('Профили преподавателей')
    
    def __str__(self):
        return f"Профиль {self.teacher.get_full_name() or self.teacher.username}"

class Lead(models.Model):
    """Потенциальный клиент (лид)"""
    LEAD_STATUS_CHOICES = [
        ('new', _('Новый')),
        ('contacted', _('Связались')),
        ('interested', _('Заинтересован')),
        ('demo_scheduled', _('Назначена демо-встреча')),
        ('demo_completed', _('Демо-встреча проведена')),
        ('proposal_sent', _('Отправлено предложение')),
        ('negotiation', _('Переговоры')),
        ('converted', _('Конвертирован')),
        ('lost', _('Потерян')),
    ]
    
    LEAD_SOURCE_CHOICES = [
        ('website', _('Сайт')),
        ('social_media', _('Социальные сети')),
        ('referral', _('Реферал')),
        ('advertisement', _('Реклама')),
        ('event', _('Мероприятие')),
        ('other', _('Другое')),
    ]
    
    first_name = models.CharField(
        max_length=100,
        verbose_name=_('Имя')
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name=_('Фамилия')
    )
    email = models.EmailField(
        verbose_name=_('Email')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Телефон')
    )
    age = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Возраст')
    )
    interested_course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Интересующий курс')
    )
    status = models.CharField(
        max_length=20,
        choices=LEAD_STATUS_CHOICES,
        default='new',
        verbose_name=_('Статус')
    )
    source = models.CharField(
        max_length=20,
        choices=LEAD_SOURCE_CHOICES,
        default='website',
        verbose_name=_('Источник')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Заметки')
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'admin'},
        verbose_name=_('Назначен менеджер')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    converted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата конверсии')
    )
    
    class Meta:
        verbose_name = _('Лид')
        verbose_name_plural = _('Лиды')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.status}"

class StudentActivity(models.Model):
    """Активность студента"""
    ACTIVITY_TYPE_CHOICES = [
        ('login', _('Вход в систему')),
        ('lesson_attended', _('Посетил занятие')),
        ('lesson_missed', _('Пропустил занятие')),
        ('homework_submitted', _('Сдал домашнее задание')),
        ('homework_late', _('Сдал домашнее задание с опозданием')),
        ('payment_made', _('Сделал платеж')),
        ('feedback_given', _('Оставил отзыв')),
        ('support_request', _('Обратился в поддержку')),
        ('course_completed', _('Завершил курс')),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Студент')
    )
    activity_type = models.CharField(
        max_length=30,
        choices=ACTIVITY_TYPE_CHOICES,
        verbose_name=_('Тип активности')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('ID связанного объекта')
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
        verbose_name = _('Активность студента')
        verbose_name_plural = _('Активности студентов')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.student} - {self.get_activity_type_display()}"

class AnalyticsReport(models.Model):
    """Аналитический отчет"""
    REPORT_TYPE_CHOICES = [
        ('student_performance', _('Успеваемость студентов')),
        ('teacher_performance', _('Эффективность преподавателей')),
        ('financial', _('Финансовая отчетность')),
        ('marketing', _('Маркетинговая отчетность')),
        ('operational', _('Операционная отчетность')),
    ]
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('Название отчета')
    )
    report_type = models.CharField(
        max_length=30,
        choices=REPORT_TYPE_CHOICES,
        verbose_name=_('Тип отчета')
    )
    period_start = models.DateField(
        verbose_name=_('Начало периода')
    )
    period_end = models.DateField(
        verbose_name=_('Конец периода')
    )
    data = models.JSONField(
        default=dict,
        verbose_name=_('Данные отчета')
    )
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
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
        verbose_name = _('Аналитический отчет')
        verbose_name_plural = _('Аналитические отчеты')
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} ({self.period_start} - {self.period_end})"