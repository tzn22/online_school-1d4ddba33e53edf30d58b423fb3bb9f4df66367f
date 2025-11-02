from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import AITrainingSession, AITrainerPrompt
from courses.models import LessonMaterial
from .serializers import (
    AITrainingSessionSerializer,
    StartSessionSerializer,
    SubmitAnswersSerializer,
    AITrainerPromptSerializer
)
from .filters import AITrainingSessionFilter
from .services import AITrainerService


# ===== Сессии AI-тренажера =====

class StartTrainingSessionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StartSessionSerializer

    @swagger_auto_schema(
        operation_summary="Начать сессию AI тренера — сгенерировать вопросы",
        responses={201: AITrainingSessionSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        level = serializer.validated_data.get('level', 'intermediate')
        count = serializer.validated_data.get('count', 5)

        questions = AITrainerService.generate_questions(level=level, count=count)
        session = AITrainingSession.objects.create(user=request.user, questions=questions)

        return Response(AITrainingSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class SubmitAnswersView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubmitAnswersSerializer

    @swagger_auto_schema(
        operation_summary="Отправить ответы и получить оценку",
        responses={200: AITrainingSessionSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data['session_id']
        answers = serializer.validated_data['answers']

        session = get_object_or_404(AITrainingSession, id=session_id, user=request.user)
        session.answers = answers

        evaluation = AITrainerService.evaluate_answers(session.questions, answers)
        session.evaluation = evaluation
        session.level = evaluation.get('overall_level') if isinstance(evaluation, dict) else None
        session.completed = True
        session.save()

        return Response(AITrainingSessionSerializer(session).data, status=status.HTTP_200_OK)


class AITrainingSessionListView(generics.ListAPIView):
    queryset = AITrainingSession.objects.all()
    serializer_class = AITrainingSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AITrainingSessionFilter


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_ai_trainer(request, lesson_material_id):
    material = get_object_or_404(LessonMaterial, id=lesson_material_id)

    level = request.data.get('level', 'intermediate')
    count = int(request.data.get('count', 5))

    questions = AITrainerService.generate_questions(level=level, count=count)

    session = AITrainingSession.objects.create(user=request.user, questions=questions)

    material.ai_trainer_session = session
    material.material_type = 'ai_trainer'
    material.save()

    return Response(AITrainingSessionSerializer(session).data, status=status.HTTP_201_CREATED)


# ===== Промпты для AI-тренажеров =====

class AITrainerPromptListView(generics.ListCreateAPIView):
    queryset = AITrainerPrompt.objects.all()
    serializer_class = AITrainerPromptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['course', 'lesson', 'is_active']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AITrainerPromptDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AITrainerPrompt.objects.all()
    serializer_class = AITrainerPromptSerializer
    permission_classes = [IsAuthenticated]
