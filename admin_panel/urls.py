from django.urls import path, include
from django.contrib import admin
from .admin import custom_admin_site

urlpatterns = [
    path('admin/', admin.site.urls),
    path('custom-admin/', custom_admin_site.urls),
]