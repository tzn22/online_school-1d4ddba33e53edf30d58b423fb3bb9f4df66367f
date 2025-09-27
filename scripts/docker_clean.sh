#!/bin/bash

# Скрипт для очистки Docker контейнеров и данных

echo "=== Очистка Docker контейнеров и данных ==="

# Подтверждение
read -p "Вы уверены, что хотите удалить все контейнеры и данные? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Отменено"
    exit 1
fi

# Остановка контейнеров
echo "Остановка контейнеров..."
docker-compose down -v

# Удаление volumes
echo "Удаление volumes..."
docker volume rm online_school_postgres_data 2>/dev/null || true
docker volume rm online_school_redis_data 2>/dev/null || true
docker volume rm online_school_static_volume 2>/dev/null || true
docker volume rm online_school_media_volume 2>/dev/null || true

# Удаление образов
echo "Удаление образов..."
docker rmi online_school_web 2>/dev/null || true

# Очистка dangling ресурсов
echo "Очистка dangling ресурсов..."
docker system prune -f

echo "=== Очистка завершена ==="