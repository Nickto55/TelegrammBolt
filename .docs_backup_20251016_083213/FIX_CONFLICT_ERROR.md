# 🔧 Решение ошибки "Conflict: terminated by other getUpdates request"

## ❌ Проблема

```
telegram.error.Conflict: Conflict: terminated by other getUpdates request; 
make sure that only one bot instance is running
```

**Причина:** Несколько экземпляров бота пытаются одновременно получать обновления от Telegram API.

## ✅ Решение

### Шаг 1: Остановить все запущенные экземпляры

```bash
# В Docker контейнере
# Остановить службу
sudo service telegrambot stop

# Проверить запущенные процессы
ps aux | grep bot.py

# Убить все процессы бота (если есть)
pkill -f "python.*bot.py"

# ИЛИ найти PID и убить вручную
ps aux | grep bot.py
kill -9 <PID>
```

### Шаг 2: Проверить, что процессов нет

```bash
ps aux | grep bot.py
# Должен показать только сам grep, без python процессов
```

### Шаг 3: Запустить бота правильно

**Вариант A: Через службу (рекомендуется)**
```bash
# Запустить службу
sudo service telegrambot start

# Проверить статус
sudo service telegrambot status

# Посмотреть логи
tail -f /opt/telegrambot/telegrambot.log
```

**Вариант B: Вручную (для отладки)**
```bash
# Остановить службу сначала!
sudo service telegrambot stop

# Запустить вручную
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

## 🚨 Частые ошибки

### 1. Служба запущена в фоне + ручной запуск

```bash
# ❌ НЕПРАВИЛЬНО - конфликт
sudo service telegrambot start      # Запускает в фоне
python bot.py                       # Запускает второй экземпляр

# ✅ ПРАВИЛЬНО - выберите один способ
sudo service telegrambot start      # ЛИБО служба
# ИЛИ
python bot.py                       # ЛИБО вручную (остановив службу)
```

### 2. Бот запущен на другом сервере/контейнере

Один токен = один активный бот.

```bash
# Проверить, где еще может быть запущен бот:
# - На хост-машине (вне Docker)
# - В другом Docker контейнере
# - На другом сервере
# - В IDE (PyCharm, VS Code) с запущенным bot.py
```

### 3. Webhook не отключен

Если раньше использовали webhook:

```bash
# Проверить webhook
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"

# Удалить webhook
curl "https://api.telegram.org/bot<YOUR_TOKEN>/deleteWebhook"
```

## 📋 Полная процедура очистки

```bash
#!/bin/bash

echo "🔍 Поиск всех процессов бота..."
ps aux | grep -E "bot\.py|telegrambot" | grep -v grep

echo "🛑 Остановка службы..."
sudo service telegrambot stop

echo "💀 Убийство всех процессов Python с bot.py..."
pkill -9 -f "python.*bot.py"

echo "⏱️  Ожидание 5 секунд..."
sleep 5

echo "🔍 Проверка процессов снова..."
ps aux | grep -E "bot\.py|telegrambot" | grep -v grep

echo "✅ Очистка завершена! Теперь можно запускать бота."
echo ""
echo "Запустите: sudo service telegrambot start"
```

Сохраните как `cleanup-bot.sh` и запустите:

```bash
chmod +x cleanup-bot.sh
./cleanup-bot.sh
```

## 🐳 Docker-специфичные команды

### Если бот в Docker

```bash
# Остановить контейнер
docker stop <container_name>

# Или перезапустить
docker restart <container_name>

# Или удалить и создать заново
docker-compose down
docker-compose up -d

# Посмотреть логи
docker logs -f <container_name>
```

### Если бот на хосте И в Docker

```bash
# На хосте
sudo service telegrambot stop
pkill -f "python.*bot.py"

# В контейнере
docker exec <container_name> pkill -f "python.*bot.py"
docker exec <container_name> service telegrambot stop
```

## 📊 Мониторинг

### Скрипт для проверки статуса

```bash
#!/bin/bash

echo "📊 Статус TelegrammBolt"
echo "======================="
echo ""

# Проверка службы
echo "🔧 Статус службы:"
service telegrambot status
echo ""

# Проверка процессов
echo "🔍 Процессы Python:"
ps aux | grep "bot.py" | grep -v grep || echo "Нет запущенных процессов"
echo ""

# Проверка портов (если есть веб-интерфейс)
echo "🌐 Открытые порты:"
netstat -tulpn | grep :5000 || echo "Порт 5000 не занят"
echo ""

# Последние строки лога
echo "📝 Последние 10 строк лога:"
tail -10 /opt/telegrambot/telegrambot.log 2>/dev/null || echo "Лог не найден"
```

Сохраните как `check-bot-status.sh`

## 🔐 Проверка токена

Убедитесь, что используется правильный токен:

```bash
# Показать текущий токен (без полного значения)
cat /opt/telegrambot/ven_bot.json | grep -o '"bot_token": "[^"]*"' | cut -c 1-30

# Проверить токен через API
TOKEN=$(cat /opt/telegrambot/ven_bot.json | grep -o '"bot_token": "[^"]*"' | cut -d'"' -f4)
curl "https://api.telegram.org/bot${TOKEN}/getMe"
```

## ⚡ Быстрое решение (TL;DR)

```bash
# 1. Убить все
sudo service telegrambot stop
pkill -9 -f "python.*bot.py"

# 2. Подождать
sleep 3

# 3. Запустить заново
sudo service telegrambot start

# 4. Проверить
sudo service telegrambot status
tail -f /opt/telegrambot/telegrambot.log
```

## 🆘 Если ничего не помогает

### 1. Проверить другие места

```bash
# Проверить все Python процессы
ps aux | grep python

# Проверить systemd (если есть)
systemctl status telegrambot 2>/dev/null

# Проверить cron задачи
crontab -l | grep bot
```

### 2. Перезапустить контейнер

```bash
# Docker
docker restart <container_name>

# Docker Compose
docker-compose restart
```

### 3. Удалить lockfile (если есть)

```bash
rm -f /opt/telegrambot/*.lock
rm -f /opt/telegrambot/*.pid
```

### 4. Создать новый токен

В крайнем случае:
1. Перейдите к [@BotFather](https://t.me/BotFather)
2. Отправьте `/mybots`
3. Выберите своего бота
4. API Token → Revoke current token
5. Обновите `ven_bot.json` с новым токеном

## 📚 Дополнительная информация

- [Официальная документация Telegram Bot API](https://core.telegram.org/bots/api)
- [python-telegram-bot документация](https://docs.python-telegram-bot.org/)
- [Основная документация проекта](README_Ubuntu.md)

---

**Важно:** Никогда не запускайте бота одновременно через службу И вручную!
