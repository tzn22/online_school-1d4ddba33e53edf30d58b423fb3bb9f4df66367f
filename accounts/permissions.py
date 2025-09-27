from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение только для администраторов на запись
    """
    def has_permission(self, request, view):
        # Разрешаем чтение всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Запись только администраторам
        return request.user.is_authenticated and request.user.is_admin

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение только владельцу объекта или администратору
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        # Владелец может всё со своим объектом
        return obj == request.user

class IsParentOrAdmin(permissions.BasePermission):
    """
    Разрешение только родителям или администраторам
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_parent or request.user.is_admin
        )

class IsStudentOrParent(permissions.BasePermission):
    """
    Разрешение только студентам или их родителям
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Администратор может всё
        if request.user.is_admin:
            return True
            
        # Студент может видеть свой профиль
        if request.user.is_student and obj == request.user:
            return True
            
        # Родитель может видеть профиль своего ребенка
        if request.user.is_parent:
            return obj.parent == request.user
            
        return False