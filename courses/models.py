from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import datetime
from django.db import models

User = settings.AUTH_USER_MODEL

class Course(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_('Название курса')
    )
    description = models.TextField(
        verbose_name=_('Описание курса')
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Цена курса')
    )
    duration_hours = models.PositiveIntegerField(
        verbose_name=_('Длительность курса '),
        help_text=_('Общая длительность курса')
    )
    level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', _('Начальный')),
            ('intermediate', _('Средний')),
            ('advanced', _('Продвинутый')),
        ],
        verbose_name=_('Уровень сложности')
    )
    language = models.CharField(
        max_length=50,
        default='Английский',
        verbose_name=_('Язык преподавания')
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
        verbose_name = _('Курс')
        verbose_name_plural = _('Курсы')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Group(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_('Название группы')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name=_('Курс')
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_groups',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_('Преподаватель')
    )
    students = models.ManyToManyField(
        User,
        related_name='learning_groups',
        limit_choices_to={'role': 'student'},
        blank=True,
        verbose_name=_('Студенты')
    )
    max_students = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Максимальное количество студентов')
    )
    start_date = models.DateField(
        verbose_name=_('Дата начала')
    )
    end_date = models.DateField(
        verbose_name=_('Дата окончания')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    
    class Meta:
        verbose_name = _('Группа')
        verbose_name_plural = _('Группы')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.course.title}"
    
    @property
    def student_count(self):
        return self.students.count()
    
    @property
    def available_spots(self):
        return self.max_students - self.student_count

class Lesson(models.Model):
    LESSON_TYPE_CHOICES = [
        ('group', _('Групповое занятие')),
        ('individual', _('Индивидуальное занятие')),
    ]
    has_ai_trainer = models.BooleanField(default=False, verbose_name=_('Есть ИИ-тренажер'))
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='lessons',
        null=True,
        blank=True,
        verbose_name=_('Группа')
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='individual_lessons',
        limit_choices_to={'role': 'student'},
        null=True,
        blank=True,
        verbose_name=_('Студент (для индивидуальных)')
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lessons',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_('Преподаватель')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Тема занятия')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание занятия')
    )
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPE_CHOICES,
        default='group',
        verbose_name=_('Тип занятия')
    )
    start_time = models.DateTimeField(
        verbose_name=_('Время начала')
    )
    end_time = models.DateTimeField(
        verbose_name=_('Время окончания')
    )
    duration_minutes = models.PositiveIntegerField(
        verbose_name=_('Длительность (минуты)'),
        help_text=_('Длительность занятия в минутах')
    )
    zoom_link = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Ссылка на Zoom')
    )
    meeting_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('ID встречи')
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Завершено')
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
        verbose_name = _('Занятие')
        verbose_name_plural = _('Занятия')
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%d.%m.%Y %H:%M')}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Проверка, что для группового занятия указана группа
        if self.lesson_type == 'group' and not self.group:
            raise ValidationError(_('Для группового занятия необходимо указать группу'))
        
        # Проверка, что для индивидуального занятия указан студент
        if self.lesson_type == 'individual' and not self.student:
            raise ValidationError(_('Для индивидуального занятия необходимо указать студента'))
        
        # Проверка времени
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_('Время начала должно быть меньше времени окончания'))
    
    def save(self, *args, **kwargs):
        # Автоматически вычисляем длительность
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            self.duration_minutes = int(duration.total_seconds() / 60)
        super().save(*args, **kwargs)

class Attendance(models.Model):
    ATTENDANCE_STATUS_CHOICES = [
        ('present', _('Присутствовал')),
        ('absent', _('Отсутствовал')),
        ('late', _('Опоздал')),
        ('excused', _('Уважительная причина')),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('Занятие')
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendances',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Студент')
    )
    status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default='present',
        verbose_name=_('Статус посещения')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Комментарий')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Заметки')
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
        verbose_name = _('Посещение')
        verbose_name_plural = _('Посещения')
        unique_together = ['lesson', 'student']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student} - {self.lesson} - {self.get_status_display()}"

# === НОВЫЕ МОДЕЛИ ДЛЯ ПРЕПОДАВАТЕЛЯ ===

