#!/bin/bash

# Скрипт для настройки PostgreSQL для проекта

echo "=== Настройка PostgreSQL для онлайн-школы ==="

# Проверка наличия PostgreSQL
if ! command -v psql &> /dev/null
then
    echo "PostgreSQL не установлен. Пожалуйста, установите PostgreSQL."
    exit 1
fi

# Переменные из .env файла
DB_NAME=${DB_NAME:-online_school}
DB_USER=${DB_USER:-online_school_user}
DB_PASSWORD=${DB_PASSWORD:-online_school_pass}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

echo "Создание базы данных и пользователя..."

# Создание пользователя PostgreSQL
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "Пользователь уже существует"

# Создание базы данных
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME WITH OWNER $DB_USER;" 2>/dev/null || echo "База данных уже существует"

# Назначение привилегий
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"

echo "База данных создана:"
echo "- Название: $DB_NAME"
echo "- Пользователь: $DB_USER"
echo "- Пароль: $DB_PASSWORD"
echo "- Хост: $DB_HOST"
echo "- Порт: $DB_PORT"

# Создание файла .env если его нет
if [ ! -f .env ]; then
    echo "Создание .env файла..."
    cat > .env << EOF
# Database settings
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT

# Redis settings
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Django settings
DEBUG=True
SECRET_KEY=django-insecure-development-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Email settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Payment settings
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000
EOF
    echo ".env файл создан"
fi

echo "=== Настройка PostgreSQL завершена ==="