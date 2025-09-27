from rest_framework import permissions

class IsFeedbackOwner(permissions.BasePermission):
    """
    Разрешение владельцу отзыва или администратору
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Владелец отзыва может просматривать и редактировать
        if request.user == obj.student:
            return True
        
        # Преподаватель может просматривать отзывы о себе
        if hasattr(obj, 'teacher') and obj.teacher == request.user:
            return True
            
        return False

class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Разрешение преподавателям или администраторам
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_teacher or request.user.is_admin
        )

class CanRespondToFeedback(permissions.BasePermission):
    """
    Разрешение на ответ на отзыв
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Преподаватель может отвечать на отзывы о себе
        if hasattr(obj, 'teacher') and obj.teacher == request.user:
            return True
            
        return False

class IsSurveyRespondent(permissions.BasePermission):
    """
    Разрешение респонденту опроса
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Респондент может просматривать свои ответы
        if hasattr(obj, 'respondent') and obj.respondent == request.user:
            return True
            
        return False