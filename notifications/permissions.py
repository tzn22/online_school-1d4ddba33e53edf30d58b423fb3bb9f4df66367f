from rest_framework import permissions

class IsNotificationOwner(permissions.BasePermission):
    """
    Разрешение только владельцу уведомления
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Только владелец уведомления может его просматривать/редактировать
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