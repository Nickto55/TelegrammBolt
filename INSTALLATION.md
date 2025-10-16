# 📦 Установка TelegrammBolt

## 🚀 Быстрая установка

### Ubuntu/Debian (рекомендуется)

```bash
# Автоматическая установка
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup.sh | bash

# Или вручную:
git clone https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot
cd /opt/telegrambot
sudo bash setup.sh
```

### С веб-интерфейсом (ветка web)

```bash
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/web/setup.sh | bash
```

---

## ⚙️ Ручная установка

### 1. Установка зависимостей

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# Проверка Python
python3 --version  # Рекомендуется 3.9-3.12
```

### 2. Клонирование репозитория

```bash
# Основная ветка (только бот)
git clone https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot

# Ветка web (бот + веб-интерфейс)
git clone -b web https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot

cd /opt/telegrambot
```

### 3. Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройка конфигурации

```bash
# Создать конфиг из примера
cp ven_bot.json.example ven_bot.json
nano ven_bot.json
```

**Обязательно заполните:**
- `bot_token` - токен бота от [@BotFather](https://t.me/BotFather)
- `admin_ids` - ваш Telegram ID от [@userinfobot](https://t.me/userinfobot)

### 5. Email настройка (опционально)

```bash
cp smtp_config.json.example smtp_config.json
nano smtp_config.json
```

### 6. Запуск

```bash
# Тестовый запуск
python bot.py

# Через службу (рекомендуется)
sudo systemctl enable --now telegrambot
```

---

## 🐳 Docker

### Быстрый старт

```bash
# Создать docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  bot:
    image: python:3.12-slim
    working_dir: /app
    volumes:
      - ./:/app
    command: sh -c "pip install -r requirements.txt && python bot.py"
    restart: unless-stopped
EOF

# Запустить
docker-compose up -d
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
```

---

## 🔧 Systemd служба

### Создание службы

```bash
sudo nano /etc/systemd/system/telegrambot.service
```

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

### Управление службой

```bash
# Запуск
sudo systemctl start telegrambot
sudo systemctl enable telegrambot

# Статус
sudo systemctl status telegrambot

# Логи
sudo journalctl -u telegrambot -f
```

---

## 🌐 Веб-интерфейс

### Установка

```bash
# Установить дополнительные зависимости
pip install flask flask-cors gunicorn

# Запустить веб
python web_app.py

# Или через Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

### Nginx (рекомендуется)

```bash
sudo nano /etc/nginx/sites-available/telegrambot
```

```nginx
server {
    listen 80;
    server_name bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d bot.example.com
```

---

## 📋 Проверка установки

```bash
# Проверить зависимости
pip list | grep telegram

# Проверить конфигурацию
python -c "import json; print(json.load(open('ven_bot.json')))"

# Проверить бота
python -c "from telegram import Bot; print(Bot('YOUR_TOKEN').get_me())"

# Тест запуска
python bot.py
```

---

## 🔄 Обновление

```bash
cd /opt/telegrambot
sudo systemctl stop telegrambot

# Backup
cp -r /opt/telegrambot /opt/telegrambot.backup

# Обновление
git pull origin main  # или web

# Зависимости
.venv/bin/pip install --upgrade -r requirements.txt

# Запуск
sudo systemctl start telegrambot
```

---

## ⚠️ Без systemd (init.d)

### Создание init.d скрипта

```bash
sudo nano /etc/init.d/telegrambot
```

```bash
#!/bin/bash
DAEMON=/opt/telegrambot/.venv/bin/python
DAEMON_ARGS="bot.py"
PIDFILE=/var/run/telegrambot.pid

case "$1" in
  start)
    start-stop-daemon --start --background --make-pidfile --pidfile $PIDFILE --chdir /opt/telegrambot --exec $DAEMON -- $DAEMON_ARGS
    ;;
  stop)
    start-stop-daemon --stop --pidfile $PIDFILE
    ;;
  restart)
    $0 stop
    $0 start
    ;;
  *)
    echo "Usage: /etc/init.d/telegrambot {start|stop|restart}"
    exit 1
    ;;
esac
```

```bash
sudo chmod +x /etc/init.d/telegrambot
sudo update-rc.d telegrambot defaults
sudo service telegrambot start
```

---

## 🐛 Частые проблемы

### Python 3.13+

```bash
# Установить совместимую версию
sudo apt install python3.12 python3.12-venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Ошибка импорта

```bash
# Переустановить зависимости
pip install --force-reinstall -r requirements.txt
```

### Порт занят

```bash
# Найти процесс
sudo netstat -tulpn | grep 5000

# Убить процесс
sudo kill -9 <PID>
```

---

## 📞 Поддержка

- **Документация**: [README.md](README.md)
- **Проблемы**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Команды**: [CHEATSHEET.md](CHEATSHEET.md)
- **GitHub**: [Issues](https://github.com/Nickto55/TelegrammBolt/issues)

---

**Готово!** Бот установлен и готов к работе 🎉
