from django.urls import path
from .views import StartTrainingSessionView, SubmitAnswersView

urlpatterns = [
    path('trainer/start/', StartTrainingSessionView.as_view(), name='ai-trainer-start'),
    path('trainer/submit/', SubmitAnswersView.as_view(), name='ai-trainer-submit'),
]
