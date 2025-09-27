from rest_framework import permissions

class IsChatParticipant(permissions.BasePermission):
    """
    Разрешение только участникам чата
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Проверяем, является ли пользователь участником чата
        return obj.participants.filter(id=request.user.id).exists()

class IsMessageSender(permissions.BasePermission):
    """
    Разрешение только отправителю сообщения
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Только отправитель может редактировать/удалять сообщение
        return obj.sender == request.user

class CanViewChat(permissions.BasePermission):
    """
    Разрешение на просмотр чата
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Только участники чата могут его просматривать
        return request.user in obj.participants.all()

class IsChatCreator(permissions.BasePermission):
    """
    Разрешение только создателю чата
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Только создатель чата может управлять им
        return obj.created_by == request.user