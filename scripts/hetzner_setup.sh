#!/bin/bash

# Скрипт для настройки сервера Hetzner для онлайн-школы

echo "=== Настройка сервера Hetzner ==="

# Обновление системы
echo "Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
echo "Установка необходимых пакетов..."
sudo apt install -y \
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
    docker-compose

# Добавление текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Настройка firewall (UFW)
echo "Настройка firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Настройка fail2ban
echo "Настройка fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Создание swap файла (если мало RAM)
echo "Создание swap файла..."
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Настройка времени (NTP)
echo "Настройка времени..."
sudo timedatectl set-timezone Europe/Moscow

# Создание директорий для проекта
echo "Создание директорий..."
sudo mkdir -p /var/www/online_school
sudo mkdir -p /var/backups/online_school
sudo mkdir -p /var/log/online_school

# Установка прав доступа
sudo chown -R $USER:$USER /var/www/online_school
sudo chown -R $USER:$USER /var/backups/online_school
sudo chown -R $USER:$USER /var/log/online_school

# Настройка автоматических обновлений
echo "Настройка автоматических обновлений..."
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

echo "=== Сервер Hetzner настроен! ==="
echo ""
echo "Следующие шаги:"
echo "1. Перезагрузите сервер: sudo reboot"
echo "2. Скопируйте файлы проекта в /var/www/online_school"
echo "3. Настройте .env файл с production значениями"
echo "4. Запустите Docker контейнеры"