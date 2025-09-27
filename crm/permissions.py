from rest_framework import permissions

class IsAdminOrManager(permissions.BasePermission):
    """
    Разрешение администраторам и менеджерам
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or 
            hasattr(request.user, 'role') and request.user.role == 'manager'
        )
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

class IsAdminUser(permissions.BasePermission):
    """
    Разрешение только администраторам
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_admin

class IsProfileOwner(permissions.BasePermission):
    """
    Разрешение владельцу профиля
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Проверяем, является ли пользователь владельцем профиля
        if hasattr(obj, 'student'):
            return obj.student == request.user
        elif hasattr(obj, 'teacher'):
            return obj.teacher == request.user
            
        return False

class CanViewStudentData(permissions.BasePermission):
    """
    Разрешение на просмотр данных студента
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Преподаватель может видеть данные своих студентов
        if request.user.is_teacher:
            # Проверяем, преподает ли он этому студенту
            return obj.groups.filter(teacher=request.user).exists()
        
        # Студент может видеть свои данные
        if request.user.is_student:
            return obj == request.user
            
        return False

class CanManageLeads(permissions.BasePermission):
    """
    Разрешение на управление лидами
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or 
            hasattr(request.user, 'leads')  # Менеджер по работе с клиентами
        )