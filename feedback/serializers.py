from rest_framework import serializers
from .models import Feedback, FeedbackResponse, Survey, SurveyQuestion, SurveyResponse
from accounts.models import User
from courses.models import Lesson, Course

class FeedbackSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True, allow_null=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True, allow_null=True)
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)
    
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['student', 'created_at', 'updated_at', 'resolved_at']
    
    def validate_rating(self, value):
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError('Оценка должна быть от 1 до 5')
        return value

class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            'lesson', 'teacher', 'course', 'feedback_type', 
            'title', 'content', 'rating', 'is_anonymous'
        ]
    
    def validate(self, attrs):
        feedback_type = attrs.get('feedback_type')
        lesson = attrs.get('lesson')
        teacher = attrs.get('teacher')
        course = attrs.get('course')
        
        # Проверка соответствия типа и связанных объектов
        if feedback_type == 'lesson' and not lesson:
            raise serializers.ValidationError({
                'lesson': 'Для отзыва о занятии необходимо указать занятие'
            })
        
        if feedback_type == 'teacher' and not teacher:
            raise serializers.ValidationError({
                'teacher': 'Для отзыва о преподавателе необходимо указать преподавателя'
            })
        
        if feedback_type == 'course' and not course:
            raise serializers.ValidationError({
                'course': 'Для отзыва о курсе необходимо указать курс'
            })
        
        return attrs

class FeedbackResponseSerializer(serializers.ModelSerializer):
    responder_name = serializers.CharField(source='responder.get_full_name', read_only=True)
    
    class Meta:
        model = FeedbackResponse
        fields = '__all__'
        read_only_fields = ['responder', 'created_at']

class SurveyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyQuestion
        fields = '__all__'

class SurveySerializer(serializers.ModelSerializer):
    questions = SurveyQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Survey
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class SurveyQuestionAnswerSerializer(serializers.Serializer):
    """Сериализатор для ответов на вопросы опроса"""
    question_id = serializers.IntegerField()
    answer = serializers.JSONField()

class SurveyResponseSerializer(serializers.ModelSerializer):
    respondent_name = serializers.CharField(source='respondent.get_full_name', read_only=True)
    
    class Meta:
        model = SurveyResponse
        fields = '__all__'
        read_only_fields = ['respondent', 'submitted_at']

class SubmitSurveySerializer(serializers.Serializer):
    """Сериализатор для отправки ответов на опрос"""
    survey_id = serializers.IntegerField()
    answers = SurveyQuestionAnswerSerializer(many=True)