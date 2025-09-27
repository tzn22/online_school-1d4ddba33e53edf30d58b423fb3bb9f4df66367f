from rest_framework import serializers
from .models import Course, Group, Lesson, Attendance, Badge, StudentBadge, StudentProgress, TestResult, VideoLesson, LessonRecording, MeetingParticipant, Homework, HomeworkSubmission, LessonMaterial, Achievement, StudentAchievement, SupportTicket, TicketMessage
from accounts.models import User
from payments.models import Payment

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class GroupSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    students_list = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Group
        fields = '__all__'
        read_only_fields = ['created_at', 'student_count', 'available_spots']
    
    def get_students_list(self, obj):
        return [
            {
                'id': student.id,
                'username': student.username,
                'full_name': student.get_full_name()
            }
            for student in obj.students.all()
        ]

class LessonSerializer(serializers.ModelSerializer):
    group_title = serializers.CharField(source='group.title', read_only=True, allow_null=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True, allow_null=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    payment_status = serializers.SerializerMethodField()
    student_payment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'duration_minutes']
    
    def get_payment_status(self, obj):
        """Проверить статус оплаты для группы"""
        if obj.lesson_type == 'group' and obj.group:
            payment_status = []
            for student in obj.group.students.all():
                # Проверить оплату студента за курс группы
                has_payment = Payment.objects.filter(
                    student=student,
                    course=obj.group.course,
                    status='paid'
                ).exists()
                payment_status.append({
                    'student_id': student.id,
                    'student_name': student.get_full_name(),
                    'has_payment': has_payment
                })
            return payment_status
        return []
    
    def get_student_payment_status(self, obj):
        """Проверить статус оплаты для индивидуального занятия"""
        if obj.lesson_type == 'individual' and obj.student:
            has_payment = Payment.objects.filter(
                student=obj.student,
                course=obj.group.course if obj.group else None,
                status='paid'
            ).exists()
            return {
                'student_id': obj.student.id,
                'student_name': obj.student.get_full_name(),
                'has_payment': has_payment
            }
        return {}
    
    def validate(self, attrs):
        lesson_type = attrs.get('lesson_type', 'group')
        
        if lesson_type == 'group' and not attrs.get('group'):
            raise serializers.ValidationError({
                'group': 'Для группового занятия необходимо указать группу'
            })
        
        if lesson_type == 'individual' and not attrs.get('student'):
            raise serializers.ValidationError({
                'student': 'Для индивидуального занятия необходимо указать студента'
            })
        
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': 'Время окончания должно быть больше времени начала'
            })
        
        return attrs

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, attrs):
        # Проверка, что студент состоит в группе, если занятие групповое
        lesson = attrs.get('lesson')
        student = attrs.get('student')
        
        if lesson and student and lesson.lesson_type == 'group':
            if student not in lesson.group.students.all():
                raise serializers.ValidationError({
                    'student': 'Студент не состоит в группе этого занятия'
                })
        
        return attrs

class ScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для расписания"""
    course_title = serializers.CharField(source='group.course.title', read_only=True, allow_null=True)
    group_title = serializers.CharField(source='group.title', read_only=True, allow_null=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True, allow_null=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    payment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'lesson_type', 'start_time', 'end_time',
            'duration_minutes', 'zoom_link', 'is_completed', 'course_title',
            'group_title', 'student_name', 'teacher_name', 'payment_status'
        ]
    
    def get_payment_status(self, obj):
        if obj.lesson_type == 'group' and obj.group:
            # Проверить оплату студентов группы
            students = obj.group.students.all()
            payment_status = []
            for student in students:
                has_payment = Payment.objects.filter(
                    student=student,
                    course=obj.group.course,
                    status='paid'
                ).exists()
                payment_status.append({
                    'student_id': student.id,
                    'student_name': student.get_full_name(),
                    'has_payment': has_payment
                })
            return payment_status
        elif obj.lesson_type == 'individual' and obj.student:
            has_payment = Payment.objects.filter(
                student=obj.student,
                course=obj.group.course if obj.group else None,
                status='paid'
            ).exists()
            return [{
                'student_id': obj.student.id,
                'student_name': obj.student.get_full_name(),
                'has_payment': has_payment
            }]
        return []

# === НОВЫЕ СЕРИАЛИЗАТОРЫ ДЛЯ ПРЕПОДАВАТЕЛЯ ===

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'

class StudentBadgeSerializer(serializers.ModelSerializer):
    badge_data = BadgeSerializer(source='badge', read_only=True)
    awarded_by_name = serializers.CharField(source='awarded_by.get_full_name', read_only=True)
    
    class Meta:
        model = StudentBadge
        fields = '__all__'
        read_only_fields = ['awarded_at']

class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = '__all__'
        read_only_fields = ['date_taken']

class StudentProgressSerializer(serializers.ModelSerializer):
    test_results_data = TestResultSerializer(source='test_results.all', many=True, read_only=True)
    
    class Meta:
        model = StudentProgress
        fields = '__all__'

# === СЕРИАЛИЗАТОРЫ ДЛЯ ВИДЕОУРОКОВ ===

class VideoLessonSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_start_time = serializers.DateTimeField(source='lesson.start_time', read_only=True)
    
    class Meta:
        model = VideoLesson
        fields = '__all__'
        read_only_fields = ['created_at']

class LessonRecordingSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = LessonRecording
        fields = '__all__'
        read_only_fields = ['uploaded_at']

class MeetingParticipantSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    
    class Meta:
        model = MeetingParticipant
        fields = '__all__'

# === СЕРИАЛИЗАТОРЫ ДЛЯ ДОПОЛНИТЕЛЬНЫХ ФУНКЦИЙ ===

# 1. Сериализатор домашних заданий
class HomeworkSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_teacher = serializers.CharField(source='lesson.teacher.get_full_name', read_only=True)
    
    class Meta:
        model = Homework
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    
    class Meta:
        model = HomeworkSubmission
        fields = '__all__'
        read_only_fields = ['submitted_at']

# 2. Сериализатор материалов урока
class LessonMaterialSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = LessonMaterial
        fields = '__all__'
        read_only_fields = ['created_at']

# 3. Сериализатор достижений
class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'
        read_only_fields = ['created_at']

class StudentAchievementSerializer(serializers.ModelSerializer):
    achievement_data = AchievementSerializer(source='achievement', read_only=True)
    earned_by_name = serializers.CharField(source='earned_by.get_full_name', read_only=True)
    
    class Meta:
        model = StudentAchievement
        fields = '__all__'
        read_only_fields = ['earned_at']

# 4. Сериализатор тикетов поддержки
class SupportTicketSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'resolved_at']

class TicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    
    class Meta:
        model = TicketMessage
        fields = '__all__'
        read_only_fields = ['created_at']