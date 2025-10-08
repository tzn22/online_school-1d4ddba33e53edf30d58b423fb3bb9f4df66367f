from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from .models import AITrainingSession
from .serializers import AITrainingSessionSerializer, StartSessionSerializer, SubmitAnswersSerializer
from .services import AITrainerService


class StartTrainingSessionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StartSessionSerializer

    @swagger_auto_schema(
        operation_summary="Start AI trainer session — generate questions",
        request_body=StartSessionSerializer,
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
        operation_summary="Submit answers and receive evaluation",
        request_body=SubmitAnswersSerializer,
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
