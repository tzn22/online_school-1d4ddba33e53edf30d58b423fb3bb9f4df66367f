#!/bin/bash

# Скрипт для полной настройки проекта с базой данных

echo "=== Полная настройка проекта онлайн-школы ==="

# Проверка наличия Python
if ! command -v python3 &> /dev/null
then
    echo "Python 3 не установлен!"
    exit 1
fi

# Проверка наличия PostgreSQL
if ! command -v psql &> /dev/null
then
    echo "PostgreSQL не установлен!"
    echo "Пожалуйста, установите PostgreSQL:"
    echo "Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "macOS: brew install postgresql"
    echo "Windows: Скачайте с https://www.postgresql.org/download/"
    exit 1
fi

# Проверка наличия Redis
if ! command -v redis-cli &> /dev/null
then
    echo "Redis не установлен!"
    echo "Пожалуйста, установите Redis:"
    echo "Ubuntu/Debian: sudo apt install redis"
    echo "macOS: brew install redis"
    echo "Windows: Скачайте с https://redis.io/download/"
    exit 1
fi

# Создание виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# source venv/Scripts/activate  # Windows

# Установка зависимостей
echo "Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Настройка базы данных PostgreSQL
echo "Настройка базы данных PostgreSQL..."
DB_NAME=${DB_NAME:-online_school}
DB_USER=${DB_USER:-online_school_user}
DB_PASSWORD=${DB_USER:-online_school_pass}

# Создание пользователя PostgreSQL
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "Пользователь уже существует"

# Создание базы данных
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME WITH OWNER $DB_USER;" 2>/dev/null || echo "База данных уже существует"

# Назначение привилегий
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"

# Создание .env файла если его нет
if [ ! -f .env ]; then
    echo "Создание .env файла..."
    cat > .env << EOF
# Database settings
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

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
YOOKASSA_RETURN_URL=http://localhost:3000/payment-success/

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000
EOF
    echo ".env файл создан"
fi

# Создание миграций
echo "Создание миграций..."
python manage.py makemigrations

# Применение миграций
echo "Применение миграций..."
python manage.py migrate

# Создание суперпользователя
echo "Создание суперпользователя..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell

# Сбор статических файлов
echo "Сбор статических файлов..."
python manage.py collectstatic --noinput

echo "=== Проект успешно настроен! ==="
echo ""
echo "Для запуска проекта используйте:"
echo "1. source venv/bin/activate  # Активировать виртуальное окружение"
echo "2. python manage.py runserver  # Запустить сервер разработки"
echo ""
echo "Доступ к админке: http://localhost:8000/admin/"
echo "Логины: admin / admin"