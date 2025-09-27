#!/bin/bash

# Скрипт для настройки SSL сертификата Let's Encrypt

echo "=== Настройка SSL сертификата ==="

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo "Использование: $0 <domain>"
    echo "Пример: $0 your-domain.com"
    exit 1
fi

# Установка Certbot если не установлен
if ! command -v certbot &> /dev/null
then
    echo "📦 Установка Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Получение SSL сертификата
echo "🔐 Получение SSL сертификата для $DOMAIN..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

if [ $? -eq 0 ]; then
    echo "✅ SSL сертификат успешно получен!"
    
    # Настройка автоматического обновления
    echo "🔄 Настройка автоматического обновления..."
    crontab -l | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | crontab -
    
    # Перезапуск Nginx
    systemctl reload nginx
    
    echo "✅ SSL сертификат настроен!"
    echo ""
    echo "Доступ к приложению по HTTPS:"
    echo "- Основное приложение: https://$DOMAIN"
    echo "- Админка: https://$DOMAIN/admin/"
else
    echo "❌ Ошибка получения SSL сертификата!"
    exit 1
fi