from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    register_user,
    UserProfileView,
    UserListView,
    UserDetailView,
    RegistrationProfileView,
    # === ПОЛНАЯ ЛОГИКА РЕГИСТРАЦИИ И ТЕСТИРОВАНИЯ ===
    get_registration_steps,
    get_survey_questions,
    submit_survey_answers,
    get_language_test,
    submit_test_answers,
    get_test_results,
    get_suitable_courses,
    select_course,
    get_consultation_form,
    request_consultation,
    get_user_dashboard,
    get_consultation_requests,
    mark_consultation_completed
)

urlpatterns = [
    # Аутентификация
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', register_user, name='user_register'),
    
    # Профиль
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('registration-profile/', RegistrationProfileView.as_view(), name='registration-profile'),
    
    # Пользователи
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    
    # === ПОЛНАЯ ЛОГИКА РЕГИСТРАЦИИ И ТЕСТИРОВАНИЯ ===
    # Регистрация и шаги
    path('registration/steps/', get_registration_steps, name='registration-steps'),
    path('registration/dashboard/', get_user_dashboard, name='user-dashboard'),
    
    # Опрос
    path('survey/questions/', get_survey_questions, name='survey-questions'),
    path('survey/answers/', submit_survey_answers, name='submit-survey-answers'),
    
    # Тестирование
    path('test/', get_language_test, name='language-test'),
    path('test/answers/', submit_test_answers, name='submit-test-answers'),
    path('test/results/', get_test_results, name='test-results'),
    
    # Курсы
    path('courses/suitable/', get_suitable_courses, name='suitable-courses'),
    path('courses/select/', select_course, name='select-course'),
    
    # Консультации
    path('consultation/form/', get_consultation_form, name='consultation-form'),
    path('consultation/request/', request_consultation, name='request-consultation'),
    path('consultation/requests/', get_consultation_requests, name='consultation-requests'),
    path('consultation/requests/<int:consultation_id>/complete/', mark_consultation_completed, name='mark-consultation-completed'),
]