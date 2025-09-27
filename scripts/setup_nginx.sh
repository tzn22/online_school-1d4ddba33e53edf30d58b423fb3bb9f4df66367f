#!/bin/bash

# Скрипт для настройки Nginx

echo "=== Настройка Nginx ==="

# Установка Nginx если не установлен
if ! command -v nginx &> /dev/null
then
    echo "📦 Установка Nginx..."
    apt update
    apt install -y nginx
fi

# Запуск Nginx
systemctl start nginx
systemctl enable nginx

# Создание конфигурации сайта
echo "🔧 Создание конфигурации сайта..."
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

# Adminer for database management
server {
    listen 8080;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Включение сайта
ln -sf /etc/nginx/sites-available/online_school /etc/nginx/sites-enabled/

# Удаление default сайта
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации
echo "🔍 Проверка конфигурации Nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "🔄 Перезапуск Nginx..."
    systemctl reload nginx
    echo "✅ Nginx настроен!"
else
    echo "❌ Ошибка в конфигурации Nginx!"
    exit 1
fi

echo ""
echo "Доступ к приложению:"
echo "- Основное приложение: http://your-domain.com"
echo "- Админка: http://your-domain.com/admin/"
echo "- Adminer: http://your-domain.com:8080"