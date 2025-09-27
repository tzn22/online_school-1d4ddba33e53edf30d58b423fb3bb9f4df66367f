#!/bin/bash

# Скрипт для запуска всех сервисов проекта

echo "=== Запуск всех сервисов онлайн-школы ==="

# Проверка наличия необходимых сервисов
echo "Проверка необходимых сервисов..."

# Запуск PostgreSQL (если не запущен)
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "Запуск PostgreSQL..."
    sudo systemctl start postgresql || echo "Не удалось запустить PostgreSQL"
else
    echo "PostgreSQL уже запущен"
fi

# Запуск Redis (если не запущен)
if ! redis-cli ping >/dev/null 2>&1; then
    echo "Запуск Redis..."
    redis-server --daemonize yes || echo "Не удалось запустить Redis"
else
    echo "Redis уже запущен"
fi

# Активация виртуального окружения
if [ -d "venv" ]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate  # Linux/macOS
    # source venv/Scripts/activate  # Windows
else
    echo "Создание виртуального окружения..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Проверка подключения к базе данных
echo "Проверка подключения к базе данных..."
python scripts/test_database_connection.py

# Применение миграций если нужно
echo "Проверка миграций..."
python manage.py migrate

# Запуск Celery worker в фоне
echo "Запуск Celery worker..."
celery -A config worker --loglevel=info --detach

# Запуск Celery beat в фоне
echo "Запуск Celery beat..."
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler --detach

# Запуск Django сервера
echo "Запуск Django сервера..."
echo "Сервер доступен по адресу: http://localhost:8000"
echo "Админка: http://localhost:8000/admin/"
echo "Swagger: http://localhost:8000/swagger/"
echo "Нажмите Ctrl+C для остановки"

python manage.py runserver 0.0.0.0:8000