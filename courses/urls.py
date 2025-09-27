from django.urls import path
from .views import (
    CourseListCreateView,
    CourseDetailView,
    GroupListCreateView,
    GroupDetailView,
    LessonListCreateView,
    LessonDetailView,
    AttendanceListCreateView,
    AttendanceDetailView,
    ScheduleView,
    StudentScheduleView,
    TeacherScheduleView,
    mark_attendance,
    get_group_students,
    # === НОВЫЕ URL ДЛЯ ПРЕПОДАВАТЕЛЯ ===
    BadgeListView,
    AwardBadgeView,
    StudentBadgesView,
    StudentProgressView,
    StudentProgressListView,
    TestResultListView,
    mark_attendance_with_comment,
    get_student_detailed_info,
    award_badge_to_student,
    update_student_progress,
    add_test_result,
    # === НОВЫЕ URL ДЛЯ ВИДЕОУРОКОВ ===
    VideoLessonCreateView,
    VideoLessonDetailView,
    LessonRecordingListView,
    LessonRecordingDetailView,
    MeetingParticipantsView,
    start_zoom_meeting,
    join_zoom_meeting,
    end_zoom_meeting,
    get_lesson_chat_messages,
    send_lesson_chat_message,
    # === НОВЫЕ URL ДЛЯ ДОПОЛНИТЕЛЬНЫХ ФУНКЦИЙ ===
    # Домашние задания
    HomeworkListView,
    HomeworkDetailView,
    HomeworkSubmissionListView,
    HomeworkSubmissionDetailView,
    grade_homework_submission,
    # Материалы урока
    LessonMaterialListView,
    LessonMaterialDetailView,
    # Достижения
    AchievementListView,
    StudentAchievementsView,
    award_achievement_to_student,
    # Поддержка
    SupportTicketListView,
    SupportTicketDetailView,
    TicketMessagesView,
    assign_ticket,
    # Аналитика
    get_student_homework_stats,
    get_lesson_materials_stats,
    get_student_progress_dashboard
)

