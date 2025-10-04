# livesmart/permissions.py
from rest_framework import permissions

class IsRoomParticipant(permissions.BasePermission):
    """Разрешение участникам комнаты"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        
        lesson = obj.lesson
        user = request.user
        
        # Хост может всё
        if lesson.teacher == user:
            return True
        
        # Студенты могут видеть свои комнаты
        if user.is_student:
            if lesson.lesson_type == 'group' and lesson.group:
                return user in lesson.group.students.all()
            elif lesson.lesson_type == 'individual' and lesson.student:
                return user == lesson.student
        
        # Родители могут видеть комнаты своих детей
        if user.is_parent:
            children = user.children.all()
            if lesson.lesson_type == 'group' and lesson.group:
                for child in children:
                    if child in lesson.group.students.all():
                        return True
            elif lesson.lesson_type == 'individual' and lesson.student:
                for child in children:
                    if child == lesson.student:
                        return True
        
        return False

class IsRoomHost(permissions.BasePermission):
    """Разрешение хосту комнаты (преподавателю)"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.lesson.teacher == request.user

class IsRecordingOwner(permissions.BasePermission):
    """Разрешение владельцу записи"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.uploaded_by == request.user or obj.room.lesson.teacher == request.user

class IsSettingsOwner(permissions.BasePermission):
    """Разрешение владельцу настроек"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.user == request.user

class CanJoinRoom(permissions.BasePermission):
    """Разрешение на присоединение к комнате"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        
        lesson = obj.lesson
        user = request.user
        
        # Хост может присоединяться
        if lesson.teacher == user:
            return True
        
        # Студенты могут присоединяться к своим занятиям
        if user.is_student:
            if lesson.lesson_type == 'group' and lesson.group:
                return user in lesson.group.students.all()
            elif lesson.lesson_type == 'individual' and lesson.student:
                return user == lesson.student
        
        # Родители могут присоединяться к занятиям своих детей
        if user.is_parent:
            children = user.children.all()
            if lesson.lesson_type == 'group' and lesson.group:
                for child in children:
                    if child in lesson.group.students.all():
                        return True
            elif lesson.lesson_type == 'individual' and lesson.student:
                for child in children:
                    if child == lesson.student:
                        return True
        
        return False

class CanManageRoom(permissions.BasePermission):
    """Разрешение на управление комнатой"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.lesson.teacher == request.user

class CanViewRecording(permissions.BasePermission):
    """Разрешение на просмотр записи"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        
        # Публичные записи доступны всем
        if obj.is_public:
            return True
        
        # Преподаватель может видеть записи своих занятий
        if request.user.is_teacher:
            return obj.room.lesson.teacher == request.user
        
        # Студенты могут видеть записи своих занятий
        if request.user.is_student:
            lesson = obj.room.lesson
            if lesson.lesson_type == 'group' and lesson.group:
                return request.user in lesson.group.students.all()
            elif lesson.lesson_type == 'individual' and lesson.student:
                return request.user == lesson.student
        
        # Родители могут видеть записи занятий своих детей
        if request.user.is_parent:
            children = request.user.children.all()
            lesson = obj.room.lesson
            if lesson.lesson_type == 'group' and lesson.group:
                for child in children:
                    if child in lesson.group.students.all():
                        return True
            elif lesson.lesson_type == 'individual' and lesson.student:
                for child in children:
                    if child == lesson.student:
                        return True
        
        return False