# 1. Модель бейджей
class Badge(models.Model):
    BADGE_TYPE_CHOICES = [
        ('participation', 'Участие'),
        ('excellent', 'Отлично'),
        ('attendance', 'Посещение'),
        ('homework', 'Домашнее задание'),
        ('test', 'Тест'),
        ('achievement', 'Достижение'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Название бейджа')
    description = models.TextField(verbose_name='Описание')
    badge_type = models.CharField(
        max_length=20, 
        choices=BADGE_TYPE_CHOICES,
        verbose_name='Тип бейджа'
    )
    icon = models.ImageField(
        upload_to='badges/', 
        blank=True, 
        null=True,
        verbose_name='Иконка'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Бейдж'
        verbose_name_plural = 'Бейджи'
    
    def __str__(self):
        return self.name

# 2. Привязка бейджа к студенту
class StudentBadge(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='badges_received',
        verbose_name='Студент'
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        verbose_name='Бейдж'
    )
    awarded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата выдачи')
    awarded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='awarded_badges',
        verbose_name='Выдан преподавателем'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='За занятие'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    
    class Meta:
        verbose_name = 'Выданный бейдж'
        verbose_name_plural = 'Выданные бейджи'
        unique_together = ['student', 'badge', 'lesson']

# 3. Модель прогресса студента
class StudentProgress(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='Курс'
    )
    completed_topics = models.JSONField(default=list, verbose_name='Пройденные темы')
    test_results = models.JSONField(default=dict, verbose_name='Результаты тестов')
    current_level = models.CharField(
        max_length=20,
        default='beginner',
        choices=[
            ('beginner', 'Начальный'),
            ('intermediate', 'Средний'),
            ('advanced', 'Продвинутый'),
        ],
        verbose_name='Текущий уровень'
    )
    overall_progress = models.PositiveIntegerField(default=0, verbose_name='Общий прогресс (%)')
    last_activity = models.DateTimeField(auto_now=True, verbose_name='Последняя активность')
    
    class Meta:
        verbose_name = 'Прогресс студента'
        verbose_name_plural = 'Прогресс студентов'
        unique_together = ['student', 'course']

# 4. Модель результатов тестов
class TestResult(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='test_results',
        verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='Курс'
    )
    test_name = models.CharField(max_length=100, verbose_name='Название теста')
    score = models.IntegerField(verbose_name='Балл')
    max_score = models.IntegerField(default=100, verbose_name='Максимальный балл')
    date_taken = models.DateTimeField(auto_now_add=True, verbose_name='Дата прохождения')
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='За занятие'
    )
    
    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'

# === МОДЕЛИ ДЛЯ ВИДЕОУРОКОВ ===

# 1. Модель видеоуроков
class VideoLesson(models.Model):
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='video_lesson',
        verbose_name='Занятие'
    )
    zoom_meeting_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Zoom Meeting ID'
    )
    zoom_join_url = models.URLField(
        blank=True,
        verbose_name='Ссылка для присоединения'
    )
    zoom_start_url = models.URLField(
        blank=True,
        verbose_name='Ссылка для старта'
    )
    meeting_password = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Пароль встречи'
    )
    recording_url = models.URLField(
        blank=True,
        verbose_name='Ссылка на запись'
    )
    recording_file = models.FileField(
        upload_to='recordings/',
        blank=True,
        null=True,
        verbose_name='Файл записи'
    )
    is_recording_enabled = models.BooleanField(
        default=False,
        verbose_name='Запись включена'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Видеоурок'
        verbose_name_plural = 'Видеоуроки'

# 2. Модель записей уроков
class LessonRecording(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='recordings',
        verbose_name='Занятие'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название записи'
    )
    file = models.FileField(
        upload_to='lesson_recordings/',
        verbose_name='Файл записи'
    )
    duration = models.DurationField(
        verbose_name='Длительность'
    )
    file_size = models.BigIntegerField(
        verbose_name='Размер файла (байты)'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Загрузил'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name='Публичная'
    )
    
    class Meta:
        verbose_name = 'Запись урока'
        verbose_name_plural = 'Записи уроков'

# 3. Модель участников встречи
class MeetingParticipant(models.Model):
    MEETING_ROLE_CHOICES = [
        ('host', 'Хост'),
        ('co_host', 'Ко-хост'),
        ('participant', 'Участник'),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='meeting_participants',
        verbose_name='Занятие'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    role = models.CharField(
        max_length=20,
        choices=MEETING_ROLE_CHOICES,
        default='participant',
        verbose_name='Роль'
    )
    joined_at = models.DateTimeField(
        verbose_name='Время присоединения'
    )
    left_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время выхода'
    )
    duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name='Длительность участия'
    )
    is_present = models.BooleanField(
        default=False,
        verbose_name='Присутствовал'
    )
    
    class Meta:
        verbose_name = 'Участник встречи'
        verbose_name_plural = 'Участники встречи'
        unique_together = ['lesson', 'user']

# === НОВЫЕ МОДЕЛИ ДЛЯ ДОПОЛНИТЕЛЬНЫХ ФУНКЦИЙ ===

