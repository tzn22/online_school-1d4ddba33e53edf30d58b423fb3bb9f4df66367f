from django.db import models
from django.conf import settings


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
