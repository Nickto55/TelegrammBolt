#!/bin/bash
# Скрипт для обновления конфигурации Nginx с поддержкой WebSocket

set -e

NGINX_CONF="/etc/nginx/sites-available/telegrambot"
BACKUP_CONF="/etc/nginx/sites-available/telegrambot.backup.$(date +%Y%m%d_%H%M%S)"

echo "Обновление конфигурации Nginx для WebSocket..."

# Создаем резервную копию
if [ -f "$NGINX_CONF" ]; then
    cp "$NGINX_CONF" "$BACKUP_CONF"
    echo "✓ Резервная копия сохранена: $BACKUP_CONF"
fi

# Создаем новую конфигурацию
sudo tee $NGINX_CONF > /dev/null <<'EOF'
server {
    listen 80;
    server_name boltvolna.duckdns.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name boltvolna.duckdns.org;
    
    ssl_certificate /etc/ssl/telegrambot/fullchain.pem;
    ssl_certificate_key /etc/ssl/telegrambot/privkey.pem;
    
    # Отключаем проверку для самоподписанных
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    # Специальный location для Socket.IO
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000/socket.io/;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

echo "✓ Конфигурация обновлена"

# Проверяем конфигурацию Nginx
nginx -t

if [ $? -eq 0 ]; then
    echo "✓ Конфигурация Nginx корректна"
    
    # Перезагружаем Nginx
    systemctl reload nginx
    echo "✓ Nginx перезагружен"
    
    echo ""
    echo "Готово! WebSocket теперь должен работать через https://boltvolna.duckdns.org"
    echo "Проверьте веб-терминал: https://boltvolna.duckdns.org/terminal"
else
    echo "✗ Ошибка в конфигурации Nginx"
    echo "Восстанавливаем из резервной копии..."
    cp "$BACKUP_CONF" "$NGINX_CONF"
    exit 1
fi
