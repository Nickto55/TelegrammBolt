#!/bin/bash
# Автоматическая настройка HTTPS для TelegrammBolt
# Для IP: 87.120.166.213

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🔒 НАСТРОЙКА HTTPS ДЛЯ TELEGRAMBOT                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# ============================================================================
# 1. СОЗДАНИЕ САМОПОДПИСАННОГО SSL СЕРТИФИКАТА
# ============================================================================
echo "📝 Шаг 1: Создание SSL сертификата..."

mkdir -p /etc/nginx/ssl

if [ -f "/etc/nginx/ssl/telegrambot.crt" ]; then
    echo "   ⚠️  Сертификат уже существует"
    read -p "   Пересоздать? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Пропускаем создание сертификата"
    else
        rm -f /etc/nginx/ssl/telegrambot.{crt,key}
    fi
fi

if [ ! -f "/etc/nginx/ssl/telegrambot.crt" ]; then
    echo "   Создание самоподписанного сертификата..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout /etc/nginx/ssl/telegrambot.key \
      -out /etc/nginx/ssl/telegrambot.crt \
      -subj "/C=RU/ST=Moscow/L=Moscow/O=TelegrammBolt/CN=87.120.166.213"
    
    chmod 600 /etc/nginx/ssl/telegrambot.key
    chmod 644 /etc/nginx/ssl/telegrambot.crt
    
    echo "   ✅ Сертификат создан"
fi

# ============================================================================
# 2. УСТАНОВКА И НАСТРОЙКА NGINX
# ============================================================================
echo ""
echo "📦 Шаг 2: Проверка Nginx..."

if ! command -v nginx &> /dev/null; then
    echo "   Nginx не установлен. Установка..."
    apt-get update -qq
    apt-get install -y nginx
    echo "   ✅ Nginx установлен"
else
    echo "   ✅ Nginx уже установлен"
fi

# ============================================================================
# 3. СОЗДАНИЕ КОНФИГУРАЦИИ NGINX
# ============================================================================
echo ""
echo "⚙️  Шаг 3: Настройка Nginx..."

cat > /etc/nginx/sites-available/telegrambot << 'EOF'
# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name 87.120.166.213;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name 87.120.166.213;
    
    ssl_certificate /etc/nginx/ssl/telegrambot.crt;
    ssl_certificate_key /etc/nginx/ssl/telegrambot.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    access_log /var/log/nginx/telegrambot_access.log;
    error_log /var/log/nginx/telegrambot_error.log;
    
    client_max_body_size 16M;
    
    location /static/ {
        alias /opt/telegrambot/static/;
        expires 30d;
    }
    
    location /photos/ {
        alias /opt/telegrambot/photos/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

echo "   ✅ Конфигурация создана"

# ============================================================================
# 4. АКТИВАЦИЯ КОНФИГУРАЦИИ
# ============================================================================
echo ""
echo "🔗 Шаг 4: Активация конфигурации..."

# Удалить дефолтную конфигурацию
rm -f /etc/nginx/sites-enabled/default

# Создать симлинк
ln -sf /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/

# Проверить конфигурацию
echo "   Проверка конфигурации Nginx..."
if nginx -t 2>&1 | grep -q "successful"; then
    echo "   ✅ Конфигурация корректна"
else
    echo "   ❌ Ошибка в конфигурации!"
    nginx -t
    exit 1
fi

# ============================================================================
# 5. НАСТРОЙКА FIREWALL
# ============================================================================
echo ""
echo "🔥 Шаг 5: Настройка firewall..."

if command -v ufw &> /dev/null; then
    echo "   Открытие портов 80 и 443..."
    ufw allow 80/tcp
    ufw allow 443/tcp
    echo "   ✅ Порты открыты"
else
    echo "   ⚠️  UFW не установлен, пропускаем"
fi

# ============================================================================
# 6. ПЕРЕЗАПУСК NGINX
# ============================================================================
echo ""
echo "🔄 Шаг 6: Перезапуск Nginx..."

systemctl enable nginx
systemctl restart nginx

if systemctl is-active --quiet nginx; then
    echo "   ✅ Nginx запущен"
else
    echo "   ❌ Nginx не запустился!"
    systemctl status nginx
    exit 1
fi

# ============================================================================
# 7. ПРОВЕРКА
# ============================================================================
echo ""
echo "🧪 Шаг 7: Проверка настройки..."

echo "   Проверка портов..."
if netstat -tulpn | grep -q ":443"; then
    echo "   ✅ Порт 443 (HTTPS) слушается"
else
    echo "   ❌ Порт 443 не слушается!"
fi

if netstat -tulpn | grep -q ":80"; then
    echo "   ✅ Порт 80 (HTTP) слушается"
else
    echo "   ❌ Порт 80 не слушается!"
fi

# ============================================================================
# ФИНАЛ
# ============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ HTTPS НАСТРОЕН УСПЕШНО!                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Ваш сайт доступен по адресу:"
echo "   https://87.120.166.213"
echo ""
echo "⚠️  ВАЖНО: Браузер покажет предупреждение о небезопасном"
echo "   сертификате (это нормально для самоподписанного сертификата)."
echo "   Нажмите: Дополнительно → Продолжить"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Убедитесь что веб-приложение запущено:"
echo "      cd /opt/telegrambot"
echo "      source .venv/bin/activate"
echo "      gunicorn -w 4 -b 0.0.0.0:5000 web_app:app"
echo ""
echo "   2. Обновите домен в @BotFather:"
echo "      /setdomain → 87.120.166.213"
echo ""
echo "   3. Готово! Откройте: https://87.120.166.213"
echo ""
echo "📝 Логи Nginx:"
echo "   sudo tail -f /var/log/nginx/telegrambot_error.log"
echo ""
echo "═══════════════════════════════════════════════════════════════"
