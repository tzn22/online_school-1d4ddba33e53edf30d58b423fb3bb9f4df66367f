#!/bin/bash

# Скрипт для настройки и запуска Docker контейнеров

echo "=== Настройка Docker для онлайн-школы ==="

# Проверка наличия Docker
if ! command -v docker &> /dev/null
then
    echo "Docker не установлен. Пожалуйста, установите Docker."
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose не установлен. Пожалуйста, установите Docker Compose."
    exit 1
fi

# Создание .env файла если его нет
if [ ! -f .env ]; then
    echo "Создание .env файла..."
    cat > .env << EOF
# Database settings
DB_NAME=online_school
DB_USER=online_school_user
DB_PASSWORD=online_school_pass
DB_HOST=db
DB_PORT=5432

# Redis settings
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Django settings
DEBUG=True
SECRET_KEY=django-insecure-development-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,web

# Email settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Payment settings
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
YOOKASSA_RETURN_URL=http://localhost:3000/payment-success/

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000
EOF
    echo ".env файл создан"
fi

# Создание директорий
mkdir -p staticfiles media logs backups data/postgres data/redis

# Сборка Docker образов
echo "Сборка Docker образов..."
docker-compose build

# Запуск контейнеров
echo "Запуск контейнеров..."
docker-compose up -d

# Ожидание запуска базы данных
echo "Ожидание запуска базы данных..."
sleep 15

# Выполнение миграций
echo "Выполнение миграций..."
docker-compose exec web python manage.py migrate

# Создание суперпользователя
echo "Создание суперпользователя..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | docker-compose exec web python manage.py shell

# Сбор статических файлов
echo "Сбор статических файлов..."
docker-compose exec web python manage.py collectstatic --noinput

echo "=== Docker контейнеры запущены! ==="
echo "Основное приложение: http://localhost:8000"
echo "Админка Django: http://localhost:8000/admin/"
echo ""
echo "Состояние контейнеров:"
docker-compose ps