from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Feedback(models.Model):
    FEEDBACK_TYPE_CHOICES = [
        ('lesson', _('Отзыв о занятии')),
        ('teacher', _('Отзыв о преподавателе')),
        ('course', _('Отзыв о курсе')),
        ('platform', _('Отзыв о платформе')),
        ('technical', _('Техническая поддержка')),
        ('other', _('Другое')),
    ]
    
    FEEDBACK_STATUS_CHOICES = [
        ('new', _('Новый')),
        ('in_progress', _('В работе')),
        ('resolved', _('Решен')),
        ('closed', _('Закрыт')),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Студент')
    )
    lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.CASCADE,
        related_name='feedbacks',
        null=True,
        blank=True,
        verbose_name=_('Занятие')
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_feedbacks',
        limit_choices_to={'role': 'teacher'},
        null=True,
        blank=True,
        verbose_name=_('Преподаватель')
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='feedbacks',
        null=True,
        blank=True,
        verbose_name=_('Курс')
    )
    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_TYPE_CHOICES,
        default='lesson',
        verbose_name=_('Тип обратной связи')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Заголовок')
    )
    content = models.TextField(
        verbose_name=_('Содержание')
    )
    rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        null=True,
        blank=True,
        verbose_name=_('Оценка')
    )
    status = models.CharField(
        max_length=20,
        choices=FEEDBACK_STATUS_CHOICES,
        default='new',
        verbose_name=_('Статус')
    )
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name=_('Анонимный отзыв')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата решения')
    )
    
    class Meta:
        verbose_name = _('Обратная связь')
        verbose_name_plural = _('Обратная связь')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'created_at']),
            models.Index(fields=['feedback_type', 'status']),
            models.Index(fields=['lesson']),
            models.Index(fields=['teacher']),
        ]
    
    def __str__(self):
        return f"Отзыв от {self.student} - {self.title}"

class FeedbackResponse(models.Model):
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_('Обратная связь')
    )
    responder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedback_responses',
        verbose_name=_('Ответивший')
    )
    content = models.TextField(
        verbose_name=_('Ответ')
    )
    is_internal = models.BooleanField(
        default=False,
        verbose_name=_('Внутренний комментарий')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата ответа')
    )
    
    class Meta:
        verbose_name = _('Ответ на обратную связь')
        verbose_name_plural = _('Ответы на обратную связь')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Ответ на {self.feedback.title}"

class Survey(models.Model):
    SURVEY_STATUS_CHOICES = [
        ('draft', _('Черновик')),
        ('active', _('Активен')),
        ('closed', _('Закрыт')),
    ]
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('Название опроса')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    target_audience = models.CharField(
        max_length=20,
        choices=[
            ('all', _('Все пользователи')),
            ('students', _('Студенты')),
            ('teachers', _('Преподаватели')),
            ('parents', _('Родители')),
        ],
        default='all',
        verbose_name=_('Целевая аудитория')
    )
    status = models.CharField(
        max_length=10,
        choices=SURVEY_STATUS_CHOICES,
        default='draft',
        verbose_name=_('Статус')
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала')
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания')
    )
    is_anonymous = models.BooleanField(
        default=True,
        verbose_name=_('Анонимный опрос')
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
        verbose_name = _('Опрос')
        verbose_name_plural = _('Опросы')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class SurveyQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('text', _('Текстовый ответ')),
        ('single_choice', _('Один выбор')),
        ('multiple_choice', _('Множественный выбор')),
        ('rating', _('Оценка')),
        ('yes_no', _('Да/Нет')),
    ]
    
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Опрос')
    )
    question_text = models.TextField(
        verbose_name=_('Текст вопроса')
    )
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='text',
        verbose_name=_('Тип вопроса')
    )
    options = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Варианты ответов')
    )
    is_required = models.BooleanField(
        default=True,
        verbose_name=_('Обязательный вопрос')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Порядок')
    )
    
    class Meta:
        verbose_name = _('Вопрос опроса')
        verbose_name_plural = _('Вопросы опроса')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.survey.title} - {self.question_text[:50]}..."

class SurveyResponse(models.Model):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_('Опрос')
    )
    respondent = models.ForeignKey(  # Изменили related_name
        User,
        on_delete=models.CASCADE,
        related_name='feedback_survey_responses',  # Изменили related_name
        null=True,
        blank=True,
        verbose_name=_('Респондент')
    )
    answers = models.JSONField(
        default=dict,
        verbose_name=_('Ответы')
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата отправки')
    )
    
    class Meta:
        verbose_name = _('Ответ на опрос')
        verbose_name_plural = _('Ответы на опросы')
        ordering = ['-submitted_at']
        unique_together = ['survey', 'respondent']
    
    def __str__(self):
        respondent_name = self.respondent.get_full_name() if self.respondent else 'Аноним'
        return f"Ответ на {self.survey.title} от {respondent_name}"