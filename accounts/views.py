from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import User, RegistrationProfile, SurveyQuestion, SurveyOption, SurveyResponse, LanguageTest, TestQuestion, TestOption, TestResult, ConsultationRequest
from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer, 
    UserProfileSerializer,
    RegistrationProfileSerializer,
    SurveyQuestionSerializer,
    SurveyResponseSerializer,
    LanguageTestSerializer,
    TestQuestionSerializer,
    TestResultSerializer,
    ConsultationRequestSerializer
)
from courses.models import Course
from courses.serializers import CourseSerializer

User = get_user_model()

# === АУТЕНТИФИКАЦИЯ ===

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

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Регистрация нового пользователя"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Отправляем приветственное письмо если не изучал язык
        if not user.has_studied_language:
            send_welcome_email_with_credentials(user)
        
        return Response({
            'message': 'Пользователь успешно зарегистрирован',
            'user': UserSerializer(user).data,
            'has_studied_language': user.has_studied_language
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def send_welcome_email_with_credentials(user):
    """Отправка приветственного письма с данными для входа"""
    if user.email:
        try:
            subject = 'Добро пожаловать в онлайн-школу!'
            message = f'''
            Здравствуйте, {user.get_full_name() or user.username}!
            
            Спасибо за регистрацию в нашей онлайн-школе.
            Ваши учетные данные:
            Логин: {user.username}
            Роль: {user.get_role_display()}
            
            Пожалуйста, заполните опрос для подбора подходящего курса.
            
            С уважением,
            Команда онлайн-школы
            '''
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Ошибка отправки email: {e}")

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Просмотр и редактирование профиля пользователя"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    """Список всех пользователей (только для администраторов)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_admin:
            return User.objects.all()
        return User.objects.none()

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали пользователя"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class RegistrationProfileView(generics.RetrieveUpdateAPIView):
    """Профиль регистрации пользователя"""
    serializer_class = RegistrationProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        profile, created = RegistrationProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile

# === ПОЛНАЯ ЛОГИКА ТЕСТИРОВАНИЯ ===

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_registration_steps(request):
    """Получить текущий шаг регистрации пользователя"""
    user = request.user
    
    steps = {
        'registration_complete': True,
        'survey_complete': False,
        'test_assigned': False,
        'test_complete': False,
        'courses_selected': False,
        'payment_complete': False
    }
    
    # Проверяем, есть ли ответы на опрос
    survey_responses = SurveyResponse.objects.filter(user=user)
    if survey_responses.exists():
        steps['survey_complete'] = True
    
    # Проверяем, есть ли результаты теста
    test_results = TestResult.objects.filter(user=user)
    if test_results.exists():
        steps['test_complete'] = True
        steps['courses_selected'] = True  # После теста можно выбирать курсы
    
    # Проверяем, есть ли оплаченные курсы
    from payments.models import Payment
    paid_payments = Payment.objects.filter(student=user, status='paid')
    if paid_payments.exists():
        steps['payment_complete'] = True
    
    return Response(steps)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_survey_questions(request):
    """Получить вопросы опроса для пользователя"""
    user = request.user
    
    # Получаем вопросы опроса
    questions = SurveyQuestion.objects.all().order_by('order')
    serializer = SurveyQuestionSerializer(questions, many=True)
    
    # Получаем уже данные пользователя для автозаполнения
    user_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone,
        'birth_date': user.birth_date,
        'role': user.role,
        'has_studied_language': user.has_studied_language
    }
    
    return Response({
        'questions': serializer.data,
        'user_data': user_data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_survey_answers(request):
    """Сохранить ответы на опрос"""
    user = request.user
    answers = request.data.get('answers', [])
    
    try:
        with transaction.atomic():
            # Сохраняем ответы
            for answer_data in answers:
                question_id = answer_data.get('question_id')
                selected_options = answer_data.get('selected_options', [])
                text_answer = answer_data.get('text_answer', '')
                
                question = SurveyQuestion.objects.get(id=question_id)
                
                # Создаем или обновляем ответ
                survey_response, created = SurveyResponse.objects.update_or_create(
                    user=user,
                    question=question,
                    defaults={
                        'text_answer': text_answer
                    }
                )
                
                # Добавляем выбранные варианты
                if selected_options:
                    options = SurveyOption.objects.filter(id__in=selected_options)
                    survey_response.selected_options.set(options)
            
            # Обновляем профиль регистрации
            profile, created = RegistrationProfile.objects.get_or_create(user=user)
            profile.goals = "Цели собраны через опрос"
            profile.save()
            
        return Response({
            'message': 'Ответы на опрос сохранены',
            'next_step': 'test_assignment' if user.has_studied_language else 'course_selection'
        })
        
    except SurveyQuestion.DoesNotExist:
        return Response(
            {'error': 'Вопрос не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_language_test(request):
    """Получить языковой тест для пользователя"""
    user = request.user
    
    # Получаем активный тест
    test = LanguageTest.objects.filter(is_active=True).first()
    if not test:
        return Response(
            {'error': 'Активный тест не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Если пользователь ранее не изучал язык, предлагаем начальный тест
    if not user.has_studied_language:
        # Создаем упрощенный тест или возвращаем сообщение
        return Response({
            'message': 'Так как вы ранее не изучали язык, мы подберем для вас начальный курс',
            'test': None,
            'recommended_level': 'beginner'
        })
    
    # Получаем вопросы теста
    questions = test.questions.all()
    serializer = TestQuestionSerializer(questions, many=True)
    
    return Response({
        'test': LanguageTestSerializer(test).data,
        'questions': serializer.data,
        'duration_minutes': test.duration_minutes,
        'total_questions': questions.count()
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_test_answers(request):
    """Сдать ответы на тест и получить результаты"""
    user = request.user
    answers = request.data.get('answers', [])
    
    try:
        # Получаем тест
        test = LanguageTest.objects.filter(is_active=True).first()
        if not test:
            return Response(
                {'error': 'Активный тест не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Проверяем, что тест еще не пройден этим пользователем сегодня
        today = timezone.now().date()
        existing_result = TestResult.objects.filter(
            user=user,
            test=test,
            completed_at__date=today
        ).first()
        
        if existing_result:
            return Response({
                'message': 'Вы уже прошли этот тест сегодня',
                'result': TestResultSerializer(existing_result).data
            })
        
        # Подсчитываем баллы
        total_points = 0
        earned_points = 0
        correct_answers = 0
        total_questions = len(answers)
        
        # Проверяем каждый ответ
        for answer_data in answers:
            question_id = answer_data.get('question_id')
            selected_answer = answer_data.get('selected_answer')
            
            try:
                question = TestQuestion.objects.get(id=question_id, test=test)
                total_points += question.points
                
                # Проверяем правильность ответа
                if str(selected_answer).strip().lower() == str(question.correct_answer).strip().lower():
                    earned_points += question.points
                    correct_answers += 1
                    
            except TestQuestion.DoesNotExist:
                continue  # Пропускаем несуществующие вопросы
        
        # Рассчитываем процент
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        
        # Определяем уровень
        if percentage >= 90:
            level = 'proficient'
            level_name = 'Владение на уровне носителя'
        elif percentage >= 80:
            level = 'advanced'
            level_name = 'Продвинутый'
        elif percentage >= 70:
            level = 'upper_intermediate'
            level_name = 'Выше среднего'
        elif percentage >= 60:
            level = 'intermediate'
            level_name = 'Средний'
        elif percentage >= 50:
            level = 'elementary'
            level_name = 'Элементарный'
        else:
            level = 'beginner'
            level_name = 'Начальный'
        
        # Сохраняем результат
        test_result = TestResult.objects.create(
            user=user,
            test=test,
            score=earned_points,
            total_points=total_points,
            percentage=percentage,
            level=level
        )
        
        # Подбираем подходящие курсы
        suitable_courses = Course.objects.filter(level=level, is_active=True)[:5]  # Первые 5 курсов
        
        courses_data = []
        for course in suitable_courses:
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'level': course.get_level_display(),
                'price': float(course.price),
                'duration_hours': course.duration_hours
            })
        
        return Response({
            'message': 'Тест успешно завершен',
            'result': TestResultSerializer(test_result).data,
            'level_name': level_name,
            'suitable_courses': courses_data,
            'next_step': 'course_selection'
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_test_results(request):
    """Получить результаты тестов пользователя"""
    user = request.user
    
    results = TestResult.objects.filter(user=user).order_by('-completed_at')
    serializer = TestResultSerializer(results, many=True)
    
    return Response({
        'results': serializer.data,
        'count': results.count()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suitable_courses(request):
    """Получить подходящие курсы на основе последнего теста"""
    user = request.user
    
    # Получаем последний результат теста
    latest_result = TestResult.objects.filter(user=user).order_by('-completed_at').first()
    
    if latest_result:
        # Подбираем курсы по уровню
        courses = Course.objects.filter(level=latest_result.level, is_active=True)
    else:
        # Если нет теста, показываем все активные курсы
        courses = Course.objects.filter(is_active=True)
    
    serializer = CourseSerializer(courses, many=True)
    
    return Response({
        'courses': serializer.data,
        'test_result': TestResultSerializer(latest_result).data if latest_result else None
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_course(request):
    """Выбрать курс после прохождения теста"""
    user = request.user
    course_id = request.data.get('course_id')
    
    try:
        course = Course.objects.get(id=course_id, is_active=True)
        
        # Проверяем, есть ли результат теста
        test_result = TestResult.objects.filter(user=user).order_by('-completed_at').first()
        
        if test_result:
            # Проверяем соответствие уровня курса и результата теста
            if course.level != test_result.level:
                return Response({
                    'warning': 'Выбранный курс может не соответствовать вашему уровню',
                    'course': CourseSerializer(course).data,
                    'test_level': test_result.level,
                    'course_level': course.level
                })
        
        return Response({
            'message': 'Курс выбран',
            'course': CourseSerializer(course).data,
            'next_step': 'schedule_selection'
        })
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Курс не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consultation_form(request):
    """Получить форму запроса консультации"""
    user = request.user
    
    # Получаем данные пользователя для автозаполнения
    user_data = {
        'name': user.get_full_name() or user.username,
        'phone': user.phone,
        'email': user.email
    }
    
    # Получаем последний результат теста для указания уровня
    test_result = TestResult.objects.filter(user=user).order_by('-completed_at').first()
    if test_result:
        user_data['language_level'] = test_result.level
    
    return Response({
        'user_data': user_data,
        'test_result': TestResultSerializer(test_result).data if test_result else None
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_consultation(request):
    """Запросить бесплатную консультацию"""
    user = request.user
    serializer = ConsultationRequestSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        consultation = serializer.save()
        
        # Отправляем уведомление администраторам
        from django.core.mail import send_mail
        from django.conf import settings
        
        admin_users = User.objects.filter(role='admin')
        for admin in admin_users:
            if admin.email:
                try:
                    subject = f'Новый запрос консультации от {consultation.name}'
                    message = f'''
                    Уважаемый администратор!
                    
                    Получен новый запрос консультации:
                    Имя: {consultation.name}
                    Email: {consultation.email}
                    Телефон: {consultation.phone}
                    Уровень языка: {consultation.language_level or 'Не указан'}
                    Сообщение: {consultation.message or 'Нет сообщения'}
                    
                    Пожалуйста, свяжитесь с клиентом в ближайшее время.
                    
                    С уважением,
                    Система уведомлений
                    '''
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [admin.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Ошибка отправки email админу: {e}")
        
        return Response({
            'message': 'Запрос консультации отправлен',
            'consultation': ConsultationRequestSerializer(consultation).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def calculate_course_recommendation(user):
    """Рассчитать рекомендации курсов для пользователя"""
    # Получаем последний результат теста
    test_result = TestResult.objects.filter(user=user).order_by('-completed_at').first()
    
    if test_result:
        # Рекомендуем курсы по уровню
        courses = Course.objects.filter(level=test_result.level, is_active=True)[:5]
    else:
        # Если нет теста, рекомендуем начальные курсы
        courses = Course.objects.filter(level='beginner', is_active=True)[:5]
    
    return courses

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_dashboard(request):
    """Получить дашборд пользователя"""
    user = request.user
    
    # Получаем текущий шаг регистрации
    registration_steps = get_registration_steps(request._request).data
    
    # Получаем результаты теста
    latest_test = TestResult.objects.filter(user=user).order_by('-completed_at').first()
    
    # Получаем курсы
    if latest_test:
        courses = Course.objects.filter(level=latest_test.level, is_active=True)[:3]
    else:
        courses = Course.objects.filter(is_active=True)[:3]
    
    # Получаем оплаченные курсы
    from payments.models import Payment
    paid_courses = Payment.objects.filter(
        student=user, 
        status='paid'
    ).select_related('course')
    
    dashboard_data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'email': user.email,
            'role': user.get_role_display(),
            'has_studied_language': user.has_studied_language
        },
        'registration_steps': registration_steps,
        'latest_test_result': TestResultSerializer(latest_test).data if latest_test else None,
        'recommended_courses': CourseSerializer(courses, many=True).data,
        'enrolled_courses': [
            {
                'id': payment.course.id,
                'title': payment.course.title,
                'price': float(payment.course.price),
                'level': payment.course.get_level_display(),
                'paid_at': payment.paid_at
            }
            for payment in paid_courses
        ],
        'next_step': determine_next_step(user)
    }
    
    return Response(dashboard_data)

def determine_next_step(user):
    """Определить следующий шаг для пользователя"""
    # Проверяем, есть ли ответы на опрос
    survey_responses = SurveyResponse.objects.filter(user=user)
    
    # Проверяем, есть ли результаты теста
    test_results = TestResult.objects.filter(user=user)
    
    # Проверяем, есть ли оплаченные курсы
    from payments.models import Payment
    paid_payments = Payment.objects.filter(student=user, status='paid')
    
    if not survey_responses.exists():
        return 'complete_survey'
    elif user.has_studied_language and not test_results.exists():
        return 'take_test'
    elif not paid_payments.exists():
        return 'select_course'
    else:
        return 'view_courses'

# === API ДЛЯ АДМИНИСТРАТОРОВ ===

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consultation_requests(request):
    """Получить список запросов консультаций (для администраторов)"""
    user = request.user
    
    if not user.is_admin:
        return Response(
            {'error': 'Только администраторы могут просматривать запросы консультаций'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    consultations = ConsultationRequest.objects.all().order_by('-requested_at')
    serializer = ConsultationRequestSerializer(consultations, many=True)
    
    return Response({
        'consultations': serializer.data,
        'count': consultations.count()
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_consultation_completed(request, consultation_id):
    """Отметить консультацию как завершенную (для администраторов)"""
    user = request.user
    
    if not user.is_admin:
        return Response(
            {'error': 'Только администраторы могут завершать консультации'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        consultation = ConsultationRequest.objects.get(id=consultation_id)
        consultation.status = 'completed'
        consultation.contacted_at = timezone.now()
        consultation.save()
        
        serializer = ConsultationRequestSerializer(consultation)
        return Response({
            'message': 'Консультация отмечена как завершенная',
            'consultation': serializer.data
        })
        
    except ConsultationRequest.DoesNotExist:
        return Response(
            {'error': 'Запрос консультации не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )