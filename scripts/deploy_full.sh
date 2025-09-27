#!/bin/bash

# Полный скрипт деплоя проекта на сервер

echo "🚀 Полный деплой проекта онлайн-школы"
echo "====================================="
echo "IP: 116.203.145.245"
echo "User: root"
echo ""

# Проверка прав доступа
if [ "$EUID" -ne 0 ]
  then echo "Пожалуйста, запустите скрипт от имени root"
  exit
fi

# Обновление системы
echo "🔄 Обновление системы..."
apt update && apt upgrade -y

# Установка необходимых пакетов
echo "📦 Установка необходимых пакетов..."
apt install -y \
    curl wget git vim nano htop net-tools ufw fail2ban nginx certbot \
    python3-certbot-nginx postgresql postgresql-contrib redis-server \
    docker.io docker-compose supervisor nodejs npm unzip zip tar gzip \
    bzip2 rsync openssh-server python3-pip python3-venv

# Добавление пользователя в группу docker
usermod -aG docker root

# Настройка firewall
echo "🛡 Настройка firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Настройка fail2ban
echo "🔒 Настройка fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Создание swap файла
echo "💾 Создание swap файла..."
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab

# Настройка времени
echo "⏰ Настройка времени..."
timedatectl set-timezone Europe/Moscow

# Создание директорий проекта
echo "📁 Создание директорий..."
mkdir -p /var/www/online_school
mkdir -p /var/backups/online_school
mkdir -p /var/log/online_school
mkdir -p /var/www/online_school/{staticfiles,media,logs,data}

# Установка прав доступа
chown -R root:root /var/www/online_school
chmod -R 755 /var/www/online_school

# Клонирование репозитория
echo "📥 Клонирование репозитория..."
cd /var/www/online_school
git clone https://github.com/yourusername/online_school.git .

# Создание .env файла
echo "🔧 Создание .env файла..."
cat > .env << EOF
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

# Настройка базы данных PostgreSQL
echo "🔧 Настройка базы данных..."
sudo -u postgres psql << EOF
CREATE USER online_school_user WITH PASSWORD '$(grep DB_PASSWORD .env | cut -d'=' -f2)';
CREATE DATABASE online_school_prod WITH OWNER online_school_user;
GRANT ALL PRIVILEGES ON DATABASE online_school_prod TO online_school_user;
ALTER USER online_school_user CREATEDB;
\q
EOF

# Сборка и запуск Docker контейнеров
echo "🐳 Сборка и запуск Docker контейнеров..."
docker-compose build
docker-compose up -d

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
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
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Root path
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }

    # Static files
    location /static/ {
        alias /var/www/online_school/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip_static on;
    }

    # Media files
    location /media/ {
        alias /var/www/online_school/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # API endpoints with rate limiting
    location ~ ^/api/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Rate limiting for API
        limit_req zone=api burst=10 nodelay;
    }

    # Login endpoints with stricter rate limiting
    location ~ ^/(api/auth/login|admin/login)/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Stricter rate limiting for login
        limit_req zone=login burst=3 nodelay;
    }

    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
EOF

# Включение сайта Nginx
ln -sf /etc/nginx/sites-available/online_school /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка и перезапуск Nginx
nginx -t && systemctl reload nginx

# Настройка автоматических обновлений
echo "🔄 Настройка автоматических обновлений..."
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Настройка мониторинга
echo "📊 Настройка мониторинга..."
cat > /usr/local/bin/system_monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Monitor ==="
echo "Date: $(date)"
echo "Load: $(uptime | awk -F'load average:' '{ print $2 }')"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"
echo "Processes: $(ps aux | wc -l)"
echo "Users: $(who | wc -l)"
EOF

chmod +x /usr/local/bin/system_monitor.sh

# Добавление в cron
echo "0 * * * * /usr/local/bin/system_monitor.sh >> /var/log/system_monitor.log 2>&1" | crontab -

echo "✅ Полный деплой завершен!"
echo ""
echo "Доступ к приложению:"
echo "- Веб-интерфейс: http://$(hostname -I | awk '{print $1}')"
echo "- Админка: http://$(hostname -I | awk '{print $1}')/admin/"
echo ""
echo "Учетные данные администратора:"
echo "- Логин: admin"
echo "- Пароль: admin_password_here"
echo ""
echo "Следующие шаги:"
echo "1. Настройте домен DNS"
echo "2. Получите SSL сертификат"
echo "3. Настройте мониторинг"
echo "4. Проверьте работу всех сервисов"