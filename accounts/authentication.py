from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class CustomJWTAuthentication(JWTAuthentication):
    """
    Кастомная JWT аутентификация с дополнительной проверкой
    """
    
    def authenticate(self, request):
        # Сначала используем стандартную JWT аутентификацию
        result = super().authenticate(request)
        
        if result is None:
            return None
            
        user, token = result
        
        # Дополнительные проверки
        if not user.is_active:
            raise AuthenticationFailed(_('Пользователь деактивирован'))
            
        # Можно добавить дополнительные проверки, например:
        # - Проверка на блокировку пользователя
        # - Проверка прав доступа по IP
        # - Логирование входов
        
        return user, token

class RoleBasedAuthentication(BaseAuthentication):
    """
    Аутентификация с проверкой роли пользователя
    """
    
    def authenticate(self, request):
        # Получаем пользователя через JWT
        jwt_auth = CustomJWTAuthentication()
        result = jwt_auth.authenticate(request)
        
        if result is None:
            return None
            
        user, token = result
        return user, token
    
    def authenticate_header(self, request):
        return 'Bearer'

class AdminOnlyAuthentication(BaseAuthentication):
    """
    Аутентификация только для администраторов
    """
    
    def authenticate(self, request):
        jwt_auth = CustomJWTAuthentication()
        result = jwt_auth.authenticate(request)
        
        if result is None:
            return None
            
        user, token = result
        
        if not user.is_admin:
            raise AuthenticationFailed(_('Доступ разрешен только администраторам'))
            
        return user, token
    
    def authenticate_header(self, request):
        return 'Bearer'

class TeacherOnlyAuthentication(BaseAuthentication):
    """
    Аутентификация только для преподавателей
    """
    
    def authenticate(self, request):
        jwt_auth = CustomJWTAuthentication()
        result = jwt_auth.authenticate(request)
        
        if result is None:
            return None
            
        user, token = result
        
        if not user.is_teacher:
            raise AuthenticationFailed(_('Доступ разрешен только преподавателям'))
            
        return user, token
    
    def authenticate_header(self, request):
        return 'Bearer'

class StudentParentAuthentication(BaseAuthentication):
    """
    Аутентификация для студентов и родителей
    """
    
    def authenticate(self, request):
        jwt_auth = CustomJWTAuthentication()
        result = jwt_auth.authenticate(request)
        
        if result is None:
            return None
            
        user, token = result
        
        if not (user.is_student or user.is_parent):
            raise AuthenticationFailed(_('Доступ разрешен только студентам и родителям'))
            
        return user, token
    
    def authenticate_header(self, request):
        return 'Bearer'

# Фабрика аутентификации по роли
def get_role_authentication(allowed_roles):
    """
    Фабрика для создания аутентификации по списку разрешенных ролей
    
    Args:
        allowed_roles (list): Список разрешенных ролей
    
    Returns:
        CustomRoleAuthentication: Класс аутентификации
    """
    
    class CustomRoleAuthentication(BaseAuthentication):
        def authenticate(self, request):
            jwt_auth = CustomJWTAuthentication()
            result = jwt_auth.authenticate(request)
            
            if result is None:
                return None
                
            user, token = result
            
            if user.role not in allowed_roles:
                raise AuthenticationFailed(
                    _('Доступ разрешен только для ролей: {}').format(', '.join(allowed_roles))
                )
                
            return user, token
        
        def authenticate_header(self, request):
            return 'Bearer'
    
    return CustomRoleAuthentication