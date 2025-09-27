from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import models
from .models import Course, Group, Lesson, Attendance, Badge, StudentBadge, StudentProgress, TestResult, VideoLesson, LessonRecording, MeetingParticipant, Homework, HomeworkSubmission, LessonMaterial, Achievement, StudentAchievement, SupportTicket, TicketMessage
from accounts.models import User
from payments.models import Payment
from .serializers import (
    CourseSerializer, 
    GroupSerializer, 
    LessonSerializer, 
    AttendanceSerializer,
    ScheduleSerializer,
    BadgeSerializer,
    StudentBadgeSerializer,
    TestResultSerializer,
    StudentProgressSerializer,
    VideoLessonSerializer,
    LessonRecordingSerializer,
    MeetingParticipantSerializer,
    HomeworkSerializer,
    HomeworkSubmissionSerializer,
    LessonMaterialSerializer,
    AchievementSerializer,
    StudentAchievementSerializer,
    SupportTicketSerializer,
    TicketMessageSerializer
)
from .permissions import (
    IsTeacherOrAdmin, 
    IsStudentOrParent, 
    IsLessonOwnerOrAdmin,
    IsGroupTeacherOrAdmin,
    CanSubmitHomework,
    CanGradeHomework,
    CanManageMaterials,
    CanViewSupportTicket,
    CanManageSupportTicket
)
from notifications.services import NotificationService
import requests
import jwt
import time
from django.conf import settings

class CourseListCreateView(generics.ListCreateAPIView):
    """Список курсов и создание нового курса"""
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'language']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'price', 'created_at']
    ordering = ['-created_at']

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали курса"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

class GroupListCreateView(generics.ListCreateAPIView):
    """Список групп и создание новой группы"""
    queryset = Group.objects.filter(is_active=True)
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['course', 'teacher']
    search_fields = ['title', 'course__title']

class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали группы"""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsGroupTeacherOrAdmin]

class LessonListCreateView(generics.ListCreateAPIView):
    """Список занятий и создание нового занятия"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['lesson_type', 'teacher', 'group', 'is_completed']
    search_fields = ['title', 'description']
    ordering_fields = ['start_time', 'end_time']
    ordering = ['start_time']

class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали занятия"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsLessonOwnerOrAdmin]

class AttendanceListCreateView(generics.ListCreateAPIView):
    """Список посещений и отметка посещения"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['lesson', 'student', 'status']

class AttendanceDetailView(generics.RetrieveUpdateAPIView):
    """Детали посещения"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

class ScheduleView(generics.ListAPIView):
    """Просмотр расписания"""
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['lesson_type', 'teacher']
    ordering_fields = ['start_time']
    ordering = ['start_time']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Lesson.objects.filter(start_time__gte=timezone.now())
        
        if user.is_admin:
            return queryset
        elif user.is_teacher:
            return queryset.filter(teacher=user)
        elif user.is_student:
            # Студент видит свои групповые и индивидуальные занятия
            group_lessons = queryset.filter(
                lesson_type='group',
                group__students=user
            )
            individual_lessons = queryset.filter(
                lesson_type='individual',
                student=user
            )
            return group_lessons.union(individual_lessons)
        elif user.is_parent:
            # Родитель видит занятия своих детей
            children = user.children.all()
            group_lessons = queryset.filter(
                lesson_type='group',
                group__students__in=children
            )
            individual_lessons = queryset.filter(
                lesson_type='individual',
                student__in=children
            )
            return group_lessons.union(individual_lessons)
        
        return Lesson.objects.none()

class StudentScheduleView(generics.ListAPIView):
    """Расписание для конкретного студента"""
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        user = self.request.user
        
        # Проверка прав доступа
        if user.is_admin:
            student = User.objects.get(id=student_id, role='student')
        elif user.is_parent:
            student = User.objects.get(
                id=student_id, 
                role='student', 
                parent=user
            )
        elif user.is_student and user.id == student_id:
            student = user
        else:
            return Lesson.objects.none()
        
        # Получаем занятия студента
        group_lessons = Lesson.objects.filter(
            lesson_type='group',
            group__students=student,
            start_time__gte=timezone.now()
        )
        individual_lessons = Lesson.objects.filter(
            lesson_type='individual',
            student=student,
            start_time__gte=timezone.now()
        )
        
        return group_lessons.union(individual_lessons).order_by('start_time')

