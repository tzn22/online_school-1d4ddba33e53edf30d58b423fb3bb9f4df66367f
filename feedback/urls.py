from django.urls import path
from .views import (
    FeedbackListCreateView,
    FeedbackDetailView,
    FeedbackResponseListCreateView,
    SurveyListView,
    SurveyDetailView,
    SurveyResponseListCreateView,
    submit_survey,
    respond_to_feedback,
    resolve_feedback,
    get_feedback_statistics,
    get_survey_statistics
)

urlpatterns = [
    # Отзывы
    path('feedback/', FeedbackListCreateView.as_view(), name='feedback-list'),
    path('feedback/<int:pk>/', FeedbackDetailView.as_view(), name='feedback-detail'),
    path('feedback/<int:feedback_id>/responses/', FeedbackResponseListCreateView.as_view(), name='feedback-responses'),
    path('feedback/<int:feedback_id>/respond/', respond_to_feedback, name='respond-to-feedback'),
    path('feedback/<int:feedback_id>/resolve/', resolve_feedback, name='resolve-feedback'),
    
    # Статистика
    path('feedback/statistics/', get_feedback_statistics, name='feedback-statistics'),
    
    # Опросы
    path('surveys/', SurveyListView.as_view(), name='survey-list'),
    path('surveys/<int:pk>/', SurveyDetailView.as_view(), name='survey-detail'),
    path('surveys/<int:survey_id>/responses/', SurveyResponseListCreateView.as_view(), name='survey-responses'),
    path('surveys/submit/', submit_survey, name='submit-survey'),
    path('surveys/<int:survey_id>/statistics/', get_survey_statistics, name='survey-statistics'),
]