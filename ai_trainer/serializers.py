from rest_framework import serializers
from .models import AITrainingSession


class AITrainingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITrainingSession
        fields = ['id', 'user', 'questions', 'answers', 'evaluation', 'level', 'completed', 'created_at']
        read_only_fields = ['id', 'user', 'evaluation', 'level', 'completed', 'created_at']


class StartSessionSerializer(serializers.Serializer):
    level = serializers.ChoiceField(choices=['beginner', 'elementary', 'intermediate', 'upper_intermediate', 'advanced'],
                                    required=False, default='intermediate')
    count = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)


class SubmitAnswersSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    # answers as map of question id (string or int) -> answer string
    answers = serializers.DictField(child=serializers.CharField())
