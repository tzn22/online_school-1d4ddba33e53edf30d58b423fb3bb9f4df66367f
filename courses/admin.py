from django.contrib import admin
from django.utils.html import format_html
from .models import Course, Group, Lesson, Attendance, Badge, StudentBadge, StudentProgress, TestResult, VideoLesson, LessonRecording, MeetingParticipant, Homework, HomeworkSubmission, LessonMaterial, Achievement, StudentAchievement, SupportTicket, TicketMessage

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'level', 'duration_hours', 'is_active', 'created_at']
    list_filter = ['level', 'is_active', 'language', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'teacher', 'student_count', 'available_spots', 'start_date', 'is_active']
    list_filter = ['course', 'teacher', 'is_active', 'start_date']
    search_fields = ['title', 'course__title', 'teacher__username']
    filter_horizontal = ['students']
    readonly_fields = ['created_at']
    
    def student_count(self, obj):
        return obj.student_count
    student_count.short_description = 'Количество студентов'
    
    def available_spots(self, obj):
        return obj.available_spots
    available_spots.short_description = 'Свободных мест'

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson_type', 'teacher', 'start_time', 'duration_minutes', 'is_completed', 'ai_trainer_button']
    list_filter = ['lesson_type', 'teacher', 'is_completed', 'start_time']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'duration_minutes']
    date_hierarchy = 'start_time'
    
    def ai_trainer_button(self, obj):
        # Проверяем, есть ли поле has_ai_trainer, если нет - просто кнопка создания
        if hasattr(obj, 'has_ai_trainer'):
            if obj.has_ai_trainer:
                return format_html(
                    '<a class="button" href="{}" style="background-color: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Сгенерировать ИИ-вопросы</a>',
                    f'../generate-ai-trainer/{obj.id}/'
                )
            else:
                return format_html(
                    '<a class="button" href="{}" style="background-color: #2196F3; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Создать ИИ-тренажер</a>',
                    f'../generate-ai-trainer/{obj.id}/'
                )
        else:
            return format_html(
                '<a class="button" href="{}" style="background-color: #2196F3; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Создать ИИ-тренажер</a>',
                f'../generate-ai-trainer/{obj.id}/'
            )
    ai_trainer_button.short_description = 'ИИ-тренажер'

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'status', 'comment', 'created_at']
    list_filter = ['status', 'lesson__start_time', 'student']
    search_fields = ['student__username', 'lesson__title', 'comment']
    readonly_fields = ['created_at', 'updated_at']

# === АДМИН ПАНЕЛЬ ДЛЯ ПРЕПОДАВАТЕЛЯ ===

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'created_at']
    list_filter = ['badge_type', 'created_at']
    search_fields = ['name', 'description']

@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ['student', 'badge', 'awarded_at', 'awarded_by']
    list_filter = ['awarded_at', 'badge__badge_type']
    search_fields = ['student__username', 'badge__name', 'awarded_by__username']

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'current_level', 'overall_progress', 'last_activity']
    list_filter = ['current_level', 'last_activity']
    search_fields = ['student__username', 'course__title']

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'test_name', 'score', 'max_score', 'date_taken']
    list_filter = ['date_taken', 'test_name']
    search_fields = ['student__username', 'test_name', 'course__title']

# === АДМИН ПАНЕЛЬ ДЛЯ ВИДЕОУРОКОВ ===

@admin.register(VideoLesson)
class VideoLessonAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'zoom_meeting_id', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['lesson__title', 'zoom_meeting_id']
    readonly_fields = ['created_at']

@admin.register(LessonRecording)
class LessonRecordingAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'uploaded_by', 'uploaded_at', 'is_public']
    list_filter = ['is_public', 'uploaded_at']
    search_fields = ['title', 'lesson__title', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'file_size']

@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'user', 'role', 'joined_at', 'is_present']
    list_filter = ['role', 'is_present', 'joined_at']
    search_fields = ['lesson__title', 'user__username']

# === АДМИН ПАНЕЛЬ ДЛЯ ДОПОЛНИТЕЛЬНЫХ ФУНКЦИЙ ===

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'due_date', 'max_points', 'created_at']
    list_filter = ['due_date', 'created_at', 'lesson__title']
    search_fields = ['title', 'description', 'lesson__title']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'homework', 'submitted_at', 'grade', 'is_late']
    list_filter = ['is_late', 'submitted_at', 'grade']
    search_fields = ['student__username', 'homework__title']
    readonly_fields = ['submitted_at']

from django.contrib import admin
from django.utils.html import format_html
from .models import LessonMaterial


@admin.register(LessonMaterial)
class LessonMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'material_type', 'is_required', 'ai_trainer_button', 'created_at']
    list_filter = ['material_type', 'is_required', 'created_at']
    search_fields = ['title', 'lesson__title']
    readonly_fields = ['created_at']
    autocomplete_fields = ['lesson', 'ai_trainer_session']

    def ai_trainer_button(self, obj):
        if obj.material_type == 'ai_trainer':
            if obj.ai_trainer_prompt:
                return format_html(
                    '<a class="button" href="{}" '
                    'style="background-color: #4CAF50; color: white; padding: 5px 10px; '
                    'text-decoration: none; border-radius: 3px;">Сгенерировать по промпту</a>',
                    f'/admin/ai_trainer/aitrainingprompt/{obj.ai_trainer_prompt.id}/change/'
                )
            else:
                return format_html(
                    '<a class="button" href="{}" '
                    'style="background-color: #2196F3; color: white; padding: 5px 10px; '
                    'text-decoration: none; border-radius: 3px;">Создать промпт</a>',
                    '/admin/ai_trainer/aitrainingprompt/add/'
                )
        return "—"

    ai_trainer_button.short_description = 'ИИ-тренажёр'
    ai_trainer_button.allow_tags = True

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'achievement_type', 'required_points', 'created_at']
    list_filter = ['achievement_type', 'created_at']
    search_fields = ['name', 'description']

@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ['student', 'achievement', 'earned_at', 'earned_by']
    list_filter = ['earned_at', 'achievement__achievement_type']
    search_fields = ['student__username', 'achievement__name', 'earned_by__username']

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description', 'user__username']

@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'sender', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'ticket__title', 'sender__username']