class TeacherScheduleView(generics.ListAPIView):
    """Расписание для преподавателя с детальной информацией"""
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        user = self.request.user
        
        # Проверка прав доступа
        if user.is_admin or (user.is_teacher and user.id == teacher_id):
            return Lesson.objects.filter(
                teacher_id=teacher_id,
                start_time__gte=timezone.now()
            ).select_related('group', 'group__course').prefetch_related(
                'group__students'
            ).order_by('start_time')
        
        return Lesson.objects.none()

# === НОВЫЕ ВЬЮХИ ДЛЯ ПРЕПОДАВАТЕЛЯ ===

# 1. API для бейджей
class BadgeListView(generics.ListAPIView):
    """Список всех бейджей"""
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]

class AwardBadgeView(generics.CreateAPIView):
    """Выдача бейджа студенту"""
    serializer_class = StudentBadgeSerializer
    permission_classes = [IsTeacherOrAdmin]
    
    def perform_create(self, serializer):
        serializer.save(awarded_by=self.request.user)

class StudentBadgesView(generics.ListAPIView):
    """Бейджи конкретного студента"""
    serializer_class = StudentBadgeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        student_id = self.kwargs['student_id']
        return StudentBadge.objects.filter(student_id=student_id)

# 2. API для прогресса
class StudentProgressView(generics.RetrieveUpdateAPIView):
    """Прогресс конкретного студента по курсу"""
    serializer_class = StudentProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        student_id = self.kwargs['student_id']
        course_id = self.kwargs['course_id']
        progress, created = StudentProgress.objects.get_or_create(
            student_id=student_id,
            course_id=course_id
        )
        return progress

class StudentProgressListView(generics.ListAPIView):
    """Прогресс всех студентов по курсу"""
    serializer_class = StudentProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return StudentProgress.objects.filter(course_id=course_id)

# 3. API для результатов тестов
class TestResultListView(generics.ListCreateAPIView):
    """Список результатов тестов"""
    serializer_class = TestResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        if student_id:
            return TestResult.objects.filter(student_id=student_id)
        return TestResult.objects.all()
    
    def perform_create(self, serializer):
        serializer.save()

