# TelegrammBolt Web Interface - Настройка

## Установка веб-интерфейса

### 1. Установка зависимостей

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/pip install flask flask-cors gunicorn
```

### 2. Настройка бота для веб-авторизации

Получите username вашего бота:

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/mybots`
3. Выберите вашего бота
4. Нажмите "Bot Settings" → "Set Username"
5. Запомните username (например: `MyAwesomeBot`)

### 3. Настройка домена

#### Вариант A: Использование собственного домена

1. Укажите A-запись на ваш сервер:
   ```
   bot.example.com → IP_ВАШЕГО_СЕРВЕРА
   ```

2. Дождитесь распространения DNS (обычно 5-30 минут)

#### Вариант B: Использование локального доступа

Для тестирования можно использовать `localhost:5000` или IP сервера.

⚠️ **Важно:** Telegram Login Widget работает только на HTTPS! Для локального тестирования можно использовать ngrok.

### 4. Установка и настройка Nginx

```bash
# Установка Nginx
sudo apt-get install -y nginx

# Копирование конфигурации
sudo cp nginx.conf /etc/nginx/sites-available/telegrambot
sudo ln -s /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/

# Редактирование конфигурации
sudo nano /etc/nginx/sites-available/telegrambot
```

Замените `your-domain.com` на ваш домен.

```bash
# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
```

### 5. Установка SSL сертификата (Let's Encrypt)

```bash
# Установка Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d bot.example.com

# Автоматическое обновление (уже настроено)
sudo certbot renew --dry-run
```

Certbot автоматически изменит конфигурацию Nginx для HTTPS.

### 6. Настройка Web App

Создайте файл конфигурации:

```bash
sudo nano /opt/telegrambot/web_config.py
```

```python
# Web App Configuration
import os

# Flask настройки
SECRET_KEY = os.urandom(32)  # Сгенерируйте фиксированный ключ для production
DEBUG = False
HOST = '0.0.0.0'
PORT = 5000

# Домен для веб-интерфейса
DOMAIN = 'bot.example.com'  # Замените на ваш домен
HTTPS_ENABLED = True

# Telegram Bot
BOT_USERNAME = 'YourBotUsername'  # Замените на username вашего бота (без @)

# Сессии
SESSION_COOKIE_SECURE = True  # Только для HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 604800  # 7 дней в секундах
```

### 7. Создание systemd службы для веб-приложения

```bash
sudo nano /etc/systemd/system/telegrambot-web.service
```

```ini
[Unit]
Description=TelegrammBolt Web Interface
After=network.target

[Service]
Type=simple
User=telegrambot
WorkingDirectory=/opt/telegrambot
Environment="PATH=/opt/telegrambot/.venv/bin"
ExecStart=/opt/telegrambot/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 web_app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Запуск веб-приложения
sudo systemctl start telegrambot-web
sudo systemctl enable telegrambot-web

# Проверка статуса
sudo systemctl status telegrambot-web
```

### 8. Настройка BotFather для веб-логина

1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/mybots`
3. Выберите вашего бота
4. Нажмите "Bot Settings" → "Domain"
5. Введите ваш домен: `bot.example.com`

Это необходимо для работы Telegram Login Widget.

## Запуск в режиме разработки

Для локальной разработки:

```bash
cd /opt/telegrambot
source .venv/bin/activate
python web_app.py
```

Приложение будет доступно на `http://localhost:5000`

⚠️ **Для тестирования Telegram Login локально используйте ngrok:**

```bash
# Установка ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Регистрация на https://ngrok.com и получение токена
ngrok config add-authtoken YOUR_TOKEN

# Запуск туннеля
ngrok http 5000
```

Ngrok предоставит вам HTTPS URL (например: `https://abc123.ngrok.io`), который можно использовать для тестирования.

## Проверка работы

1. Откройте браузер и перейдите на ваш домен: `https://bot.example.com`
2. Нажмите кнопку "Login with Telegram"
3. Авторизуйтесь через Telegram
4. Вы должны быть перенаправлены на панель управления

## Логи

```bash
# Логи веб-приложения
sudo journalctl -u telegrambot-web -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Логи бота
sudo journalctl -u telegrambot -f
```

## Устранение проблем

### Ошибка "Login widget domain mismatch"

**Причина:** Домен в BotFather не совпадает с доменом сайта.

**Решение:**
1. Проверьте настройку домена в BotFather
2. Убедитесь, что используется HTTPS
3. Перезапустите веб-приложение

### Ошибка "User not registered"

**Причина:** Пользователь не запустил бота в Telegram.

**Решение:**
1. Откройте бота в Telegram: `https://t.me/YourBotUsername`
2. Отправьте `/start`
3. Попробуйте войти снова

### Ошибка 502 Bad Gateway

**Причина:** Веб-приложение не запущено или недоступно.

**Решение:**
```bash
# Проверить статус
sudo systemctl status telegrambot-web

# Перезапустить
sudo systemctl restart telegrambot-web

# Проверить логи
sudo journalctl -u telegrambot-web -n 50
```

### Ошибка SSL сертификата

**Причина:** Сертификат не установлен или истек.

**Решение:**
```bash
# Обновить сертификат
sudo certbot renew

# Проверить срок действия
sudo certbot certificates

# Перезапустить Nginx
sudo systemctl restart nginx
```

## Безопасность

### Рекомендации:

1. **Всегда используйте HTTPS** для production
2. **Сгенерируйте фиксированный SECRET_KEY** в `web_config.py`
3. **Настройте firewall:**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
4. **Регулярно обновляйте пакеты:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade
   sudo -u telegrambot .venv/bin/pip install --upgrade -r requirements.txt
   ```
5. **Ограничьте доступ к административным функциям** в коде
6. **Используйте rate limiting** для API endpoints

### Настройка rate limiting в Nginx:

```nginx
# Добавить в /etc/nginx/sites-available/telegrambot

limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    # ... остальные настройки
}
```

## Обновление

```bash
cd /opt/telegrambot

# Остановить службы
sudo systemctl stop telegrambot-web telegrambot

# Обновить код
sudo -u telegrambot git pull

# Обновить зависимости
sudo -u telegrambot .venv/bin/pip install --upgrade -r requirements.txt

# Запустить службы
sudo systemctl start telegrambot telegrambot-web

# Проверить статус
sudo systemctl status telegrambot telegrambot-web
```

## Производительность

Для высокой нагрузки увеличьте количество workers в gunicorn:

```bash
sudo nano /etc/systemd/system/telegrambot-web.service
```

Измените строку `ExecStart`:
```ini
ExecStart=/opt/telegrambot/.venv/bin/gunicorn -w 8 -b 127.0.0.1:5000 --timeout 120 web_app:app
```

Формула для количества workers: `(2 * CPU_CORES) + 1`

## Мониторинг

Установите мониторинг с помощью `htop` и `netstat`:

```bash
sudo apt-get install -y htop net-tools

# Просмотр процессов
htop

# Проверка портов
sudo netstat -tulpn | grep LISTEN
```

## Дополнительные ресурсы

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Telegram Login Widget](https://core.telegram.org/widgets/login)