urlpatterns = [
    # Курсы
    path('courses/', CourseListCreateView.as_view(), name='course-list'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    
    # Группы
    path('groups/', GroupListCreateView.as_view(), name='group-list'),
    path('groups/<int:pk>/', GroupDetailView.as_view(), name='group-detail'),
    path('groups/<int:group_id>/students/', get_group_students, name='group-students'),
    
    # Занятия
    path('lessons/', LessonListCreateView.as_view(), name='lesson-list'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    
    # Посещения
    path('attendance/', AttendanceListCreateView.as_view(), name='attendance-list'),
    path('attendance/<int:pk>/', AttendanceDetailView.as_view(), name='attendance-detail'),
    path('attendance/mark/', mark_attendance, name='mark-attendance'),
    path('attendance/mark-with-comment/', mark_attendance_with_comment, name='mark-attendance-with-comment'),
    
    # Расписание
    path('schedule/', ScheduleView.as_view(), name='schedule'),
    path('schedule/student/<int:student_id>/', StudentScheduleView.as_view(), name='student-schedule'),
    path('schedule/teacher/<int:teacher_id>/', TeacherScheduleView.as_view(), name='teacher-schedule'),
    
    # === НОВЫЕ URL ДЛЯ ПРЕПОДАВАТЕЛЯ ===
    # Бейджи
    path('badges/', BadgeListView.as_view(), name='badge-list'),
    path('badges/award/', AwardBadgeView.as_view(), name='award-badge'),
    path('students/<int:student_id>/badges/', StudentBadgesView.as_view(), name='student-badges'),
    path('students/<int:student_id>/badges/award/', award_badge_to_student, name='award-badge-to-student'),
    
    # Прогресс
    path('students/<int:student_id>/progress/<int:course_id>/', StudentProgressView.as_view(), name='student-progress'),
    path('courses/<int:course_id>/progress/', StudentProgressListView.as_view(), name='course-progress-list'),
    path('students/<int:student_id>/progress/<int:course_id>/update/', update_student_progress, name='update-student-progress'),
    
    # Результаты тестов
    path('test-results/', TestResultListView.as_view(), name='test-results-list'),
    path('students/<int:student_id>/test-results/', TestResultListView.as_view(), name='student-test-results'),
    path('test-results/add/', add_test_result, name='add-test-result'),
    
    # Детальная информация о студенте
    path('students/<int:student_id>/detailed-info/', get_student_detailed_info, name='student-detailed-info'),
    
    # === НОВЫЕ URL ДЛЯ ВИДЕОУРОКОВ ===
    # Видеоуроки
    path('video-lessons/', VideoLessonCreateView.as_view(), name='video-lesson-create'),
    path('video-lessons/<int:pk>/', VideoLessonDetailView.as_view(), name='video-lesson-detail'),
    path('lessons/<int:lesson_id>/start-meeting/', start_zoom_meeting, name='start-zoom-meeting'),
    path('lessons/<int:lesson_id>/join-meeting/', join_zoom_meeting, name='join-zoom-meeting'),
    path('lessons/<int:lesson_id>/end-meeting/', end_zoom_meeting, name='end-zoom-meeting'),
    
    # Записи уроков
    path('recordings/', LessonRecordingListView.as_view(), name='lesson-recordings'),
    path('recordings/<int:pk>/', LessonRecordingDetailView.as_view(), name='lesson-recording-detail'),
    
    # Участники встречи
    path('lessons/<int:lesson_id>/participants/', MeetingParticipantsView.as_view(), name='meeting-participants'),
    
    # Чат урока
    path('lessons/<int:lesson_id>/chat/', get_lesson_chat_messages, name='lesson-chat'),
    path('lessons/<int:lesson_id>/chat/send/', send_lesson_chat_message, name='send-lesson-message'),
    
    # === НОВЫЕ URL ДЛЯ ДОПОЛНИТЕЛЬНЫХ ФУНКЦИЙ ===
    # === ДОМАШНИЕ ЗАДАНИЯ ===
    path('homework/', HomeworkListView.as_view(), name='homework-list'),
    path('homework/<int:pk>/', HomeworkDetailView.as_view(), name='homework-detail'),
    path('homework-submissions/', HomeworkSubmissionListView.as_view(), name='homework-submissions'),
    path('homework-submissions/<int:pk>/', HomeworkSubmissionDetailView.as_view(), name='homework-submission-detail'),
    path('homework-submissions/<int:submission_id>/grade/', grade_homework_submission, name='grade-homework-submission'),
    
    # === МАТЕРИАЛЫ УРОКА ===
    path('lesson-materials/', LessonMaterialListView.as_view(), name='lesson-materials'),
    path('lesson-materials/<int:pk>/', LessonMaterialDetailView.as_view(), name='lesson-material-detail'),
    
    # === ДОСТИЖЕНИЯ ===
    path('achievements/', AchievementListView.as_view(), name='achievements'),
    path('students/<int:student_id>/achievements/', StudentAchievementsView.as_view(), name='student-achievements'),
    path('students/<int:student_id>/achievements/award/', award_achievement_to_student, name='award-achievement'),
    
    # === ПОДДЕРЖКА ===
    path('support-tickets/', SupportTicketListView.as_view(), name='support-tickets'),
    path('support-tickets/<int:pk>/', SupportTicketDetailView.as_view(), name='support-ticket-detail'),
    path('support-tickets/<int:ticket_id>/messages/', TicketMessagesView.as_view(), name='ticket-messages'),
    path('support-tickets/<int:ticket_id>/assign/', assign_ticket, name='assign-ticket'),
    
    # === АНАЛИТИКА ===
    path('students/<int:student_id>/homework-stats/', get_student_homework_stats, name='student-homework-stats'),
    path('lessons/<int:lesson_id>/materials-stats/', get_lesson_materials_stats, name='lesson-materials-stats'),
    path('dashboard/progress/', get_student_progress_dashboard, name='student-progress-dashboard'),
]