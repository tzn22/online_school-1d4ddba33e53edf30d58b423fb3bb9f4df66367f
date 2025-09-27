#!/bin/bash

# Скрипт для мониторинга системы

echo "=== Мониторинг системы ==="
echo "Дата: $(date)"
echo "Сервер: 116.203.145.245"
echo ""

# Проверка состояния контейнеров
echo "🐳 Состояние Docker контейнеров:"
docker ps

echo ""
echo "💾 Использование диска:"
df -h

echo ""
echo "🧠 Использование памяти:"
free -h

echo ""
echo "⚡ Использование CPU:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F',' '{print "CPU Usage: " $1 "%"}'

echo ""
echo "🌐 Состояние сетевых соединений:"
netstat -tuln | grep :80\|:443\|:5432\|:6379

echo ""
echo "📊 Логи ошибок:"
tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "Нет логов Nginx"

echo ""
echo "📝 Логи приложения:"
tail -n 10 /var/log/online_school/django.log 2>/dev/null || echo "Нет логов Django"

echo ""
echo "🔒 Состояние firewall:"
ufw status

echo ""
echo "🛡 Состояние fail2ban:"
fail2ban-client status

echo ""
echo "📊 Состояние базы данных:"
sudo -u postgres psql -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE datname = 'online_school_prod';" 2>/dev/null || echo "Нет доступа к PostgreSQL"

echo ""
echo "📈 Состояние Redis:"
redis-cli ping 2>/dev/null || echo "Redis недоступен"

echo ""
echo "=== Мониторинг завершен ==="