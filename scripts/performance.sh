#!/bin/bash

# Скрипт для оптимизации производительности сервера

echo "=== Оптимизация производительности сервера ==="

# Оптимизация PostgreSQL
echo "⚙️ Оптимизация PostgreSQL..."
PG_VERSION=$(psql -V | grep -o '[0-9]*\.[0-9]*')
PG_CONF="/etc/postgresql/$PG_VERSION/main/postgresql.conf"

# Резервное копирование конфига
cp $PG_CONF ${PG_CONF}.bak

# Оптимизация параметров PostgreSQL
cat >> $PG_CONF << 'EOF'

# Performance optimizations for Online School
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
max_connections = 100
EOF

systemctl restart postgresql

# Оптимизация Redis
echo "⚙️ Оптимизация Redis..."
REDIS_CONF="/etc/redis/redis.conf"

# Резервное копирование конфига
cp $REDIS_CONF ${REDIS_CONF}.bak

# Оптимизация параметров Redis
cat >> $REDIS_CONF << 'EOF'

# Performance optimizations for Online School
maxmemory 256mb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 300
save 900 1
save 300 10
save 60 10000
EOF

systemctl restart redis-server

# Оптимизация Nginx
echo "⚙️ Оптимизация Nginx..."
NGINX_CONF="/etc/nginx/nginx.conf"

# Резервное копирование конфига
cp $NGINX_CONF ${NGINX_CONF}.bak

# Добавление оптимизаций в Nginx
sed -i '/http {/a \    # Performance optimizations\n    worker_connections 1024;\n    multi_accept on;\n    use epoll;' $NGINX_CONF

# Добавление кэширования
cat >> $NGINX_CONF << 'EOF'

    # Cache settings
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=10g inactive=60m use_temp_path=off;
    
    # Gzip settings
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
EOF

systemctl reload nginx

# Оптимизация Docker
echo "⚙️ Оптимизация Docker..."
DOCKER_DAEMON="/etc/docker/daemon.json"

# Создание конфига Docker
cat > $DOCKER_DAEMON << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.override_kernel_check=true"
    ]
}
EOF

systemctl restart docker

# Оптимизация системы
echo "⚙️ Оптимизация системы..."

# Увеличение лимитов
cat >> /etc/security/limits.conf << 'EOF'
# Increase limits for Online School
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
EOF

# Настройка sysctl
cat >> /etc/sysctl.conf << 'EOF'
# Network optimizations for Online School
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 1
EOF

sysctl -p

# Очистка кэша и временных файлов
echo "🧹 Очистка кэша..."
apt autoremove -y
apt autoclean
docker system prune -af
journalctl --vacuum-time=7d

echo "✅ Оптимизация производительности завершена!"
echo ""
echo "Оптимизированы компоненты:"
echo "- PostgreSQL: настроены параметры производительности"
echo "- Redis: оптимизированы настройки кэширования"
echo "- Nginx: включено кэширование и сжатие"
echo "- Docker: настроены логи и хранилище"
echo "- Система: увеличены лимиты и оптимизированы параметры ядра"