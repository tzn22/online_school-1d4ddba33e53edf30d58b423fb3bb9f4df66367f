from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import AITrainingSession
from .serializers import AITrainingSessionSerializer
from .filters import AITrainingSessionFilter
from .services import AITrainerService
from .serializers import StartSessionSerializer, SubmitAnswersSerializer


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
    """
    Получить список сессий с фильтрацией по пользователю, уровню, дате, статусу.
    """
    queryset = AITrainingSession.objects.all()
    serializer_class = AITrainingSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AITrainingSessionFilter