# 1. Модель домашних заданий
class Homework(models.Model):
    HOMEWORK_STATUS_CHOICES = [
        ('assigned', 'Назначено'),
        ('submitted', 'Сдано'),
        ('graded', 'Оценено'),
        ('late', 'Сдано с опозданием'),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Занятие'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название задания'
    )
    description = models.TextField(
        verbose_name='Описание задания'
    )
    due_date = models.DateTimeField(
        verbose_name='Срок сдачи'
    )
    max_points = models.PositiveIntegerField(
        default=100,
        verbose_name='Максимальный балл'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['-created_at']

# 2. Модель сдачи домашнего задания
class HomeworkSubmission(models.Model):
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Домашнее задание'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='homework_submissions',
        verbose_name='Студент'
    )
    file = models.FileField(
        upload_to='homework_submissions/',
        blank=True,
        null=True,
        verbose_name='Файл задания'
    )
    text_content = models.TextField(
        blank=True,
        verbose_name='Текстовое задание'
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата сдачи'
    )
    grade = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Оценка'
    )
    feedback = models.TextField(
        blank=True,
        verbose_name='Комментарий преподавателя'
    )
    is_late = models.BooleanField(
        default=False,
        verbose_name='Сдано с опозданием'
    )
    
    class Meta:
        verbose_name = 'Сдача задания'
        verbose_name_plural = 'Сдачи заданий'
        unique_together = ['homework', 'student']
        ordering = ['-submitted_at']

# 3. Модель материалов урока
from django.db import models
from django.utils.translation import gettext_lazy as _

class LessonMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ('pdf', 'PDF документ'),
        ('doc', 'Документ'),
        ('ppt', 'Презентация'),
        ('video', 'Видео'),
        ('audio', 'Аудио'),
        ('image', 'Изображение'),
        ('link', 'Ссылка'),
        ('ai_trainer', 'ИИ-тренажёр'),
    ]

    lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name=_('Занятие')
    )
    title = models.CharField(max_length=255, verbose_name=_('Название материала'))
    material_type = models.CharField(
        max_length=20,
        choices=MATERIAL_TYPE_CHOICES,
        verbose_name=_('Тип материала')
    )
    file = models.FileField(
        upload_to='lesson_materials/',
        blank=True,
        null=True,
        verbose_name=_('Файл')
    )
    link = models.URLField(blank=True, null=True, verbose_name=_('Ссылка'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    is_required = models.BooleanField(default=False, verbose_name=_('Обязательный материал'))
    ai_trainer_session = models.ForeignKey(
        'ai_trainer.AITrainingSession',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Привязанный ИИ-тренажёр'),
        help_text=_('Выберите, если этот материал связан с конкретным AI тренажёром')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата загрузки'))
    ai_trainer_prompt = models.ForeignKey(
        'ai_trainer.AITrainerPrompt',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Промпт ИИ-тренажёра'),
        help_text=_('Позволяет выбрать конкретный промпт для данного материала'),
    )
    class Meta:
        verbose_name = _('Материал урока')
        verbose_name_plural = _('Материалы урока')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_material_type_display()})"

# 4. Модель достижений (улучшенная система бейджей)
class Achievement(models.Model):
    ACHIEVEMENT_TYPE_CHOICES = [
        ('completion', 'Завершение курса'),
        ('perfect_score', 'Идеальный результат'),
        ('attendance', 'Посещение'),
        ('homework', 'Домашние задания'),
        ('test', 'Тесты'),
        ('participation', 'Участие'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Название достижения')
    description = models.TextField(verbose_name='Описание')
    achievement_type = models.CharField(
        max_length=20,
        choices=ACHIEVEMENT_TYPE_CHOICES,
        verbose_name='Тип достижения'
    )
    icon = models.ImageField(
        upload_to='achievements/',
        blank=True,
        null=True,
        verbose_name='Иконка'
    )
    required_points = models.PositiveIntegerField(
        default=0,
        verbose_name='Необходимые баллы'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
    
    def __str__(self):
        return self.name

# 5. Привязка достижения к студенту
class StudentAchievement(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='achievements',
        verbose_name='Студент'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        verbose_name='Достижение'
    )
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата получения')
    earned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='awarded_achievements',
        verbose_name='Выдано преподавателем'
    )
    progress = models.PositiveIntegerField(
        default=0,
        verbose_name='Прогресс (%)'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    
    class Meta:
        verbose_name = 'Полученное достижение'
        verbose_name_plural = 'Полученные достижения'
        unique_together = ['student', 'achievement']

# 6. Модель тикетов поддержки
class SupportTicket(models.Model):
    TICKET_STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
        ('resolved', 'Решен'),
        ('closed', 'Закрыт'),
    ]
    
    TICKET_PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        verbose_name='Пользователь'
    )
    title = models.CharField(max_length=255, verbose_name='Тема')
    description = models.TextField(verbose_name='Описание проблемы')
    status = models.CharField(
        max_length=20,
        choices=TICKET_STATUS_CHOICES,
        default='new',
        verbose_name='Статус'
    )
    priority = models.CharField(
        max_length=10,
        choices=TICKET_PRIORITY_CHOICES,
        default='medium',
        verbose_name='Приоритет'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        verbose_name='Назначен администратору'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата решения')
    
    class Meta:
        verbose_name = 'Тикет поддержки'
        verbose_name_plural = 'Тикеты поддержки'
        ordering = ['-created_at']

# 7. Модель сообщений тикета
class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Тикет'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Отправитель'
    )
    content = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    
    class Meta:
        verbose_name = 'Сообщение тикета'
        verbose_name_plural = 'Сообщения тикетов'
        ordering = ['created_at']