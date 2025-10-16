# 🔧 Решение проблем TelegrammBolt

## ⚡ Быстрые ответы (FAQ)

| Вопрос | Ответ |
|--------|-------|
| **systemd-analyze не найден** | Это нормально для Docker. Запускайте бота напрямую: `python bot.py` → [подробнее](#-systemd-analyze-command-not-found) |
| **Python 3.13 предупреждение** | Это нормально! Установка продолжится автоматически → [подробнее](#-конфликт-версий-python) |
| **Docker не запускает службу** | Docker НЕ использует systemd. Используйте `CMD ["python", "bot.py"]` → [подробнее](#️-docker-не-использует-systemd) |
| **ImportError: show_pdf_export_menu** | Запустите `./emergency-fix.sh` → [подробнее](#-importerror-cannot-import-name-show_pdf_export_menu) |
| **Conflict: terminated by other getUpdates** | Остановите все копии бота: `pkill -f bot.py` → [подробнее](#-ошибка-подключения-к-telegram-api) |

---

## 🚨 Критические ошибки

### ❌ AttributeError: module 'telegram' has no attribute 'Bot'

**Причина**: Неправильная версия python-telegram-bot или конфликт с другой библиотекой `telegram`

**Решение:**

```bash
# 1. Полностью удалить конфликтующие пакеты
pip uninstall -y telegram python-telegram-bot telegram-bot

# 2. Установить правильную версию
pip install python-telegram-bot>=21.0

# 3. Проверка
python -c "from telegram import Bot; print('OK')"
```

**Автоматическое исправление:**

```bash
# Скрипт cleanup-bot.sh
chmod +x cleanup-bot.sh
./cleanup-bot.sh
```

---

### ❌ ImportError: cannot import name 'show_pdf_export_menu'

**Причина**: Отсутствует функция в `pdf_generator.py`

**Решение:**

```bash
# Автоматический фикс
chmod +x emergency-fix.sh
./emergency-fix.sh

# Или вручную добавьте в pdf_generator.py:
```

```python
async def show_pdf_export_menu(update, context):
    """Показывает меню экспорта PDF"""
    keyboard = [
        [InlineKeyboardButton("📄 Экспорт в PDF", callback_data="export_pdf")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )
```

---

### ❌ ModuleNotFoundError: No module named 'flask'

**Причина**: Не установлены зависимости для веб-интерфейса

**Решение:**

```bash
# Установить Flask
pip install flask flask-cors gunicorn

# Или обновить все зависимости
pip install -r requirements.txt
```

---

### ❌ Ошибка подключения к Telegram API

**Симптом:**
```
telegram.error.NetworkError: Connect timeout
```

**Решение:**

```bash
# 1. Проверить интернет
ping api.telegram.org

# 2. Проверить прокси (если используется)
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# 3. Увеличить таймаут в bot.py:
application = Application.builder().token(TOKEN).connect_timeout(30).build()

# 4. Проверить токен
python -c "from telegram import Bot; Bot('YOUR_TOKEN').get_me()"
```

---

### ❌ Бот не реагирует на команды

**Причина 1**: Не добавлен admin_id

```bash
# Узнать свой ID
# Напишите @userinfobot в Telegram

# Добавить в ven_bot.json
{
  "admin_ids": [123456789]
}
```

**Причина 2**: Бот не запущен

```bash
# Проверить статус службы
sudo systemctl status telegrambot

# Или запустить вручную
python bot.py
```

**Причина 3**: Конфликт экземпляров

```bash
# Найти все процессы бота
ps aux | grep bot.py

# Убить старые процессы
pkill -f bot.py

# Запустить заново
python bot.py
```

---

## 🐳 Docker проблемы

### ⚠️ Docker не использует systemd

**Важно:** Docker контейнеры обычно НЕ используют systemd!

**Правильный запуск в Docker:**

```bash
# В Dockerfile
CMD ["python", "bot.py"]

# Или docker-compose.yml
services:
  bot:
    command: python bot.py
    
# Ручной запуск в контейнере
cd /opt/telegrambot
python bot.py

# В фоне (внутри контейнера)
nohup python bot.py > /var/log/bot.log 2>&1 &
```

**Если setup.sh запущен в Docker:**

```bash
# Пропустить создание службы
export SKIP_SERVICE=1
bash setup.sh

# Или запустить бота вручную после установки
cd /opt/telegrambot
.venv/bin/python bot.py
```

---

### ❌ Cannot connect to Docker daemon

```bash
# Запустить Docker
sudo systemctl start docker

# Добавить пользователя в группу
sudo usermod -aG docker $USER
newgrp docker

# Перезапуск
sudo systemctl restart docker
```

---

### ❌ Permission denied при монтировании

```bash
# Изменить владельца
sudo chown -R 1000:1000 /opt/telegrambot

# Или запустить с правами root
docker-compose run --user root bot
```

---

### ❌ Контейнер постоянно перезапускается

```bash
# Проверить логи
docker logs telegrambot

# Остановить автоперезапуск
docker update --restart=no telegrambot

# Проверить конфигурацию
docker-compose config
```

---

## 🌐 Веб-интерфейс проблемы

### ❌ Telegram Login Widget не работает

**Причина**: Неправильный домен в настройках бота

**Решение:**

```bash
# 1. Открыть @BotFather
# 2. /setdomain
# 3. Выбрать бота
# 4. Указать ваш домен (например: bot.example.com)
# 5. Перезапустить веб-приложение

# Для локальной разработки используйте ngrok:
ngrok http 5000
# И укажите ngrok URL в @BotFather
```

---

### ❌ CORS ошибка в браузере

```python
# Добавить в web_app.py:
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['https://your-domain.com'])
```

---

### ❌ 502 Bad Gateway (Nginx)

```bash
# Проверить, что веб запущен
netstat -tulpn | grep 5000

# Проверить логи Nginx
sudo tail -f /var/log/nginx/error.log

# Проверить конфиг
sudo nginx -t

# Перезапустить Nginx
sudo systemctl restart nginx
```

---

## 📧 Email проблемы

### ❌ smtplib.SMTPAuthenticationError

**Решение для Gmail:**

```bash
# 1. Включить двухфакторную аутентификацию
# 2. Создать App Password: https://myaccount.google.com/apppasswords
# 3. Использовать этот пароль в smtp_config.json

{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "your@gmail.com",
  "smtp_password": "xxxx xxxx xxxx xxxx"
}
```

---

### ❌ smtplib.SMTPConnectError

```bash
# Проверить фаервол
sudo ufw allow 587/tcp
sudo ufw allow 465/tcp

# Проверить подключение
telnet smtp.gmail.com 587
```

---

## 💾 База данных проблемы

### ❌ JSON decode error

```bash
# Backup поврежденного файла
cp bot_data.json bot_data.json.backup

# Создать пустой
echo '{}' > bot_data.json

# Или восстановить из backup
cp bot_data.json.backup bot_data.json
python -c "import json; json.load(open('bot_data.json'))"
```

---

### ❌ Permission denied на запись

```bash
# Изменить владельца
sudo chown -R $USER:$USER /opt/telegrambot

# Или права
chmod 644 bot_data.json users_data.json
```

---

## 🔐 Systemd проблемы

### ❌ systemd-analyze: command not found

**Причина**: Docker контейнеры обычно не используют systemd

**Решение для Docker:**

```bash
# Запустить бота напрямую (рекомендуется для Docker)
cd /opt/telegrambot
.venv/bin/python bot.py

# Или в фоне
nohup .venv/bin/python bot.py > bot.log 2>&1 &

# Проверить процесс
ps aux | grep bot.py
```

**Решение для обычных систем:**

```bash
# Если systemd-analyze недоступен, проверить службу вручную
cat /etc/systemd/system/telegrambot.service

# Перезагрузить конфигурацию
sudo systemctl daemon-reload

# Запустить службу
sudo systemctl start telegrambot
```

---

### ❌ Failed to start service

```bash
# Проверить синтаксис (если доступен systemd-analyze)
sudo systemd-analyze verify /etc/systemd/system/telegrambot.service 2>/dev/null

# Перезагрузить конфигурацию
sudo systemctl daemon-reload

# Проверить логи
sudo journalctl -u telegrambot -n 50 --no-pager

# Запустить вручную для отладки
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

---

### ❌ Служба не перезапускается после краша

```bash
# Увеличить RestartSec в службе
sudo nano /etc/systemd/system/telegrambot.service

# Добавить:
[Service]
Restart=always
RestartSec=10
StartLimitInterval=0
```

---

## 📦 Проблемы зависимостей

### ❌ Конфликт версий Python

```bash
# Установить нужную версию
sudo apt install python3.12 python3.12-venv

# Пересоздать виртуальное окружение
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### ❌ pip устарел

```bash
# Обновить pip
pip install --upgrade pip setuptools wheel

# Или через apt
sudo apt install --reinstall python3-pip
```

---

### ❌ SSL certificate verify failed

```bash
# Временно отключить проверку (НЕ для production!)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Или обновить сертификаты
sudo apt install ca-certificates
sudo update-ca-certificates
```

---

## 🔍 Диагностика

### Проверка всех компонентов

```bash
# Создать diagnostic.sh
cat > diagnostic.sh << 'EOF'
#!/bin/bash
echo "=== Python ==="
python3 --version
which python3

echo -e "\n=== Виртуальное окружение ==="
source .venv/bin/activate
pip list | grep telegram

echo -e "\n=== Конфигурация ==="
python -c "import json; print(json.load(open('ven_bot.json')))" 2>&1

echo -e "\n=== Токен ==="
python -c "from telegram import Bot; import json; Bot(json.load(open('ven_bot.json'))['bot_token']).get_me()" 2>&1

echo -e "\n=== Служба ==="
systemctl status telegrambot --no-pager

echo -e "\n=== Логи ==="
sudo journalctl -u telegrambot -n 20 --no-pager

echo -e "\n=== Процессы ==="
ps aux | grep bot.py

echo -e "\n=== Порты ==="
netstat -tulpn | grep 5000
EOF

chmod +x diagnostic.sh
./diagnostic.sh
```

---

## 🆘 Экстренные скрипты

### emergency-fix.sh

```bash
#!/bin/bash
# Полное исправление всех известных проблем

echo "🔧 Экстренное исправление бота..."

# Остановить бота
sudo systemctl stop telegrambot 2>/dev/null
pkill -f bot.py

# Очистка зависимостей
pip uninstall -y telegram python-telegram-bot telegram-bot
pip install python-telegram-bot>=21.0

# Исправление pdf_generator.py
if ! grep -q "show_pdf_export_menu" pdf_generator.py; then
    cat >> pdf_generator.py << 'EOF'

async def show_pdf_export_menu(update, context):
    """Показывает меню экспорта PDF"""
    keyboard = [
        [InlineKeyboardButton("📄 Экспорт в PDF", callback_data="export_pdf")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
EOF
fi

# Проверка конфигурации
python -c "import json; json.load(open('ven_bot.json'))" || echo "{}" > ven_bot.json

# Перезапуск
sudo systemctl start telegrambot

echo "✅ Исправление завершено!"
```

---

### cleanup-bot.sh

```bash
#!/bin/bash
# Полная очистка и переустановка

echo "🧹 Полная очистка..."

# Остановить все
sudo systemctl stop telegrambot
pkill -f bot.py
docker-compose down 2>/dev/null

# Очистка Python
pip freeze | xargs pip uninstall -y
pip install -r requirements.txt

# Очистка данных (ОСТОРОЖНО!)
# rm -f bot_data.json users_data.json

# Перезапуск
sudo systemctl start telegrambot

echo "✅ Очистка завершена!"
```

---

## 📞 Получение помощи

### Сбор информации для баг-репорта

```bash
# Создать bug-report.txt
cat > bug-report.txt << EOF
=== Системная информация ===
$(uname -a)
$(python3 --version)
$(pip list | grep telegram)

=== Логи ===
$(sudo journalctl -u telegrambot -n 100 --no-pager)

=== Конфигурация ===
$(cat ven_bot.json | sed 's/"bot_token": ".*"/"bot_token": "HIDDEN"/g')

=== Ошибка ===
[Вставьте текст ошибки сюда]
EOF

# Отправить на GitHub Issues
```

---

## ✅ Быстрые решения (Cheatsheet)

| Проблема | Команда |
|----------|---------|
| Переустановить telegram | `pip uninstall -y telegram python-telegram-bot && pip install python-telegram-bot>=21.0` |
| Перезапустить бота | `sudo systemctl restart telegrambot` |
| Посмотреть логи | `sudo journalctl -u telegrambot -f` |
| Убить процесс бота | `pkill -f bot.py` |
| Проверить токен | `python -c "from telegram import Bot; Bot('TOKEN').get_me()"` |
| Очистить данные | `rm -f bot_data.json users_data.json` |
| Пересоздать venv | `rm -rf .venv && python3 -m venv .venv` |

---

**Не нашли решение?** Смотрите [CHEATSHEET.md](CHEATSHEET.md) или создайте [Issue на GitHub](https://github.com/Nickto55/TelegrammBolt/issues)
