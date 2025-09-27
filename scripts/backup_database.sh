#!/bin/bash

# Скрипт для создания резервной копии базы данных

echo "=== Создание резервной копии базы данных ==="

# Переменные
BACKUP_DIR="./backups"
DATE=$(date +"%Y%m%d_%H%M%S")
DB_NAME=${DB_NAME:-online_school}
DB_USER=${DB_USER:-online_school_user}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

# Создание резервной копии
if command -v pg_dump &> /dev/null
then
    # Используем pg_dump для PostgreSQL
    BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo "Резервная копия создана: $BACKUP_FILE"
        echo "Размер: $(du -h "$BACKUP_FILE" | cut -f1)"
    else
        echo "Ошибка создания резервной копии!"
        exit 1
    fi
else
    echo "pg_dump не найден. Используется SQLite бэкап..."
    # Для SQLite просто копируем файл
    if [ -f "db.sqlite3" ]; then
        BACKUP_FILE="$BACKUP_DIR/backup_sqlite_${DATE}.db"
        cp "db.sqlite3" "$BACKUP_FILE"
        echo "SQLite бэкап создан: $BACKUP_FILE"
    else
        echo "Файл базы данных SQLite не найден!"
        exit 1
    fi
fi

# Удаление старых бэкапов (оставляем последние 10)
cd "$BACKUP_DIR"
ls -t backup_* | tail -n +11 | xargs -r rm --

echo "=== Резервное копирование завершено ==="