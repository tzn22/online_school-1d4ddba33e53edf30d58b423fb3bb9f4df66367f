from django.db import models
from django.conf import settings

class AITrainerPrompt(models.Model):
    """Хранит шаблоны промптов для ИИ-тренажёров."""
    title = models.CharField(max_length=255, verbose_name='Название промпта')
    description = models.TextField(blank=True, verbose_name='Описание')
    prompt_text = models.TextField(verbose_name='Текст промпта')
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_prompts',
        verbose_name='Курс (опционально)',
    )
    lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_prompts',
        verbose_name='Урок (опционально)',
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создан пользователем',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Промпт для ИИ-тренажёра'
        verbose_name_plural = 'Промпты для ИИ-тренажёров'
        ordering = ['-created_at']

    def __str__(self):
        base = f"{self.title}"
        if self.lesson:
            base += f" (урок: {self.lesson.title})"
        elif self.course:
            base += f" (курс: {self.course.title})"
        return base

class AITrainingSession(models.Model):
    """
    Сессия теста: вопросы, ответы, результат.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_sessions'
    )
    questions = models.JSONField(default=list, blank=True)
    answers = models.JSONField(default=dict, blank=True)
    evaluation = models.JSONField(default=dict, blank=True)
    level = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "AI тренажер"
        verbose_name_plural = "AI тренажер"

    def __str__(self):
        username = getattr(self.user, 'username', str(self.user))
        return f"AITrainingSession {self.pk} for {username}"
class AITrainingSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_sessions'
    )
    prompt = models.ForeignKey(
        'ai_trainer.AITrainerPrompt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        verbose_name='Использованный промпт'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_sessions',
        verbose_name='Курс'
    )
    lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_sessions',
        verbose_name='Урок'
    )
    questions = models.JSONField(default=list, blank=True)
    answers = models.JSONField(default=dict, blank=True)
    evaluation = models.JSONField(default=dict, blank=True)
    level = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Сессия ИИ-тренажёра"
        verbose_name_plural = "Сессии ИИ-тренажёров"

    def __str__(self):
        username = getattr(self.user, 'username', str(self.user))
        return f"Сессия {self.pk} ({username})"