# 4. Новый endpoint для отметки посещений с комментариями
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def mark_attendance_with_comment(request):
    """Массовая отметка посещений с комментариями"""
    lesson_id = request.data.get('lesson_id')
    attendance_data = request.data.get('attendance', [])
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        # Проверка прав доступа
        if not (request.user.is_admin or lesson.teacher == request.user):
            return Response(
                {'error': 'Нет прав для отметки посещений'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        created_attendances = []
        for data in attendance_data:
            student_id = data.get('student_id')
            status_value = data.get('status', 'present')
            comment = data.get('comment', '')
            
            # Создаем или обновляем запись посещения
            attendance, created = Attendance.objects.update_or_create(
                lesson=lesson,
                student_id=student_id,
                defaults={
                    'status': status_value,
                    'comment': comment
                }
            )
            
            # Отправляем уведомление студенту
            student = User.objects.get(id=student_id)
            if comment:
                NotificationService.send_notification(
                    user=student,
                    title=f'Комментарий к занятию: {lesson.title}',
                    message=f'Преподаватель оставил комментарий: {comment}',
                    notification_type='info',
                    channels=['email', 'in_app']
                )
            
            created_attendances.append(attendance)
        
        serializer = AttendanceSerializer(created_attendances, many=True)
        return Response({
            'message': 'Посещения успешно отмечены',
            'attendances': serializer.data
        })
        
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Занятие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_detailed_info(request, student_id):
    """Детальная информация о студенте (для преподавателя)"""
    try:
        student = User.objects.get(id=student_id, role='student')
        user = request.user
        
        # Проверка прав доступа
        if not (user.is_admin or 
                user.is_teacher or 
                (user.is_parent and student.parent == user)):
            return Response(
                {'error': 'Нет прав для просмотра информации о студенте'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Получаем информацию о студенте
        student_data = {
            'id': student.id,
            'username': student.username,
            'full_name': student.get_full_name(),
            'email': student.email,
            'birth_date': student.birth_date,
            'phone': student.phone,
            'avatar': student.avatar.url if student.avatar else None,
        }
        
        # Прогресс по курсам
        progress_data = []
        for progress in StudentProgress.objects.filter(student=student):
            progress_data.append({
                'course': {
                    'id': progress.course.id,
                    'title': progress.course.title,
                },
                'completed_topics': progress.completed_topics,
                'current_level': progress.current_level,
                'overall_progress': progress.overall_progress,
                'last_activity': progress.last_activity,
            })
        
        # Бейджи
        badges_data = []
        for badge in StudentBadge.objects.filter(student=student):
            badges_data.append({
                'id': badge.id,
                'badge': {
                    'id': badge.badge.id,
                    'name': badge.badge.name,
                    'description': badge.badge.description,
                    'badge_type': badge.badge.badge_type,
                    'icon': badge.badge.icon.url if badge.badge.icon else None,
                },
                'awarded_at': badge.awarded_at,
                'awarded_by': badge.awarded_by.get_full_name(),
                'comment': badge.comment,
            })
        
        # Результаты тестов
        test_results_data = []
        for test_result in TestResult.objects.filter(student=student):
            test_results_data.append({
                'test_name': test_result.test_name,
                'score': test_result.score,
                'max_score': test_result.max_score,
                'date_taken': test_result.date_taken,
                'course': {
                    'id': test_result.course.id,
                    'title': test_result.course.title,
                },
            })
        
        return Response({
            'student': student_data,
            'progress': progress_data,
            'badges': badges_data,
            'test_results': test_results_data,
        })
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Студент не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

# 5. Расширение существующих эндпоинтов
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def award_badge_to_student(request):
    """Выдача бейджа студенту"""
    student_id = request.data.get('student_id')
    badge_id = request.data.get('badge_id')
    comment = request.data.get('comment', '')
    lesson_id = request.data.get('lesson_id')
    
    try:
        student = User.objects.get(id=student_id, role='student')
        badge = Badge.objects.get(id=badge_id)
        lesson = Lesson.objects.get(id=lesson_id) if lesson_id else None
        
        # Создаем бейдж
        student_badge = StudentBadge.objects.create(
            student=student,
            badge=badge,
            awarded_by=request.user,
            lesson=lesson,
            comment=comment
        )
        
        # Отправляем уведомление
        NotificationService.send_notification(
            user=student,
            title=f'Новый бейдж: {badge.name}',
            message=f'Вам выдан бейдж "{badge.name}": {badge.description}',
            notification_type='success',
            channels=['email', 'in_app']
        )
        
        serializer = StudentBadgeSerializer(student_badge)
        return Response({
            'message': 'Бейдж успешно выдан',
            'badge': serializer.data
        })
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Студент не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Badge.DoesNotExist:
        return Response(
            {'error': 'Бейдж не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def update_student_progress(request, student_id, course_id):
    """Обновление прогресса студента"""
    try:
        progress, created = StudentProgress.objects.get_or_create(
            student_id=student_id,
            course_id=course_id
        )
        
        # Обновляем прогресс
        completed_topics = request.data.get('completed_topics', progress.completed_topics)
        test_results = request.data.get('test_results', progress.test_results)
        current_level = request.data.get('current_level', progress.current_level)
        overall_progress = request.data.get('overall_progress', progress.overall_progress)
        
        progress.completed_topics = completed_topics
        progress.test_results = test_results
        progress.current_level = current_level
        progress.overall_progress = overall_progress
        progress.save()
        
        serializer = StudentProgressSerializer(progress)
        return Response({
            'message': 'Прогресс успешно обновлен',
            'progress': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def add_test_result(request):
    """Добавление результата теста"""
    try:
        student_id = request.data.get('student_id')
        course_id = request.data.get('course_id')
        test_name = request.data.get('test_name')
        score = request.data.get('score')
        max_score = request.data.get('max_score', 100)
        lesson_id = request.data.get('lesson_id')
        
        test_result = TestResult.objects.create(
            student_id=student_id,
            course_id=course_id,
            test_name=test_name,
            score=score,
            max_score=max_score,
            lesson_id=lesson_id if lesson_id else None
        )
        
        serializer = TestResultSerializer(test_result)
        return Response({
            'message': 'Результат теста добавлен',
            'result': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

# === ВИДЕОУРОКИ ===

# 1. API для видеоуроков
class VideoLessonCreateView(generics.CreateAPIView):
    """Создание видеоурока (Zoom встречи)"""
    serializer_class = VideoLessonSerializer
    permission_classes = [IsTeacherOrAdmin]
    
    def perform_create(self, serializer):
        lesson_id = self.request.data.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Создаем Zoom встречу
        zoom_data = self.create_zoom_meeting(lesson)
        
        video_lesson = serializer.save(
            lesson=lesson,
            zoom_meeting_id=zoom_data.get('id'),
            zoom_join_url=zoom_data.get('join_url'),
            zoom_start_url=zoom_data.get('start_url'),
            meeting_password=zoom_data.get('password')
        )
        
        # Добавляем участников
        self.add_participants_to_meeting(lesson, zoom_data.get('id'))
    
    def create_zoom_meeting(self, lesson):
        """Создание Zoom встречи через API"""
        # Заглушка - в реальности нужно использовать Zoom API
        zoom_api_key = getattr(settings, 'ZOOM_API_KEY', '')
        zoom_api_secret = getattr(settings, 'ZOOM_API_SECRET', '')
        
        if not zoom_api_key or not zoom_api_secret:
            # Возвращаем тестовые данные
            return {
                'id': f'test_{lesson.id}',
                'join_url': f'https://zoom.us/j/test_{lesson.id}',
                'start_url': f'https://zoom.us/s/test_{lesson.id}',
                'password': '123456'
            }
        
        # Реализация Zoom API вызова
        headers = {
            'Authorization': f'Bearer {self.get_zoom_token()}',
            'Content-Type': 'application/json'
        }
        
        meeting_data = {
            'topic': f'Занятие: {lesson.title}',
            'type': 2,  # Scheduled meeting
            'start_time': lesson.start_time.isoformat(),
            'duration': lesson.duration_minutes,
            'timezone': 'Europe/Moscow',
            'settings': {
                'host_video': True,
                'participant_video': True,
                'join_before_host': True,
                'mute_upon_entry': False,
                'waiting_room': False
            }
        }
        
        response = requests.post(
            f'https://api.zoom.us/v2/users/{self.get_zoom_user_id()}/meetings',
            headers=headers,
            json=meeting_data
        )
        
        return response.json() if response.status_code == 201 else {}
    
    def get_zoom_token(self):
        """Получение Zoom токена"""
        # Заглушка - в реальности нужно использовать JWT или OAuth
        return 'test_token'
    
    def get_zoom_user_id(self):
        """Получение Zoom user ID"""
        return 'test_user_id'
    
    def add_participants_to_meeting(self, lesson, meeting_id):
        """Добавление участников в Zoom встречу"""
        if lesson.lesson_type == 'group' and lesson.group:
            students = lesson.group.students.all()
        elif lesson.lesson_type == 'individual' and lesson.student:
            students = [lesson.student]
        else:
            students = []
        
        for student in students:
            MeetingParticipant.objects.create(
                lesson=lesson,
                user=student,
                role='participant',
                joined_at=lesson.start_time
            )

class VideoLessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали видеоурока"""
    queryset = VideoLesson.objects.all()
    serializer_class = VideoLessonSerializer
    permission_classes = [IsAuthenticated, IsLessonOwnerOrAdmin]

# 2. API для записей уроков
class LessonRecordingListView(generics.ListCreateAPIView):
    """Список записей урока и загрузка новой записи"""
    serializer_class = LessonRecordingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            return LessonRecording.objects.filter(lesson_id=lesson_id)
        return LessonRecording.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class LessonRecordingDetailView(generics.RetrieveDestroyAPIView):
    """Детали записи урока"""
    queryset = LessonRecording.objects.all()
    serializer_class = LessonRecordingSerializer
    permission_classes = [IsAuthenticated]

# 3. API для участников встречи
class MeetingParticipantsView(generics.ListAPIView):
    """Список участников встречи"""
    serializer_class = MeetingParticipantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        return MeetingParticipant.objects.filter(lesson_id=lesson_id)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def start_zoom_meeting(request, lesson_id):
    """Начать Zoom встречу"""
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        video_lesson = VideoLesson.objects.get(lesson=lesson)
        
        # В реальности - запуск Zoom встречи
        # Здесь возвращаем тестовые данные
        meeting_data = {
            'meeting_id': video_lesson.zoom_meeting_id,
            'join_url': video_lesson.zoom_join_url,
            'start_url': video_lesson.zoom_start_url,
            'password': video_lesson.meeting_password,
            'lesson_title': lesson.title,
            'start_time': lesson.start_time,
        }
        
        # Отправляем уведомления участникам
        if lesson.lesson_type == 'group' and lesson.group:
            participants = lesson.group.students.all()
        elif lesson.lesson_type == 'individual' and lesson.student:
            participants = [lesson.student]
        else:
            participants = []
        
        for participant in participants:
            NotificationService.send_notification(
                user=participant,
                title=f'Начало занятия: {lesson.title}',
                message=f'Занятие "{lesson.title}" начинается. Ссылка: {video_lesson.zoom_join_url}',
                notification_type='lesson',
                channels=['email', 'in_app', 'push']
            )
        
        return Response({
            'message': 'Zoom встреча запущена',
            'meeting_data': meeting_data
        })
        
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Занятие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except VideoLesson.DoesNotExist:
        return Response(
            {'error': 'Видеоурок не создан'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_zoom_meeting(request, lesson_id):
    """Присоединиться к Zoom встрече"""
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        video_lesson = VideoLesson.objects.get(lesson=lesson)
        
        # Проверяем права доступа
        user = request.user
        if not (user.is_admin or 
                lesson.teacher == user or
                (lesson.lesson_type == 'group' and user in lesson.group.students.all()) or
                (lesson.lesson_type == 'individual' and lesson.student == user)):
            return Response(
                {'error': 'Нет прав для присоединения к встрече'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Отмечаем участие
        participant, created = MeetingParticipant.objects.get_or_create(
            lesson=lesson,
            user=user,
            defaults={
                'role': 'participant' if user.is_student else 'host',
                'joined_at': timezone.now(),
                'is_present': True
            }
        )
        
        if not created:
            participant.joined_at = timezone.now()
            participant.is_present = True
            participant.save()
        
        return Response({
            'message': 'Успешно присоединились к встрече',
            'join_url': video_lesson.zoom_join_url,
            'password': video_lesson.meeting_password
        })
        
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Занятие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except VideoLesson.DoesNotExist:
        return Response(
            {'error': 'Видеоурок не создан'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def end_zoom_meeting(request, lesson_id):
    """Завершить Zoom встречу"""
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        # Обновляем статус участников
        participants = MeetingParticipant.objects.filter(lesson=lesson, is_present=True)
        for participant in participants:
            participant.left_at = timezone.now()
            participant.duration = participant.left_at - participant.joined_at
            participant.is_present = False
            participant.save()
        
        # Отмечаем занятие как завершенное
        lesson.is_completed = True
        lesson.save()
        
        return Response({
            'message': 'Встреча завершена',
            'participants_count': participants.count()
        })
        
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Занятие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

# 4. WebSocket чат для урока (заглушка - реальная реализация требует Channels)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_chat_messages(request, lesson_id):
    """Получить сообщения чата урока"""
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        # Проверяем права доступа
        user = request.user
        if not (user.is_admin or 
                lesson.teacher == user or
                (lesson.lesson_type == 'group' and user in lesson.group.students.all()) or
                (lesson.lesson_type == 'individual' and lesson.student == user)):
            return Response(
                {'error': 'Нет прав для доступа к чату'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Получаем сообщения из чата урока
        # В реальности - это будет через WebSocket
        # Здесь возвращаем последние 50 сообщений из чата группы
        from chat.models import ChatRoom, Message
        
        if lesson.lesson_type == 'group' and lesson.group:
            # Ищем чат группы
            chat_room, created = ChatRoom.objects.get_or_create(
                name=f"Урок: {lesson.title}",
                chat_type='group',
                created_by=lesson.teacher
            )
            # Добавляем участников
            for student in lesson.group.students.all():
                chat_room.participants.add(student)
            chat_room.participants.add(lesson.teacher)
            
            messages = Message.objects.filter(room=chat_room).order_by('-created_at')[:50]
            message_data = [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'sender': msg.sender.get_full_name(),
                    'created_at': msg.created_at,
                    'message_type': msg.message_type
                }
                for msg in messages
            ]
            
            return Response({
                'lesson_id': lesson.id,
                'chat_room_id': chat_room.id,
                'messages': message_data
            })
        else:
            return Response({
                'lesson_id': lesson.id,
                'messages': []
            })
            
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Занятие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_lesson_chat_message(request, lesson_id):
    """Отправить сообщение в чат урока"""
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        # Проверяем права доступа
        user = request.user
        if not (user.is_admin or 
                lesson.teacher == user or
                (lesson.lesson_type == 'group' and user in lesson.group.students.all()) or
                (lesson.lesson_type == 'individual' and lesson.student == user)):
            return Response(
                {'error': 'Нет прав для отправки сообщений'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        content = request.data.get('content', '')
        if not content.strip():
            return Response(
                {'error': 'Сообщение не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем чат комнату для урока
        from chat.models import ChatRoom, Message
        
        chat_room, created = ChatRoom.objects.get_or_create(
            name=f"Урок: {lesson.title}",
            chat_type='group',
            created_by=lesson.teacher
        )
        
        # Добавляем участников
        if lesson.lesson_type == 'group' and lesson.group:
            for student in lesson.group.students.all():
                chat_room.participants.add(student)
        elif lesson.lesson_type == 'individual' and lesson.student:
            chat_room.participants.add(lesson.student)
        
        chat_room.participants.add(lesson.teacher)
        
        # Создаем сообщение
        message = Message.objects.create(
            room=chat_room,
            sender=user,
            content=content,
            message_type='text'
        )
        
        # В реальности - отправка через WebSocket
        # Здесь просто возвращаем сообщение
        
        return Response({
            'message': 'Сообщение отправлено',
            'message_data': {
                'id': message.id,
                'content': message.content,
                'sender': message.sender.get_full_name(),
                'created_at': message.created_at,
                'message_type': message.message_type
            }
        })
        
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Занятие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

# === ДОМАШНИЕ ЗАДАНИЯ ===

class HomeworkListView(generics.ListCreateAPIView):
    """Список домашних заданий и создание нового задания"""
    serializer_class = HomeworkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            return Homework.objects.filter(lesson_id=lesson_id)
        return Homework.objects.all()
    
    def perform_create(self, serializer):
        # Только преподаватель может создавать задания
        lesson = serializer.validated_data['lesson']
        if not (self.request.user.is_admin or lesson.teacher == self.request.user):
            raise PermissionError("Только преподаватель может создавать задания для этого урока")
        serializer.save()

class HomeworkDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали домашнего задания"""
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [IsAuthenticated]

class HomeworkSubmissionListView(generics.ListCreateAPIView):
    """Список сдач заданий и сдача нового задания"""
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        homework_id = self.request.query_params.get('homework_id')
        student_id = self.request.query_params.get('student_id')
        
        queryset = HomeworkSubmission.objects.all()
        
        if homework_id:
            queryset = queryset.filter(homework_id=homework_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
            
        return queryset
    
    def perform_create(self, serializer):
        homework = serializer.validated_data['homework']
        
        # Проверяем права: только студент может сдавать свое задание
        if serializer.validated_data['student'] != self.request.user:
            if not (self.request.user.is_admin or homework.lesson.teacher == self.request.user):
                raise PermissionError("Нет прав для сдачи этого задания")
        
        # Проверяем срок сдачи
        if timezone.now() > homework.due_date:
            serializer.save(is_late=True)
        else:
            serializer.save()

class HomeworkSubmissionDetailView(generics.RetrieveUpdateAPIView):
    """Детали сдачи задания"""
    queryset = HomeworkSubmission.objects.all()
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = [IsAuthenticated]

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def grade_homework_submission(request, submission_id):
    """Оценка домашнего задания"""
    try:
        submission = HomeworkSubmission.objects.get(id=submission_id)
        grade = request.data.get('grade')
        feedback = request.data.get('feedback', '')
        
        if grade is None:
            return Response(
                {'error': 'Оценка обязательна'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        submission.grade = grade
        submission.feedback = feedback
        submission.save()
        
        # Отправляем уведомление студенту
        NotificationService.send_notification(
            user=submission.student,
            title=f'Оценка за задание: {submission.homework.title}',
            message=f'Вам выставлена оценка {grade} за задание "{submission.homework.title}". Комментарий: {feedback}',
            notification_type='info',
            channels=['email', 'in_app']
        )
        
        serializer = HomeworkSubmissionSerializer(submission)
        return Response({
            'message': 'Задание оценено',
            'submission': serializer.data
        })
        
    except HomeworkSubmission.DoesNotExist:
        return Response(
            {'error': 'Сдача задания не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

# === МАТЕРИАЛЫ УРОКА ===

class LessonMaterialListView(generics.ListCreateAPIView):
    """Список материалов урока и загрузка новых"""
    serializer_class = LessonMaterialSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            return LessonMaterial.objects.filter(lesson_id=lesson_id)
        return LessonMaterial.objects.all()
    
    def perform_create(self, serializer):
        lesson = serializer.validated_data['lesson']
        # Только преподаватель может добавлять материалы
        if not (self.request.user.is_admin or lesson.teacher == self.request.user):
            raise PermissionError("Только преподаватель может добавлять материалы для этого урока")
        serializer.save()

class LessonMaterialDetailView(generics.RetrieveDestroyAPIView):
    """Детали материала урока"""
    queryset = LessonMaterial.objects.all()
    serializer_class = LessonMaterialSerializer
    permission_classes = [IsAuthenticated]

# === ДОСТИЖЕНИЯ ===

class AchievementListView(generics.ListAPIView):
    """Список всех достижений"""
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]

class StudentAchievementsView(generics.ListAPIView):
    """Достижения конкретного студента"""
    serializer_class = StudentAchievementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        student_id = self.kwargs['student_id']
        return StudentAchievement.objects.filter(student_id=student_id)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def award_achievement_to_student(request):
    """Выдача достижения студенту"""
    try:
        student_id = request.data.get('student_id')
        achievement_id = request.data.get('achievement_id')
        comment = request.data.get('comment', '')
        
        student = User.objects.get(id=student_id, role='student')
        achievement = Achievement.objects.get(id=achievement_id)
        
        student_achievement = StudentAchievement.objects.create(
            student=student,
            achievement=achievement,
            earned_by=request.user,
            comment=comment
        )
        
        # Отправляем уведомление
        NotificationService.send_notification(
            user=student,
            title=f'Новое достижение: {achievement.name}',
            message=f'Вам выдано достижение "{achievement.name}": {achievement.description}',
            notification_type='success',
            channels=['email', 'in_app']
        )
        
        serializer = StudentAchievementSerializer(student_achievement)
        return Response({
            'message': 'Достижение успешно выдано',
            'achievement': serializer.data
        })
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Студент не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Achievement.DoesNotExist:
        return Response(
            {'error': 'Достижение не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

# === ПОДДЕРЖКА ===

class SupportTicketListView(generics.ListCreateAPIView):
    """Список тикетов и создание нового тикета"""
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            # Админ видит все тикеты
            return SupportTicket.objects.all()
        else:
            # Пользователь видит только свои тикеты
            return SupportTicket.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SupportTicketDetailView(generics.RetrieveUpdateAPIView):
    """Детали тикета"""
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        user = request.user
        
        # Проверяем права
        if not (user.is_admin or ticket.user == user):
            return Response(
                {'error': 'Нет прав для изменения тикета'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Если админ меняет статус
        if user.is_admin and 'status' in request.data:
            if request.data['status'] == 'resolved':
                serializer.save(resolved_at=timezone.now())
            else:
                return super().update(request, *args, **kwargs)
        
        return super().update(request, *args, **kwargs)

class TicketMessagesView(generics.ListCreateAPIView):
    """Сообщения тикета"""
    serializer_class = TicketMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        ticket_id = self.kwargs['ticket_id']
        return TicketMessage.objects.filter(ticket_id=ticket_id)
    
    def perform_create(self, serializer):
        ticket_id = self.kwargs['ticket_id']
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        user = self.request.user
        
        # Проверяем права
        if not (user.is_admin or ticket.user == user or ticket.assigned_to == user):
            raise PermissionError("Нет прав для отправки сообщения в этот тикет")
        
        serializer.save(sender=user)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def assign_ticket(request, ticket_id):
    """Назначить тикет администратору"""
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
        admin_id = request.data.get('admin_id')
        
        admin = User.objects.get(id=admin_id, role='admin')
        ticket.assigned_to = admin
        ticket.status = 'in_progress'
        ticket.save()
        
        # Отправляем уведомление админу
        NotificationService.send_notification(
            user=admin,
            title=f'Назначен тикет: {ticket.title}',
            message=f'Вам назначен тикет "{ticket.title}" от {ticket.user.get_full_name()}',
            notification_type='info',
            channels=['email', 'in_app']
        )
        
        serializer = SupportTicketSerializer(ticket)
        return Response({
            'message': 'Тикет назначен',
            'ticket': serializer.data
        })
        
    except SupportTicket.DoesNotExist:
        return Response(
            {'error': 'Тикет не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'Администратор не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

# === АНАЛИТИКА И ОТЧЕТЫ ===

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def get_student_homework_stats(request, student_id):
    """Статистика домашних заданий студента"""
    try:
        student = User.objects.get(id=student_id, role='student')
        
        # Подсчет заданий
        total_homework = HomeworkSubmission.objects.filter(student=student).count()
        submitted_homework = HomeworkSubmission.objects.filter(
            student=student,
            grade__isnull=False
        ).count()
        late_submissions = HomeworkSubmission.objects.filter(
            student=student,
            is_late=True
        ).count()
        
        # Средняя оценка
        avg_grade = HomeworkSubmission.objects.filter(
            student=student,
            grade__isnull=False
        ).aggregate(models.Avg('grade'))['grade__avg']
        
        stats = {
            'student_id': student.id,
            'student_name': student.get_full_name(),
            'total_homework': total_homework,
            'submitted_homework': submitted_homework,
            'late_submissions': late_submissions,
            'average_grade': float(avg_grade) if avg_grade else 0,
            'completion_rate': (submitted_homework / total_homework * 100) if total_homework > 0 else 0
        }
        
        return Response(stats)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Студент не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def get_lesson_materials_stats(request, lesson_id):
    """Статистика материалов урока"""
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        total_materials = LessonMaterial.objects.filter(lesson=lesson).count()
        required_materials = LessonMaterial.objects.filter(
            lesson=lesson,
            is_required=True
        ).count()
        
        materials_stats = {
            'lesson_id': lesson.id,
            'lesson_title': lesson.title,
            'total_materials': total_materials,
            'required_materials': required_materials,
            'materials': []
        }
        
        for material in LessonMaterial.objects.filter(lesson=lesson):
            materials_stats['materials'].append({
                'id': material.id,
                'title': material.title,
                'type': material.material_type,
                'is_required': material.is_required,
                'created_at': material.created_at
            })
        
        return Response(materials_stats)
        
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Занятие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_progress_dashboard(request):
    """Дашборд прогресса студента"""
    user = request.user
    
    if user.is_student:
        # Прогресс для студента
        progress_data = {
            'student_id': user.id,
            'student_name': user.get_full_name(),
            'total_courses': user.learning_groups.values('course').distinct().count(),
            'total_lessons': Lesson.objects.filter(
                models.Q(group__students=user) | models.Q(student=user)
            ).count(),
            'completed_lessons': Attendance.objects.filter(
                student=user,
                status='present'
            ).count(),
            'total_homework': HomeworkSubmission.objects.filter(student=user).count(),
            'submitted_homework': HomeworkSubmission.objects.filter(
                student=user,
                grade__isnull=False
            ).count(),
            'total_badges': StudentBadge.objects.filter(student=user).count(),
            'total_achievements': StudentAchievement.objects.filter(student=user).count(),
        }
        
        return Response(progress_data)
    elif user.is_teacher:
        # Статистика для преподавателя
        teacher_stats = {
            'teacher_id': user.id,
            'teacher_name': user.get_full_name(),
            'total_groups': Group.objects.filter(teacher=user).count(),
            'total_students': Group.objects.filter(teacher=user).values('students').count(),
            'total_lessons': Lesson.objects.filter(teacher=user).count(),
            'graded_homework': HomeworkSubmission.objects.filter(
                homework__lesson__teacher=user,
                grade__isnull=False
            ).count(),
        }
        
        return Response(teacher_stats)
    else:
        return Response(
            {'error': 'Недостаточно прав'},
            status=status.HTTP_403_FORBIDDEN
        )

# === ОСТАЛЬНЫЕ СУЩЕСТВУЮЩИЕ ФУНКЦИИ ===

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def mark_attendance(request):
    """Массовая отметка посещений для занятия (старая версия)"""
    lesson_id = request.data.get('lesson_id')
    attendance_data = request.data.get('attendance', [])
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        # Проверка прав доступа
        if not (request.user.is_admin or lesson.teacher == request.user):
            return Response(
                {'error': 'Нет прав для отметки посещений'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        created_attendances = []
        for data in attendance_data:
            student_id = data.get('student_id')
            status_value = data.get('status', 'present')
            notes = data.get('notes', '')
            
            # Создаем или обновляем запись посещения
            attendance, created = Attendance.objects.update_or_create(
                lesson=lesson,
                student_id=student_id,
                defaults={
                    'status': status_value,
                    'comment': notes  # Обновлено: теперь используется поле comment
                }
            )
            created_attendances.append(attendance)
        
        serializer = AttendanceSerializer(created_attendances, many=True)
        return Response({
            'message': 'Посещения успешно отмечены',
            'attendances': serializer.data
        })
        
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Занятие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_group_students(request, group_id):
    """Получить список студентов в группе"""
    try:
        group = Group.objects.get(id=group_id)
        user = request.user
        
        # Проверка прав доступа
        if not (user.is_admin or group.teacher == user):
            return Response(
                {'error': 'Нет прав для просмотра студентов группы'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        students = group.students.all()
        student_data = [
            {
                'id': student.id,
                'username': student.username,
                'full_name': student.get_full_name(),
                'email': student.email
            }
            for student in students
        ]
        
        return Response({
            'group': group.title,
            'students': student_data,
            'count': len(student_data)
        })
        
    except Group.DoesNotExist:
        return Response(
            {'error': 'Группа не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )