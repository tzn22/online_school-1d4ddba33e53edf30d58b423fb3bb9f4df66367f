# ai_trainer/urls.py
from django.urls import path
from . import views

app_name = 'ai_trainer'

urlpatterns = [
    # API / Admin actions
    path('generate/<int:lesson_material_id>/', views.generate_ai_trainer, name='generate_ai_trainer'),
    path('session/<int:pk>/', views.AITrainingSessionListView.as_view(), name='ai_session_detail'),
    path('prompts/', views.AITrainerPromptListView.as_view(), name='prompt_list'),
    path('prompts/<int:pk>/', views.AITrainerPromptDetailView.as_view(), name='prompt_detail'),
]
