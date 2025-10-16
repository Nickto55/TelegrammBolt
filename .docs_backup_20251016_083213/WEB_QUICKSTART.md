# 🌐 Быстрый старт веб-интерфейса TelegrammBolt

## За 10 минут до запуска!

> 💡 **Примечание:** Веб-интерфейс автоматически определяет Docker окружение и показывает правильную ссылку!

### Получение ссылки на веб-интерфейс

После запуска получить ссылку можно 4 способами:

1. **Веб-страница:** `http://ваш-IP:5000/show-url`
2. **Скрипт:** `bash show-web-url.sh`
3. **API:** `curl http://localhost:5000/api/server-info`
4. **При запуске** - автоматически выводится в консоль

Подробнее: [GET_WEB_URL.md](GET_WEB_URL.md)

---

### Шаг 1: Установка зависимостей (2 мин)

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/pip install flask flask-cors gunicorn
```

### Шаг 2: Получение username бота (1 мин)

1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/mybots` → выберите бота → "Bot Settings" → проверьте username

### Шаг 3: Настройка домена в BotFather (1 мин)

1. В BotFather: "Bot Settings" → "Domain"
2. Введите ваш домен (например: `bot.example.com`)

### Шаг 4: Установка Nginx + SSL (3 мин)

```bash
# Установка
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Копирование конфигурации
sudo cp /opt/telegrambot/nginx.conf /etc/nginx/sites-available/telegrambot

# Редактирование (замените your-domain.com на ваш домен)
sudo nano /etc/nginx/sites-available/telegrambot

# Активация
sudo ln -s /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Получение SSL сертификата
sudo certbot --nginx -d bot.example.com
```

### Шаг 5: Создание службы веб-приложения (2 мин)

```bash
sudo nano /etc/systemd/system/telegrambot-web.service
```

Вставьте:
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
# Запуск
sudo systemctl daemon-reload
sudo systemctl start telegrambot-web
sudo systemctl enable telegrambot-web

# Проверка
sudo systemctl status telegrambot-web
```

### Шаг 6: Исправление web_app.py (1 мин)

Откройте `web_app.py` и найдите функцию `get_bot_username()` (строка ~413):

```python
def get_bot_username():
    """Получить username бота для Telegram Login Widget"""
    return "YourBotUsername"  # Замените на реальный username вашего бота (без @)
```

Замените `"YourBotUsername"` на ваш реальный username бота.

### Готово! 🎉

Откройте в браузере: `https://bot.example.com`

## Быстрая проверка

```bash
# Проверить статусы служб
sudo systemctl status telegrambot telegrambot-web nginx

# Проверить логи
sudo journalctl -u telegrambot-web -f

# Проверить порты
sudo netstat -tulpn | grep :5000
sudo netstat -tulpn | grep :443
```

## Тестирование локально (без домена)

Используйте **ngrok** для временного HTTPS туннеля:

```bash
# Установка ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Получите токен на https://ngrok.com
ngrok config add-authtoken YOUR_TOKEN

# Запуск Flask в одном терминале
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python web_app.py

# Запуск ngrok в другом терминале
ngrok http 5000
```

Ngrok выдаст URL вида `https://abc123.ngrok.io` - используйте его для тестирования!

## Частые проблемы

### "Login widget domain mismatch"
→ Проверьте домен в BotFather → Bot Settings → Domain

### "User not registered"
→ Откройте бота в Telegram и отправьте `/start`

### 502 Bad Gateway
→ Проверьте: `sudo systemctl status telegrambot-web`

### Бот не получает username
→ Отредактируйте `web_app.py`, строка ~413, замените `"YourBotUsername"`

## Полная документация

Подробная инструкция: [WEB_SETUP.md](WEB_SETUP.md)

## Архитектура

```
[Пользователь] 
    ↓ HTTPS
[Nginx :443] 
    ↓ HTTP
[Gunicorn :5000]
    ↓
[Flask App]
    ↓
[Bot Modules: user_manager, dse_manager, chat_manager]
    ↓
[Data: JSON files, Excel]
```

## Что дальше?

- ✅ Авторизация через Telegram - работает
- ✅ Просмотр ДСЕ - работает
- ✅ Экспорт Excel - работает
- ✅ API endpoints - работает
- 🔧 Добавить остальные шаблоны (dse_list.html, chat.html, reports.html)
- 🔧 Реализовать полный CRUD для ДСЕ
- 🔧 Добавить real-time чат через WebSocket

## Безопасность

⚠️ **Важно для production:**

1. Сгенерируйте фиксированный `SECRET_KEY` в `web_app.py`
2. Установите `DEBUG = False`
3. Настройте firewall: `sudo ufw allow 80,443/tcp`
4. Регулярно обновляйте сертификаты (автоматически с certbot)
5. Используйте strong passwords для всех сервисов

Готово! Ваш веб-интерфейс запущен! 🚀
