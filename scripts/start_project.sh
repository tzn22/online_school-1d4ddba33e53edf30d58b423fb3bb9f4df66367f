#!/bin/bash

echo "=== Запуск проекта онлайн-школы ==="

# Проверка наличия Docker
if ! command -v docker &> /dev/null
then
    echo "Docker не установлен!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose не установлен!"
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

# Сборка Docker образов
echo "Сборка Docker образов..."
docker-compose build

# Запуск контейнеров
echo "Запуск контейнеров..."
docker-compose up -d

# Ожидание запуска базы данных
echo "Ожидание запуска базы данных..."
sleep 30

# Проверка состояния контейнеров
echo "Состояние контейнеров:"
docker-compose ps

# Выполнение миграций
echo "Выполнение миграций..."
docker-compose exec web python manage.py migrate

# Создание суперпользователя (опционально)
echo "Создание суперпользователя..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | docker-compose exec web python manage.py shell 2>/dev/null || echo "Создайте суперпользователя вручную"

# Сбор статических файлов
echo "Сбор статических файлов..."
docker-compose exec web python manage.py collectstatic --noinput

echo "=== Проект запущен! ==="
echo ""
echo "Доступ к приложению:"
echo "- Основное приложение: http://localhost:8000"
echo "- Админка Django: http://localhost:8000/admin/"
echo "- Swagger API: http://localhost:8000/swagger/"
echo "- Adminer: http://localhost:8080"
echo "- Redis Commander: http://localhost:8081"
echo ""
echo "Логин для админки: admin / admin (если не изменяли)"