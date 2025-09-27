"""
Production settings for Online School project.
"""
from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'fluencyclub.fun',
    'www.fluencyclub.fun',
    '116.203.145.245'  # IP сервера
]
CORS_ALLOWED_ORIGINS = [
    'https://fluencyclub.fun',
    'https://www.fluencyclub.fun',
    'http://fluencyclub.fun',
    'http://www.fluencyclub.fun',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

CORS_ALLOW_ALL_ORIGINS = True
# CSRF и CORS настройки
CSRF_TRUSTED_ORIGINS = [
    'https://fluencyclub.fun',
    'https://www.fluencyclub.fun',
    'http://fluencyclub.fun',
    'http://www.fluencyclub.fun'
]

CORS_ALLOWED_ORIGINS = [
    'https://fluencyclub.fun',
    'https://www.fluencyclub.fun',
    'http://fluencyclub.fun',
    'http://www.fluencyclub.fun'
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Logging for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/online_school.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
