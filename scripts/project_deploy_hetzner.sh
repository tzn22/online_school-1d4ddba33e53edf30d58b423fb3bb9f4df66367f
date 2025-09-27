#!/bin/bash

# Скрипт для деплоя проекта на сервер Hetzner

echo "=== Деплой проекта на сервер Hetzner ==="

PROJECT_DIR="/var/www/online_school"
BACKUP_DIR="/var/backups/online_school"
LOG_DIR="/var/log/online_school"

# Создание директорий
sudo mkdir -p $PROJECT_DIR
sudo mkdir -p $BACKUP_DIR
sudo mkdir -p $LOG_DIR

# Установка прав доступа
sudo chown -R $USER:$USER $PROJECT_DIR
sudo chown -R $USER:$USER $BACKUP_DIR
sudo chown -R $USER:$USER $LOG_DIR

# Клонирование репозитория (или копирование файлов)
if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "Клонирование репозитория..."
    git clone https://github.com/yourusername/online_school.git $PROJECT_DIR
else
    echo "Обновление репозитория..."
    cd $PROJECT_DIR
    git pull origin main
fi

# Создание .env файла если его нет
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Создание .env файла..."
    cat > $PROJECT_DIR/.env << EOF
# Database settings
DB_NAME=online_school_prod
DB_USER=online_school_user
DB_PASSWORD=$(openssl rand -base64 32)
DB_HOST=db
DB_PORT=5432

# Redis settings
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Django settings
DEBUG=False
SECRET_KEY=$(openssl rand -base64 50)
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com,www.your-domain.com,$(hostname -I | awk '{print $1}')

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Payment settings
YOOKASSA_SHOP_ID=your_production_shop_id
YOOKASSA_SECRET_KEY=your_production_secret_key
YOOKASSA_RETURN_URL=https://your-domain.com/payment-success/

# CORS settings
CORS_ALLOWED_ORIGINS=https://your-domain.com
EOF
fi

# Переход в директорию проекта
cd $PROJECT_DIR

# Установка Docker если не установлен
if ! command -v docker &> /dev/null; then
    echo "Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# Установка Docker Compose если не установлен
if ! command -v docker-compose &> /dev/null; then
    echo "Установка Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
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

# Выполнение миграций
echo "Выполнение миграций..."
docker-compose exec web python manage.py migrate

# Создание суперпользователя
echo "Создание суперпользователя..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@your-domain.com', 'admin_password_here')" | docker-compose exec web python manage.py shell

# Сбор статических файлов
echo "Сбор статических файлов..."
docker-compose exec web python manage.py collectstatic --noinput

echo "=== Проект успешно задеплоен! ==="
echo ""
echo "Доступ к приложению:"
echo "- Веб-интерфейс: http://$(hostname -I | awk '{print $1}'):8000"
echo "- Админка: http://$(hostname -I | awk '{print $1}'):8000/admin/"
echo ""
echo "Следующие шаги:"
echo "1. Настройте Nginx как reverse proxy"
echo "2. Получите SSL сертификат"
echo "3. Настройте домен DNS"