from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Feedback, FeedbackResponse, Survey, SurveyQuestion, SurveyResponse
from accounts.models import User
from courses.models import Lesson, Course
from .serializers import (
    FeedbackSerializer, 
    FeedbackCreateSerializer,
    FeedbackResponseSerializer,
    SurveySerializer,
    SurveyQuestionSerializer,
    SurveyResponseSerializer,
    SubmitSurveySerializer
)
from .services import FeedbackService, SurveyService
from .permissions import IsFeedbackOwner, IsTeacherOrAdmin

class FeedbackListCreateView(generics.ListCreateAPIView):
    """Список отзывов и создание нового отзыва"""
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['feedback_type', 'status', 'rating', 'is_anonymous']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Feedback.objects.all()
        elif user.is_teacher:
            return Feedback.objects.filter(teacher=user)
        else:
            return Feedback.objects.filter(student=user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FeedbackCreateSerializer
        return FeedbackSerializer
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

class FeedbackDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали отзыва"""
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated, IsFeedbackOwner]

class FeedbackResponseListCreateView(generics.ListCreateAPIView):
    """Список ответов на отзывы и создание нового ответа"""
    serializer_class = FeedbackResponseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        feedback_id = self.kwargs['feedback_id']
        feedback = get_object_or_404(Feedback, id=feedback_id)
        
        # Проверяем права доступа
        user = self.request.user
        if not (user.is_admin or user == feedback.student or 
                (feedback.teacher and user == feedback.teacher)):
            return FeedbackResponse.objects.none()
        
        return FeedbackResponse.objects.filter(feedback=feedback)
    
    def perform_create(self, serializer):
        feedback_id = self.kwargs['feedback_id']
        feedback = get_object_or_404(Feedback, id=feedback_id)
        serializer.save(feedback=feedback, responder=self.request.user)

class SurveyListView(generics.ListAPIView):
    """Список опросов"""
    queryset = Survey.objects.filter(status='active')
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['target_audience']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

class SurveyDetailView(generics.RetrieveAPIView):
    """Детали опроса"""
    queryset = Survey.objects.filter(status__in=['active', 'closed'])
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated]

class SurveyResponseListCreateView(generics.ListCreateAPIView):
    """Список ответов на опросы и создание нового ответа"""
    serializer_class = SurveyResponseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        survey_id = self.kwargs['survey_id']
        return SurveyResponse.objects.filter(
            survey_id=survey_id,
            survey__status='active'
        )
    
    def perform_create(self, serializer):
        survey_id = self.kwargs['survey_id']
        survey = get_object_or_404(Survey, id=survey_id, status='active')
        serializer.save(survey=survey, respondent=self.request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_survey(request):
    """Отправка ответов на опрос"""
    serializer = SubmitSurveySerializer(data=request.data)
    if serializer.is_valid():
        try:
            survey_id = serializer.validated_data['survey_id']
            answers = serializer.validated_data['answers']
            
            survey = Survey.objects.get(id=survey_id, status='active')
            
            # Преобразуем ответы в нужный формат
            formatted_answers = {}
            for answer in answers:
                formatted_answers[str(answer['question_id'])] = answer['answer']
            
            # Отправляем ответы через сервис
            response = SurveyService.submit_survey_response(
                survey=survey,
                respondent=request.user,
                answers=formatted_answers
            )
            
            return Response({
                'message': 'Ответы на опрос успешно отправлены',
                'response_id': response.id
            })
        except Survey.DoesNotExist:
            return Response({
                'error': 'Опрос не найден или не активен'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_to_feedback(request, feedback_id):
    """Ответ на отзыв"""
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        
        # Проверяем права доступа
        user = request.user
        if not (user.is_admin or (feedback.teacher and user == feedback.teacher)):
            return Response({
                'error': 'Нет прав для ответа на этот отзыв'
            }, status=status.HTTP_403_FORBIDDEN)
        
        content = request.data.get('content', '')
        is_internal = request.data.get('is_internal', False)
        
        # Создаем ответ через сервис
        response = FeedbackService.respond_to_feedback(
            feedback=feedback,
            responder=user,
            content=content,
            is_internal=is_internal
        )
        
        serializer = FeedbackResponseSerializer(response)
        return Response({
            'message': 'Ответ успешно добавлен',
            'response': serializer.data
        })
        
    except Feedback.DoesNotExist:
        return Response({
            'error': 'Отзыв не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def resolve_feedback(request, feedback_id):
    """Решение отзыва"""
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        
        # Решаем отзыв через сервис
        resolved_feedback = FeedbackService.resolve_feedback(
            feedback=feedback,
            resolver=request.user
        )
        
        serializer = FeedbackSerializer(resolved_feedback)
        return Response({
            'message': 'Отзыв отмечен как решенный',
            'feedback': serializer.data
        })
        
    except Feedback.DoesNotExist:
        return Response({
            'error': 'Отзыв не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_feedback_statistics(request):
    """Получение статистики отзывов"""
    user = request.user
    
    if user.is_student:
        stats = FeedbackService.get_student_feedback_stats(user)
    elif user.is_teacher:
        stats = FeedbackService.get_teacher_feedback_stats(user)
    else:
        return Response({
            'error': 'Нет доступа к статистике'
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_survey_statistics(request, survey_id):
    """Получение статистики опроса (только для админов)"""
    if not request.user.is_admin:
        return Response({
            'error': 'Только администраторы могут просматривать статистику опросов'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        survey = Survey.objects.get(id=survey_id)
        stats = SurveyService.get_survey_statistics(survey)
        return Response(stats)
    except Survey.DoesNotExist:
        return Response({
            'error': 'Опрос не найден'
        }, status=status.HTTP_404_NOT_FOUND)