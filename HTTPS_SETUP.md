# 🔒 Настройка HTTPS для веб-интерфейса

## 🎯 Цель
Настроить безопасное HTTPS соединение для доступа к веб-интерфейсу по адресу `https://87.120.166.213`

---

## ✅ Вариант 1: SSL с самоподписанным сертификатом (быстро)

Для тестирования или если нет домена.

### Шаг 1: Создать самоподписанный сертификат

```bash
# На сервере (не в контейнере)
sudo mkdir -p /etc/nginx/ssl

# Создать сертификат
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/telegrambot.key \
  -out /etc/nginx/ssl/telegrambot.crt \
  -subj "/C=RU/ST=Moscow/L=Moscow/O=TelegrammBolt/CN=87.120.166.213"
```

### Шаг 2: Настроить Nginx

Создайте файл `/etc/nginx/sites-available/telegrambot`:

```nginx
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
    
    # SSL сертификаты
    ssl_certificate /etc/nginx/ssl/telegrambot.crt;
    ssl_certificate_key /etc/nginx/ssl/telegrambot.key;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # Логи
    access_log /var/log/nginx/telegrambot_access.log;
    error_log /var/log/nginx/telegrambot_error.log;
    
    # Максимальный размер загружаемого файла
    client_max_body_size 16M;
    
    # Статические файлы
    location /static/ {
        alias /opt/telegrambot/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /photos/ {
        alias /opt/telegrambot/photos/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # Прокси к Flask/Gunicorn
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
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Шаг 3: Активировать конфигурацию

```bash
# Создать симлинк
sudo ln -sf /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/

# Удалить дефолтную конфигурацию (если есть)
sudo rm -f /etc/nginx/sites-enabled/default

# Проверить конфигурацию
sudo nginx -t

# Перезапустить Nginx
sudo systemctl restart nginx

# Проверить статус
sudo systemctl status nginx
```

### Шаг 4: Открыть порты в firewall

```bash
# Разрешить HTTPS
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp

# Проверить
sudo ufw status
```

**⚠️ Предупреждение:** Браузер покажет предупреждение о небезопасном сертификате (это нормально для самоподписанного сертификата). Нужно нажать "Дополнительно" → "Продолжить".

---

## ✅ Вариант 2: SSL с Let's Encrypt (рекомендуется для домена)

Если у вас есть домен (например, `bot.yourdomain.com`).

### Шаг 1: Установить Certbot

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

### Шаг 2: Получить сертификат

```bash
# Для домена
sudo certbot --nginx -d bot.yourdomain.com

# Следуйте инструкциям:
# 1. Введите email
# 2. Согласитесь с условиями
# 3. Выберите перенаправление HTTP на HTTPS (рекомендуется)
```

### Шаг 3: Автоматическое обновление

```bash
# Проверить автообновление
sudo certbot renew --dry-run

# Сертификаты будут автоматически обновляться
```

---

## ✅ Вариант 3: Cloudflare (самый простой)

Если у вас есть домен, используйте Cloudflare для бесплатного SSL.

### Шаг 1: Добавить домен в Cloudflare

1. Зарегистрируйтесь на [cloudflare.com](https://cloudflare.com)
2. Добавьте ваш домен
3. Измените nameservers у регистратора домена

### Шаг 2: Настроить DNS

В Cloudflare DNS:
```
A    bot    87.120.166.213    (proxy включен - оранжевое облако)
```

### Шаг 3: Настроить SSL в Cloudflare

1. SSL/TLS → Overview → Выберите "Full" или "Flexible"
2. Edge Certificates → Always Use HTTPS: ON

Готово! Cloudflare автоматически выдаст SSL сертификат.

---

## 🐳 Вариант 4: Docker с SSL

Если используете Docker Compose:

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: telegrambot_web
    restart: unless-stopped
    expose:
      - "5000"
    volumes:
      - ./:/app
      - ./bot_data.json:/app/bot_data.json
      - ./users_data.json:/app/users_data.json
    environment:
      - FLASK_ENV=production
    command: gunicorn -w 4 -b 0.0.0.0:5000 web_app:app

  nginx:
    image: nginx:alpine
    container_name: telegrambot_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
      - ./static:/opt/telegrambot/static
      - ./photos:/opt/telegrambot/photos
    depends_on:
      - web
```

### nginx.conf для Docker

```nginx
server {
    listen 80;
    server_name 87.120.166.213;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 87.120.166.213;
    
    ssl_certificate /etc/nginx/ssl/telegrambot.crt;
    ssl_certificate_key /etc/nginx/ssl/telegrambot.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    client_max_body_size 16M;
    
    location /static/ {
        alias /opt/telegrambot/static/;
    }
    
    location / {
        proxy_pass http://web:5000;  # web - имя сервиса
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔍 Проверка HTTPS

После настройки:

```bash
# Проверить что порт 443 открыт
sudo netstat -tulpn | grep :443

# Проверить SSL
curl -k https://87.120.166.213

# Или откройте в браузере
https://87.120.166.213
```

---

## ⚙️ Настройка Telegram Login для HTTPS

После настройки HTTPS обновите домен в @BotFather:

```
@BotFather → /setdomain
→ Выберите бота
→ Введите: 87.120.166.213 (без https://)
```

И в `ven_bot.json` можете добавить:

```json
{
  "BOT_TOKEN": "ваш_токен",
  "ADMIN_IDS": ["ваш_id"],
  "BOT_USERNAME": "ваш_бот",
  "WEB_URL": "https://87.120.166.213"
}
```

---

## 🆘 Решение проблем

### Ошибка: ERR_SSL_PROTOCOL_ERROR

```bash
# Проверить что Nginx слушает 443 порт
sudo netstat -tulpn | grep nginx

# Проверить логи
sudo tail -f /var/log/nginx/error.log
```

### Ошибка: NET::ERR_CERT_AUTHORITY_INVALID

Это нормально для самоподписанного сертификата. Нажмите "Дополнительно" → "Продолжить".

### Firewall блокирует порт 443

```bash
sudo ufw allow 443/tcp
sudo ufw reload
```

---

## 📋 Быстрая настройка (самоподписанный сертификат)

```bash
# 1. Создать сертификат
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/telegrambot.key \
  -out /etc/nginx/ssl/telegrambot.crt \
  -subj "/C=RU/ST=Moscow/L=Moscow/O=TelegrammBolt/CN=87.120.166.213"

# 2. Скопировать конфиг Nginx (см. выше в Вариант 1)
sudo nano /etc/nginx/sites-available/telegrambot

# 3. Активировать
sudo ln -sf /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 4. Открыть порты
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp

# 5. Готово!
# Откройте: https://87.120.166.213
```

---

**После настройки HTTPS ваш сайт будет доступен по адресу `https://87.120.166.213` 🔒**
