# 🔗 Получение ссылки на веб-интерфейс

## Быстрые способы

### 1. Веб-страница с информацией
Откройте в браузере:
```
http://ваш-сервер:5000/show-url
```

Эта страница покажет:
- ✅ Готовую ссылку для копирования
- 📍 Публичный и локальный IP
- 🔧 Инструкции по настройке Telegram Login
- 📋 Кнопку для копирования URL

### 2. Через скрипт (Linux/Docker)
```bash
bash show-web-url.sh
```

Или с правами выполнения:
```bash
chmod +x show-web-url.sh
./show-web-url.sh
```

### 3. API endpoint
```bash
curl http://localhost:5000/api/server-info
```

Вернет JSON:
```json
{
  "url": "http://123.45.67.89:5000",
  "type": "Public",
  "public_ip": "123.45.67.89",
  "local_ip": "192.168.1.100",
  "port": 5000,
  "is_docker": true
}
```

### 4. При запуске сервера
При запуске `web_app.py` автоматически выводится:
```
============================================================
🚀 TelegrammBolt Web Interface Starting...
============================================================

🌐 Access URL: http://123.45.67.89:5000
📍 Environment: Docker
🔗 Server Info Page: http://123.45.67.89:5000/show-url
🌍 Public IP: 123.45.67.89
🏠 Local IP: 192.168.1.100
🚪 Port: 5000

============================================================
✅ Server is ready!
============================================================
```

## Примеры использования

### Docker
```bash
# Запустить контейнер
docker run -d -p 5000:5000 --name telegrambot telegrambot

# Показать URL
docker exec telegrambot bash show-web-url.sh

# Или просто откройте
curl http://localhost:5000/show-url
```

### Docker Compose
```bash
# Запустить
docker-compose up -d

# Показать URL
docker-compose exec telegrambot bash show-web-url.sh

# Или просто откройте браузер
# http://ваш-IP:5000/show-url
```

### Нативная установка
```bash
# Запустить сервис
systemctl start telegrambot-web

# Показать URL
bash /opt/telegrambot/show-web-url.sh

# Или откройте
curl http://localhost:5000/show-url
```

## Автоматическое определение IP

Веб-приложение автоматически определяет:
1. **Docker окружение** - проверяет `/.dockerenv` и `/proc/1/cgroup`
2. **Публичный IP** - через `ifconfig.me` или `icanhazip.com`
3. **Локальный IP** - через socket connection
4. **Порт** - из переменной окружения `WEB_PORT` или 5000 по умолчанию

## Настройка переменных окружения

### Docker
```yaml
# docker-compose.yml
environment:
  - WEB_PORT=5000
  - PUBLIC_IP=123.45.67.89  # Опционально
```

### Systemd
```ini
# /etc/systemd/system/telegrambot-web.service
[Service]
Environment="WEB_PORT=5000"
```

## Добавление в команды бота

Можете добавить команду `/weburl` в бота:

```python
# В commands.py
async def weburl_command(update, context):
    """Команда /weburl - показать ссылку на веб-интерфейс"""
    import urllib.request
    import json
    
    try:
        response = urllib.request.urlopen('http://localhost:5000/api/server-info')
        data = json.loads(response.read())
        
        message = f"""
🌐 <b>Веб-интерфейс TelegrammBolt</b>

🔗 Ссылка: <code>{data['url']}</code>

📍 Тип: {data['type']}
🌍 IP: {data['public_ip'] or data['local_ip']}
🚪 Порт: {data['port']}

💡 Нажмите на ссылку или скопируйте для открытия в браузере
"""
        await update.message.reply_text(message, parse_mode='HTML')
    except:
        await update.message.reply_text("❌ Веб-интерфейс недоступен")

# Добавить в bot.py:
app.add_handler(CommandHandler("weburl", weburl_command))
```

## QR код для мобильных устройств

Если установлен `qrencode`:
```bash
# Установка
apt-get install qrencode

# Использование в скрипте
bash show-web-url.sh  # Автоматически покажет QR код
```

## Troubleshooting

### URL не определяется
```bash
# Проверить доступность
curl http://localhost:5000/api/server-info

# Если не работает, проверить порт
netstat -tulpn | grep 5000

# Перезапустить веб-интерфейс
systemctl restart telegrambot-web
# или
docker-compose restart telegrambot
```

### Неправильный IP
Можно задать вручную через переменную окружения:
```bash
export PUBLIC_IP="123.45.67.89"
python web_app.py
```

### Docker не определяется
Проверить:
```bash
docker exec telegrambot ls -la /.dockerenv
docker exec telegrambot cat /proc/1/cgroup | grep docker
```

## Интеграция с CI/CD

```yaml
# .github/workflows/deploy.yml
- name: Get Web URL
  run: |
    docker-compose up -d
    sleep 5
    curl http://localhost:5000/api/server-info
    
- name: Send URL to Telegram
  run: |
    URL=$(curl -s http://localhost:5000/api/server-info | jq -r '.url')
    curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
      -d "chat_id=$ADMIN_ID" \
      -d "text=✅ Deployed! Web: $URL"
```

## Примеры вывода

### Консоль (show-web-url.sh)
```
╔════════════════════════════════════════════════╗
║     TelegrammBolt Web Interface URL            ║
╚════════════════════════════════════════════════╝

Environment: Docker

Status: ✅ Online

🌐 Access URLs:

  ➜ Container: http://localhost:5000
  ➜ Public:    http://123.45.67.89:5000
  ➜ Local:     http://192.168.1.100:5000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Copy this URL:

   http://123.45.67.89:5000
```

### Веб-страница (/show-url)
Красивая страница с:
- Большой кнопкой "Копировать ссылку"
- Информацией о сервере
- Инструкциями по настройке
- Кнопкой перехода к входу

### API (/api/server-info)
```json
{
  "url": "http://123.45.67.89:5000",
  "type": "Public",
  "public_ip": "123.45.67.89",
  "local_ip": "192.168.1.100",
  "port": 5000,
  "is_docker": true
}
```

Готово! Теперь у вас есть 4 способа получить ссылку на веб-интерфейс! 🚀
