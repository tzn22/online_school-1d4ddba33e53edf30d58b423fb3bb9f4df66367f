from rest_framework import permissions

class IsNotificationOwner(permissions.BasePermission):
    """
    Разрешение только владельцу уведомления
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Владелец уведомления может его просматривать/редактировать
        return obj.user == request.user

class IsAdminOrOwner(permissions.BasePermission):
    """
    Разрешение администратору или владельцу
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.user == request.user

class CanSendBulkNotifications(permissions.BasePermission):
    """
    Разрешение на массовую отправку уведомлений (только админам)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin

class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Разрешение преподавателям или администраторам
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or request.user.is_teacher
        )

class IsStudentOrParent(permissions.BasePermission):
    """
    Разрешение студентам или их родителям
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_admin:
            return True
            
        if request.user.is_student:
            # Студент может видеть свои уведомления
            if hasattr(obj, 'student') and obj.student == request.user:
                return True
            # Или если он в группе
            if hasattr(obj, 'group') and request.user in obj.group.students.all():
                return True
                
        if request.user.is_parent:
            # Родитель может видеть уведомления своих детей
            children = request.user.children.all()
            if hasattr(obj, 'student') and obj.student in children:
                return True
            if hasattr(obj, 'group'):
                for child in children:
                    if child in obj.group.students.all():
                        return True
                        
        return False

class IsLessonOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение владельцу занятия (преподавателю) или администратору
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.teacher == request.user

class IsGroupTeacherOrAdmin(permissions.BasePermission):
    """
    Разрешение преподавателю группы или администратору
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.teacher == request.user

class IsStudentOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение владельцу студента или администратору
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if request.user.is_teacher:
            # Преподаватель может видеть студентов своей группы
            if hasattr(obj, 'groups'):
                for group in obj.groups.all():
                    if group.teacher == request.user:
                        return True
        return obj == request.user

class IsProgressOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение владельцу прогресса или администратору
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if request.user.is_teacher:
            # Преподаватель может видеть прогресс студентов своей группы
            if hasattr(obj, 'student'):
                for group in obj.student.learning_groups.all():
                    if group.teacher == request.user:
                        return True
        return obj.student == request.user

class IsVideoLessonOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение владельцу видеоурока или администратору
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if hasattr(obj, 'lesson'):
            return obj.lesson.teacher == request.user
        return False

class CanViewLessonChat(permissions.BasePermission):
    """
    Разрешение на просмотр чата урока
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if hasattr(obj, 'lesson'):
            lesson = obj.lesson
            if lesson.teacher == request.user:
                return True
            if lesson.lesson_type == 'group' and request.user in lesson.group.students.all():
                return True
            if lesson.lesson_type == 'individual' and lesson.student == request.user:
                return True
        return False

class CanSubmitHomework(permissions.BasePermission):
    """
    Разрешение на сдачу домашнего задания
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if hasattr(obj, 'student'):
            return obj.student == request.user
        return False

class CanGradeHomework(permissions.BasePermission):
    """
    Разрешение на оценку домашнего задания
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if hasattr(obj, 'homework'):
            return obj.homework.lesson.teacher == request.user
        return False

class CanManageMaterials(permissions.BasePermission):
    """
    Разрешение на управление материалами урока
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if hasattr(obj, 'lesson'):
            return obj.lesson.teacher == request.user
        return False

class CanViewSupportTicket(permissions.BasePermission):
    """
    Разрешение на просмотр тикета поддержки
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.user == request.user or obj.assigned_to == request.user

class CanManageSupportTicket(permissions.BasePermission):
    """
    Разрешение на управление тикетом поддержки
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.assigned_to == request.user

# === НОВЫЕ РАЗРЕШЕНИЯ ДЛЯ УВЕДОМЛЕНИЙ ===

class CanManageNotifications(permissions.BasePermission):
    """
    Разрешение на управление уведомлениями (администраторам и преподавателям)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or request.user.is_teacher
        )
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.user == request.user

class IsNotificationRecipient(permissions.BasePermission):
    """
    Разрешение получателю уведомления
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.user == request.user

class CanSendNotifications(permissions.BasePermission):
    """
    Разрешение на отправку уведомлений
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or request.user.is_teacher
        )

class CanViewNotificationTemplates(permissions.BasePermission):
    """
    Разрешение на просмотр шаблонов уведомлений
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or request.user.is_teacher
        )

class CanManageNotificationTemplates(permissions.BasePermission):
    """
    Разрешение на управление шаблонами уведомлений (только админам)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin

class CanViewUserNotificationSettings(permissions.BasePermission):
    """
    Разрешение на просмотр настроек уведомлений пользователя
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.user == request.user

class CanManageUserNotificationSettings(permissions.BasePermission):
    """
    Разрешение на управление настройками уведомлений пользователя
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.user == request.user

class CanViewNotificationLogs(permissions.BasePermission):
    """
    Разрешение на просмотр логов уведомлений
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin

class CanManageNotificationLogs(permissions.BasePermission):
    """
    Разрешение на управление логами уведомлений (только админам)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin