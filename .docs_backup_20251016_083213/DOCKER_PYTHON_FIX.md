# 🔧 Быстрое решение для Docker с Python 3.13

Если вы получаете ошибку:
```
AttributeError: 'Updater' object has no attribute '_Updater__polling_cleanup_cb'
```

## Решение 1: Обновить библиотеку (БЫСТРО)

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/pip install --upgrade python-telegram-bot
sudo -u telegrambot .venv/bin/python bot.py
```

Если работает, запустите службу:
```bash
# Для systemd:
sudo systemctl restart telegrambot

# Для init.d:
sudo service telegrambot restart
```

## Решение 2: Использовать правильный Docker образ

Если используете Docker, измените образ на Python 3.12:

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /opt/telegrambot
COPY . /opt/telegrambot

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

CMD ["python", "bot.py"]
```

**Пересоздать контейнер:**
```bash
docker build -t telegrambot .
docker stop telegrambot_container 2>/dev/null || true
docker rm telegrambot_container 2>/dev/null || true
docker run -d --name telegrambot_container \
    -v $(pwd)/ven_bot.json:/opt/telegrambot/ven_bot.json \
    -v $(pwd)/smtp_config.json:/opt/telegrambot/smtp_config.json \
    -v $(pwd)/bot_data.json:/opt/telegrambot/bot_data.json \
    -v $(pwd)/users_data.json:/opt/telegrambot/users_data.json \
    telegrambot
```

## Решение 3: Использовать docker-compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  telegrambot:
    build:
      context: .
      dockerfile: Dockerfile
    image: telegrambot:latest
    container_name: telegrambot
    restart: unless-stopped
    volumes:
      - ./ven_bot.json:/opt/telegrambot/ven_bot.json:ro
      - ./smtp_config.json:/opt/telegrambot/smtp_config.json:ro
      - ./bot_data.json:/opt/telegrambot/bot_data.json
      - ./users_data.json:/opt/telegrambot/users_data.json
      - ./RezultBot.xlsx:/opt/telegrambot/RezultBot.xlsx
      - ./photos:/opt/telegrambot/photos
    environment:
      - PYTHONUNBUFFERED=1
      - TZ=Europe/Moscow
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Запуск:**
```bash
docker-compose up -d
docker-compose logs -f
```

## Проверка

После применения любого решения:

```bash
# Проверить версию Python
python3 --version

# Проверить версию библиотеки
.venv/bin/pip show python-telegram-bot

# Запустить бота вручную для проверки
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

Если видите логи запуска без ошибок - всё работает! Ctrl+C для остановки, затем запустите службу.

## Дополнительно

Полная документация: [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md)
