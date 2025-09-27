#!/bin/bash

# Скрипт для резервного копирования

echo "=== Резервное копирование ==="

BACKUP_DIR="/var/backups/online_school"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="online_school_backup_$DATE"

echo "📁 Создание директории для бэкапа..."
mkdir -p $BACKUP_DIR/$BACKUP_NAME

# Бэкап базы данных PostgreSQL
echo "💾 Бэкап базы данных..."
sudo -u postgres pg_dump -d online_school_prod > $BACKUP_DIR/$BACKUP_NAME/postgres_backup.sql

# Бэкап Redis
echo "💾 Бэкап Redis..."
redis-cli BGSAVE
sleep 10
cp /var/lib/redis/dump.rdb $BACKUP_DIR/$BACKUP_NAME/redis_backup.rdb 2>/dev/null || echo "Redis dump не найден"

# Бэкап файлов проекта
echo "💾 Бэкап файлов проекта..."
tar -czf $BACKUP_DIR/$BACKUP_NAME/project_files.tar.gz \
    /var/www/online_school/staticfiles/ \
    /var/www/online_school/media/ \
    /var/www/online_school/logs/ \
    2>/dev/null || echo "Некоторые директории отсутствуют"

# Бэкап конфигурационных файлов
echo "💾 Бэкап конфигураций..."
mkdir -p $BACKUP_DIR/$BACKUP_NAME/configs
cp /etc/nginx/sites-available/online_school $BACKUP_DIR/$BACKUP_NAME/configs/ 2>/dev/null || echo "Nginx конфиг не найден"
cp /var/www/online_school/.env $BACKUP_DIR/$BACKUP_NAME/configs/ 2>/dev/null || echo ".env файл не найден"

# Создание архива всего бэкапа
echo "📦 Создание архива..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}.tar.gz -C $BACKUP_DIR $BACKUP_NAME

# Удаление временной директории
rm -rf $BACKUP_DIR/$BACKUP_NAME

# Удаление старых бэкапов (оставляем последние 10)
echo "🧹 Очистка старых бэкапов..."
cd $BACKUP_DIR
ls -t online_school_backup_*.tar.gz | tail -n +11 | xargs -r rm --

echo "✅ Резервная копия создана: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "📊 Размер: $(du -h $BACKUP_DIR/${BACKUP_NAME}.tar.gz | cut -f1)"
echo "=== Резервное копирование завершено ==="