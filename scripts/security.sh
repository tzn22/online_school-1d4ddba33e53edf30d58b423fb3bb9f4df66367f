#!/bin/bash

# Скрипт для настройки безопасности сервера

echo "=== Настройка безопасности сервера ==="

# Обновление системы
echo "🔄 Обновление системы..."
apt update && apt upgrade -y

# Установка необходимых пакетов безопасности
echo "🛡 Установка пакетов безопасности..."
apt install -y fail2ban ufw logwatch clamav rkhunter

# Настройка firewall
echo "🔥 Настройка UFW firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Настройка fail2ban
echo "🔒 Настройка fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600
findtime = 600

[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 3600
findtime = 600
EOF

systemctl restart fail2ban

# Настройка SSH
echo "🔐 Настройка SSH..."
sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

systemctl restart ssh

# Настройка автоматических обновлений безопасности
echo "🔄 Настройка автоматических обновлений..."
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Настройка сканирования на вирусы
echo "🦠 Настройка антивируса..."
freshclam  # Обновление баз данных ClamAV
clamdscan --fdpass /var/www/  # Сканирование директории проекта

# Настройка rootkit hunter
echo "🕵️‍♂️ Настройка rkhunter..."
rkhunter --update
rkhunter --propupd

# Настройка логирования
echo "📝 Настройка логирования..."
mkdir -p /var/log/online_school
chmod 755 /var/log/online_school

# Создание скрипта ежедневной проверки безопасности
cat > /usr/local/bin/daily_security_check.sh << 'EOF'
#!/bin/bash
# Ежедневная проверка безопасности

echo "=== Ежедневная проверка безопасности ==="
date

# Проверка fail2ban
echo "Fail2ban status:"
fail2ban-client status

# Проверка firewall
echo "UFW status:"
ufw status numbered

# Проверка SSH
echo "SSH connections:"
who

# Проверка диска
echo "Disk usage:"
df -h

# Проверка памяти
echo "Memory usage:"
free -h

# Проверка процессов
echo "Top processes:"
ps aux --sort=-%cpu | head -10

# Проверка логов ошибок
echo "Recent errors:"
grep -i "error\|fail\|warn" /var/log/syslog | tail -5

echo "=== Проверка завершена ==="
EOF

chmod +x /usr/local/bin/daily_security_check.sh

# Добавление в cron
echo "0 2 * * * /usr/local/bin/daily_security_check.sh >> /var/log/security_check.log 2>&1" | crontab -

echo "✅ Безопасность настроена!"
echo ""
echo "Настройки безопасности:"
echo "- Firewall (UFW): включен"
echo "- Fail2ban: настроен"
echo "- SSH: настроен (без пароля, root запрещен)"
echo "- Автоматические обновления: включены"
echo "- Антивирус: настроен"
echo "- Ежедневные проверки: запланированы"