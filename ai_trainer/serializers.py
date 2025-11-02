from rest_framework import serializers
from .models import AITrainingSession, AITrainerPrompt
from courses.models import Course, Lesson


# ===== Сериализаторы сессий AI-тренажера =====
class AITrainingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITrainingSession
        fields = [
            'id',
            'user',
            'prompt',
            'course',
            'lesson',
            'questions',
            'answers',
            'evaluation',
            'level',
            'completed',
            'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'evaluation', 'level', 'completed', 'created_at'
        ]


class StartSessionSerializer(serializers.Serializer):
    level = serializers.ChoiceField(
        choices=['beginner', 'elementary', 'intermediate', 'upper_intermediate', 'advanced'],
        required=False,
        default='intermediate'
    )
    count = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)


class SubmitAnswersSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    # answers as map of question id (string or int) -> answer string
    answers = serializers.DictField(child=serializers.CharField())


# ===== Сериализаторы промптов AI-тренажера =====
class AITrainerPromptSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), required=False, allow_null=True)
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all(), required=False, allow_null=True)

    class Meta:
        model = AITrainerPrompt
        fields = [
            'id',
            'title',
            'description',
            'prompt_text',
            'course',
            'lesson',
            'is_active',
            'created_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
