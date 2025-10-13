# 🚀 Установка TelegrammBolt из ветки web

## Быстрая установка

### Автоматическая установка из ветки web

```bash
# Скачать и запустить установочный скрипт
wget https://raw.githubusercontent.com/Nickto55/TelegrammBolt/web/setup.sh
chmod +x setup.sh
./setup.sh
```

Или одной командой:
```bash
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/web/setup.sh | bash
```

## Ручная установка

### Шаг 1: Клонирование репозитория

**Вариант A: Клонировать только ветку web**
```bash
git clone -b web --single-branch https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot
```

**Вариант B: Клонировать весь репозиторий и переключиться на ветку web**
```bash
# Клонировать
git clone https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot

# Перейти в директорию
cd /opt/telegrambot

# Переключиться на ветку web
git checkout web
```

### Шаг 2: Создание пользователя

```bash
# Создать пользователя для бота
sudo useradd --system --shell /bin/bash --home /opt/telegrambot --create-home telegrambot

# Установить владельца
sudo chown -R telegrambot:telegrambot /opt/telegrambot
```

### Шаг 3: Установка зависимостей

```bash
# Обновить систему
sudo apt-get update

# Установить Python и необходимые пакеты
sudo apt-get install -y python3 python3-pip python3-venv git

# Перейти в директорию
cd /opt/telegrambot

# Создать виртуальное окружение
sudo -u telegrambot python3 -m venv .venv

# Установить зависимости
sudo -u telegrambot .venv/bin/pip install --upgrade pip
sudo -u telegrambot .venv/bin/pip install -r requirements.txt
```

### Шаг 4: Настройка конфигурации

```bash
# Создать конфигурацию бота
sudo nano /opt/telegrambot/ven_bot.json
```

Вставить:
```json
{
  "BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
  "ADMIN_IDS": ["YOUR_TELEGRAM_ID_HERE"]
}
```

Настроить email (опционально):
```bash
sudo nano /opt/telegrambot/smtp_config.json
```

### Шаг 5: Запуск

**Тестовый запуск:**
```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

**Запуск веб-интерфейса:**
```bash
sudo -u telegrambot .venv/bin/python web_app.py
```

### Шаг 6: Создание systemd служб

**Служба бота:**
```bash
sudo nano /etc/systemd/system/telegrambot.service
```

Содержимое:
```ini
[Unit]
Description=TelegrammBolt Telegram Bot
After=network.target

[Service]
Type=simple
User=telegrambot
WorkingDirectory=/opt/telegrambot
Environment="PATH=/opt/telegrambot/.venv/bin"
ExecStart=/opt/telegrambot/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Служба веб-интерфейса:**
```bash
sudo nano /etc/systemd/system/telegrambot-web.service
```

Содержимое:
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

**Запуск служб:**
```bash
# Перезагрузить systemd
sudo systemctl daemon-reload

# Запустить службы
sudo systemctl start telegrambot
sudo systemctl start telegrambot-web

# Добавить в автозагрузку
sudo systemctl enable telegrambot
sudo systemctl enable telegrambot-web

# Проверить статус
sudo systemctl status telegrambot
sudo systemctl status telegrambot-web
```

## Обновление из ветки web

```bash
cd /opt/telegrambot

# Остановить службы
sudo systemctl stop telegrambot telegrambot-web

# Обновить код из ветки web
sudo -u telegrambot git pull origin web

# Обновить зависимости (если изменились)
sudo -u telegrambot .venv/bin/pip install --upgrade -r requirements.txt

# Запустить службы
sudo systemctl start telegrambot telegrambot-web

# Проверить статус
sudo systemctl status telegrambot telegrambot-web
```

## Модифицированный setup.sh для ветки web

Если вы хотите, чтобы `setup.sh` всегда использовал ветку `web`, измените его:

```bash
# Найти строку с git clone в setup.sh
sudo nano /opt/telegrambot/setup.sh

# Найти:
git clone https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot

# Заменить на:
git clone -b web --single-branch https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot
```

Или создать отдельный скрипт `setup-web.sh`:

```bash
#!/bin/bash
# Установка из ветки web

# Все как в setup.sh, но с измененной строкой клонирования:
git clone -b web --single-branch https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot
```

## Docker установка из ветки web

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  telegrambot:
    build:
      context: https://github.com/Nickto55/TelegrammBolt.git#web
      dockerfile: Dockerfile
    container_name: telegrambot
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./ven_bot.json:/app/ven_bot.json:ro
      - ./smtp_config.json:/app/smtp_config.json:ro
      - ./bot_data.json:/app/bot_data.json
      - ./users_data.json:/app/users_data.json
      - ./RezultBot.xlsx:/app/RezultBot.xlsx
      - ./photos:/app/photos
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - TZ=Europe/Moscow
```

Или клонировать локально:
```bash
# Клонировать ветку web
git clone -b web https://github.com/Nickto55/TelegrammBolt.git

# Перейти в директорию
cd TelegrammBolt

# Запустить
docker-compose up -d
```

## Проверка текущей ветки

```bash
cd /opt/telegrambot

# Показать текущую ветку
git branch

# Показать удаленную ветку
git branch -r

# Показать информацию о репозитории
git remote -v
git status
```

Должно быть:
```
* web
```

## Переключение между ветками

**С main на web:**
```bash
cd /opt/telegrambot
sudo systemctl stop telegrambot telegrambot-web
sudo -u telegrambot git checkout web
sudo -u telegrambot git pull origin web
sudo systemctl start telegrambot telegrambot-web
```

**С web на main:**
```bash
cd /opt/telegrambot
sudo systemctl stop telegrambot telegrambot-web
sudo -u telegrambot git checkout main
sudo -u telegrambot git pull origin main
sudo systemctl start telegrambot telegrambot-web
```

## GitHub Actions для ветки web

Если используете CI/CD:

```yaml
# .github/workflows/deploy.yml
name: Deploy from web branch

on:
  push:
    branches:
      - web

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout web branch
        uses: actions/checkout@v3
        with:
          ref: web
      
      - name: Deploy
        run: |
          # Ваш скрипт развертывания
```

## Частые вопросы

### Q: Как установить только веб-интерфейс из ветки web?
```bash
git clone -b web --single-branch https://github.com/Nickto55/TelegrammBolt.git
cd TelegrammBolt
pip install -r requirements.txt
python web_app.py
```

### Q: Как автоматически обновляться из ветки web?
Создайте cron job:
```bash
sudo crontab -e

# Добавить строку (обновление каждый день в 3:00)
0 3 * * * cd /opt/telegrambot && sudo -u telegrambot git pull origin web && systemctl restart telegrambot telegrambot-web
```

### Q: Можно ли использовать разные ветки для бота и веба?
Да, создайте две директории:
```bash
# Бот из main
git clone -b main https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot-main

# Веб из web
git clone -b web https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot-web
```

## Получение ссылки на веб-интерфейс

После установки:
```bash
# Показать ссылку
bash /opt/telegrambot/show-web-url.sh

# Или открыть в браузере
http://ваш-сервер:5000/show-url
```

## Полезные команды

```bash
# Проверить ветку
cd /opt/telegrambot && git branch

# Обновить из web
cd /opt/telegrambot && sudo -u telegrambot git pull origin web

# Посмотреть изменения
cd /opt/telegrambot && git log --oneline -10

# Откатиться на предыдущую версию
cd /opt/telegrambot && sudo -u telegrambot git reset --hard HEAD~1

# Посмотреть разницу между main и web
cd /opt/telegrambot && git diff main..web
```

## Структура команд для быстрой установки

**Полная установка из web в одну команду:**
```bash
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/web/setup.sh | bash
```

**Или пошагово:**
```bash
# 1. Клонировать
git clone -b web --single-branch https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot

# 2. Установить
cd /opt/telegrambot && chmod +x setup.sh && ./setup.sh

# 3. Настроить
sudo nano /opt/telegrambot/ven_bot.json

# 4. Запустить
sudo systemctl start telegrambot telegrambot-web

# 5. Получить ссылку
bash /opt/telegrambot/show-web-url.sh
```

Готово! Теперь вы можете работать с веткой `web` и держать её отдельно от `main`! 🚀
