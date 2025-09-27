#!/bin/bash

# Скрипт для восстановления базы данных из резервной копии

echo "=== Восстановление базы данных ==="

# Переменные
BACKUP_DIR="./backups"
DB_NAME=${DB_NAME:-online_school}
DB_USER=${DB_USER:-online_school_user}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

# Проверка наличия бэкапов
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Директория с бэкапами не найдена!"
    exit 1
fi

# Список доступных бэкапов
echo "Доступные бэкапы:"
ls -t "$BACKUP_DIR"/backup_* 2>/dev/null || echo "Нет доступных бэкапов"

if [ $# -eq 0 ]; then
    echo "Использование: $0 <путь_к_файлу_бэкапа>"
    exit 1
fi

BACKUP_FILE="$1"

# Проверка существования файла
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Файл бэкапа не найден: $BACKUP_FILE"
    exit 1
fi

echo "Восстановление из: $BACKUP_FILE"

# Подтверждение
read -p "Вы уверены, что хотите восстановить базу данных? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Отменено"
    exit 1
fi

# Остановка сервера Django
pkill -f "python.*manage.py runserver" 2>/dev/null

# Восстановление в зависимости от типа файла
if [[ "$BACKUP_FILE" == *.sql ]]; then
    # PostgreSQL SQL файл
    if command -v psql &> /dev/null
    then
        # Удаление существующей базы данных
        dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null || true
        createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
        
        # Восстановление из SQL файла
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE"
        
        if [ $? -eq 0 ]; then
            echo "База данных успешно восстановлена из SQL файла!"
        else
            echo "Ошибка восстановления из SQL файла!"
            exit 1
        fi
    else
        echo "psql не найден!"
        exit 1
    fi
elif [[ "$BACKUP_FILE" == *.db ]]; then
    # SQLite файл
    if [ -f "db.sqlite3" ]; then
        rm "db.sqlite3"
    fi
    cp "$BACKUP_FILE" "db.sqlite3"
    echo "База данных SQLite успешно восстановлена!"
else
    echo "Неподдерживаемый формат файла бэкапа!"
    exit 1
fi

echo "=== Восстановление завершено ==="