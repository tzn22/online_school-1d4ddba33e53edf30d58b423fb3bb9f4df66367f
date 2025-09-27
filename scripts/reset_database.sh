#!/bin/bash

# Скрипт для полного сброса базы данных

echo "=== Сброс базы данных ==="

read -p "Вы уверены, что хотите сбросить базу данных? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Отменено"
    exit 1
fi

# Остановка сервера Django
pkill -f "python.*manage.py runserver" 2>/dev/null

# Удаление файлов базы данных (для SQLite)
rm -f db.sqlite3

# Удаление миграций
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

echo "Миграции удалены"

# Создание новых миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Создание суперпользователя
echo "Создание суперпользователя..."
python manage.py createsuperuser --username admin --email admin@example.com

echo "=== База данных сброшена ==="