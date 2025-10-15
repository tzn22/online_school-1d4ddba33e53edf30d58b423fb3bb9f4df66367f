from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, RegistrationProfile, SurveyQuestion, SurveyOption, SurveyResponse, LanguageTest, TestQuestion, TestOption, TestResult, ConsultationRequest

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    children = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'birth_date', 'phone', 'avatar', 'parent',
            'has_studied_language', 'password', 'children', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        """Получить список детей для родителя"""
        if obj.role == 'parent':
            children_data = []
            for child in obj.children.all():
                children_data.append({
                    'id': child.id,
                    'username': child.username,
                    'first_name': child.first_name,
                    'last_name': child.last_name,
                    'birth_date': child.birth_date
                })
            return children_data
        return []
    
    def validate_password(self, value):
        if value:
            try:
                validate_password(value)
            except ValidationError as e:
                raise serializers.ValidationError(e.messages)
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    has_studied_language = serializers.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'password', 'password_confirm', 'role', 'birth_date',
            'phone', 'has_studied_language'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs
    
    def validate_role(self, value):
        # Ограничиваем доступные роли при регистрации
        if value not in ['student', 'parent']:
            raise serializers.ValidationError("Недопустимая роль при регистрации")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        has_studied_language = validated_data.pop('has_studied_language', False)
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.has_studied_language = has_studied_language
        user.save()
        
        # Создаем профиль регистрации
        RegistrationProfile.objects.create(user=user)
        
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Добавляем пользовательские поля в токен
        token['username'] = user.username
        token['role'] = user.role
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['has_studied_language'] = user.has_studied_language
        return token

class UserProfileSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'birth_date', 'phone', 'avatar', 'has_studied_language',
            'children', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'role', 'created_at']
    
    def get_children(self, obj):
        if obj.role == 'parent':
            return UserSerializer(obj.children.all(), many=True).data
        return []

# === СЕРИАЛИЗАТОРЫ ДЛЯ РЕГИСТРАЦИИ И ОПРОСА ===

class RegistrationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class SurveyOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyOption
        fields = ['id', 'option_text', 'value']

class SurveyQuestionSerializer(serializers.ModelSerializer):
    options = SurveyOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = SurveyQuestion
        fields = ['id', 'question_text', 'question_type', 'is_required', 'order', 'options']

class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = ['id', 'user', 'question', 'selected_options', 'text_answer', 'created_at']
        read_only_fields = ['user', 'created_at']

class TestOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestOption
        fields = ['id', 'option_text', 'is_correct']

from rest_framework import serializers
from .models import TestQuestion

class TestQuestionSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = TestQuestion
        fields = ['id', 'test', 'question_text', 'image', 'question_type', 'correct_answer', 'points']


class LanguageTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageTest
        fields = ['id', 'title', 'description', 'duration_minutes', 'is_active']

class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = ['id', 'user', 'test', 'score', 'total_points', 'percentage', 'level', 'completed_at']
        read_only_fields = ['user', 'completed_at']

class ConsultationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationRequest
        fields = ['id', 'user', 'name', 'phone', 'email', 'language_level', 'message', 'status', 'requested_at', 'contacted_at']
        read_only_fields = ['user', 'requested_at', 'contacted_at', 'status']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['name'] = user.get_full_name() or user.username
        validated_data['phone'] = user.phone
        validated_data['email'] = user.email
        
        # Попробуем получить уровень из результатов теста
        latest_test_result = TestResult.objects.filter(user=user).order_by('-completed_at').first()
        if latest_test_result:
            validated_data['language_level'] = latest_test_result.level
        
        return super().create(validated_data)