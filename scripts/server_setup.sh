#!/bin/bash

# Скрипт для настройки сервера для онлайн-школы

echo "=== Настройка сервера для онлайн-школы ==="
echo "IP: 116.203.145.245"
echo "User: root"
echo ""

# Обновление системы
echo "🔄 Обновление системы..."
apt update && apt upgrade -y

# Установка необходимых пакетов
echo "📦 Установка необходимых пакетов..."
apt install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    net-tools \
    ufw \
    fail2ban \
    nginx \
    certbot \
    python3-certbot-nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    docker.io \
    docker-compose \
    supervisor \
    nodejs \
    npm \
    unzip \
    zip \
    tar \
    gzip \
    bzip2 \
    rsync \
    openssh-server \
    openssh-client

# Добавление текущего пользователя в группу docker
usermod -aG docker root

# Настройка firewall (UFW)
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

# Создание swap файла (если мало RAM)
echo "💾 Создание swap файла..."
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab

# Настройка времени (NTP)
echo "⏰ Настройка времени..."
timedatectl set-timezone Europe/Moscow

# Создание директорий для проекта
echo "📁 Создание директорий..."
mkdir -p /var/www/online_school
mkdir -p /var/backups/online_school
mkdir -p /var/log/online_school
mkdir -p /var/www/online_school/{staticfiles,media,logs,data}

# Установка прав доступа
chown -R root:root /var/www/online_school
chmod -R 755 /var/www/online_school

# Настройка автоматических обновлений
echo "🔄 Настройка автоматических обновлений..."
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Настройка логирования
echo "📝 Настройка логирования..."
mkdir -p /var/log/online_school
touch /var/log/online_school/{django.log,gunicorn.log,nginx.log,docker.log}
chmod 644 /var/log/online_school/*.log

echo "✅ Сервер настроен!"
echo ""
echo "Следующие шаги:"
echo "1. Клонировать репозиторий проекта"
echo "2. Настроить базу данных PostgreSQL"
echo "3. Настроить Nginx"
echo "4. Получить SSL сертификат"
echo "5. Запустить Docker контейнеры"