#!/bin/bash

# Скрипт для восстановления из резервной копии

echo "=== Восстановление из резервной копии ==="

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Использование: $0 <backup_file>"
    echo "Пример: $0 /var/backups/online_school/online_school_backup_20231015_143022.tar.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Файл бэкапа не найден: $BACKUP_FILE"
    exit 1
fi

# Подтверждение
echo "Вы уверены, что хотите восстановить из $BACKUP_FILE?"
echo "Все текущие данные будут потеряны!"
read -p "Продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Отменено"
    exit 1
fi

# Остановка сервисов
echo "⏹ Остановка сервисов..."
systemctl stop nginx
systemctl stop postgresql
systemctl stop redis-server

# Распаковка бэкапа
echo "📦 Распаковка бэкапа..."
TEMP_DIR="/tmp/online_school_restore"
mkdir -p $TEMP_DIR
tar -xzf $BACKUP_FILE -C $TEMP_DIR

# Восстановление базы данных
echo "💾 Восстановление базы данных..."
sudo -u postgres dropdb online_school_prod 2>/dev/null || true
sudo -u postgres createdb online_school_prod
sudo -u postgres psql -d online_school_prod -f $TEMP_DIR/*/postgres_backup.sql

# Восстановление Redis
echo "💾 Восстановление Redis..."
cp $TEMP_DIR/*/redis_backup.rdb /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb

# Восстановление файлов проекта
echo "💾 Восстановление файлов проекта..."
tar -xzf $TEMP_DIR/*/project_files.tar.gz -C /

# Восстановление конфигураций
echo "💾 Восстановление конфигураций..."
cp $TEMP_DIR/*/configs/* /etc/nginx/sites-available/ 2>/dev/null || true
cp $TEMP_DIR/*/configs/.env /var/www/online_school/ 2>/dev/null || true

# Удаление временной директории
rm -rf $TEMP_DIR

# Перезапуск сервисов
echo "🚀 Перезапуск сервисов..."
systemctl start postgresql
systemctl start redis-server
systemctl start nginx

# Перезапуск Docker контейнеров
echo "🐳 Перезапуск Docker контейнеров..."
cd /var/www/online_school
docker-compose down
docker-compose up -d

echo "✅ Восстановление завершено!"
echo "Проверьте работу сервисов:"
echo "- http://your-domain.com"
echo "- http://your-domain.com/admin/"