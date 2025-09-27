#!/bin/bash

# Скрипт для деплоя проекта на сервер

echo "=== Деплой проекта онлайн-школы ==="
echo "IP: 116.203.145.245"
echo "User: root"
echo ""

PROJECT_DIR="/var/www/online_school"
BACKUP_DIR="/var/backups/online_school"
LOG_DIR="/var/log/online_school"

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p $PROJECT_DIR
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR

# Установка прав доступа
chown -R root:root $PROJECT_DIR
chown -R root:root $BACKUP_DIR
chown -R root:root $LOG_DIR

# Клонирование репозитория
if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "📥 Клонирование репозитория..."
    git clone https://github.com/yourusername/online_school.git $PROJECT_DIR
else
    echo "🔄 Обновление репозитория..."
    cd $PROJECT_DIR
    git pull origin main
fi

# Переход в директорию проекта
cd $PROJECT_DIR

# Создание .env файла если его нет
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "🔧 Создание .env файла..."
    cat > $PROJECT_DIR/.env << EOF
# Database settings
DB_NAME=online_school_prod
DB_USER=online_school_user
DB_PASSWORD=$(openssl rand -base64 32)
DB_HOST=localhost
DB_PORT=5432

# Redis settings
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Django settings
DEBUG=False
SECRET_KEY=$(openssl rand -base64 50)
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,$(hostname -I | awk '{print $1}'),your-domain.com,www.your-domain.com

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Payment settings
YOOKASSA_SHOP_ID=your_production_shop_id
YOOKASSA_SECRET_KEY=your_production_secret_key
YOOKASSA_RETURN_URL=https://your-domain.com/payment-success/

# CORS settings
CORS_ALLOWED_ORIGINS=https://your-domain.com

# Security settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
EOF
fi

# Установка Docker если не установлен
if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker root
fi

# Установка Docker Compose если не установлен
if ! command -v docker-compose &> /dev/null; then
    echo "🚢 Установка Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Сборка Docker образов
echo "🏗 Сборка Docker образов..."
docker-compose build

# Запуск контейнеров
echo "🚀 Запуск контейнеров..."
docker-compose up -d

# Ожидание запуска базы данных
echo "⏳ Ожидание запуска базы данных..."
sleep 30

# Выполнение миграций
echo "🔄 Выполнение миграций..."
docker-compose exec web python manage.py migrate

# Создание суперпользователя
echo "👤 Создание суперпользователя..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@your-domain.com', 'admin_password_here')" | docker-compose exec web python manage.py shell

# Сбор статических файлов
echo "📦 Сбор статических файлов..."
docker-compose exec web python manage.py collectstatic --noinput

# Настройка Nginx
echo "🌐 Настройка Nginx..."
cat > /etc/nginx/sites-available/online_school << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/online_school/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/online_school/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
EOF

# Включение сайта Nginx
ln -sf /etc/nginx/sites-available/online_school /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "✅ Проект успешно задеплоен!"
echo ""
echo "Доступ к приложению:"
echo "- Веб-интерфейс: http://$(hostname -I | awk '{print $1}'):8000"
echo "- Админка: http://$(hostname -I | awk '{print $1}'):8000/admin/"
echo ""
echo "Следующие шаги:"
echo "1. Настройте домен DNS"
echo "2. Получите SSL сертификат"
echo "3. Настройте мониторинг"