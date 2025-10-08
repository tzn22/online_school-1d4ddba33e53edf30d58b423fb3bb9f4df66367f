from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class AITrainingSession(models.Model):
    """
    Сессия теста: вопросы, ответы, результат.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_sessions')
    # questions: list of {"id": int, "question": str}
    questions = models.JSONField(default=list, blank=True)
    # answers: dict {"1": "answer text", ...}
    answers = models.JSONField(default=dict, blank=True)
    # evaluation: dict with per-answer feedback and overall summary
    evaluation = models.JSONField(default=dict, blank=True)
    # extracted overall level (A1..C2)
    level = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AITrainingSession {self.pk} for {self.user}"
