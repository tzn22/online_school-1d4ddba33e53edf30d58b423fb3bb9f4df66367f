from rest_framework import permissions

class IsPaymentOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение владельцу платежа или администратору
    """
    def has_object_permission(self, request, view, obj):
        # Администратор может всё
        if request.user.is_admin:
            return True
        
        # Для платежей, подписок, счетов и возвратов
        if hasattr(obj, 'student'):
            student = obj.student
        elif hasattr(obj, 'payment'):
            student = obj.payment.student
        else:
            return False
        
        # Владелец может просматривать
        if request.user == student:
            return True
        
        # Родитель может просматривать платежи своих детей
        if request.user.is_parent and student.parent == request.user:
            return True
            
        return False

class IsAdminOnly(permissions.BasePermission):
    """
    Разрешение только администраторам
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_admin

class IsStudentOrParent(permissions.BasePermission):
    """
    Разрешение студентам и их родителям
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_student or request.user.is_parent or request.user.is_admin
        )
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
            
        if hasattr(obj, 'student'):
            student = obj.student
        else:
            return False
            
        if request.user.is_student and request.user == student:
            return True
            
        if request.user.is_parent and student.parent == request.user:
            return True
            
        return False