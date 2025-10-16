# 🚀 Быстрый старт в Docker - Решение конфликтов

## ❌ Проблема
```
telegram.error.Conflict: Conflict: terminated by other getUpdates request
```

## ✅ Быстрое решение (3 команды)

### Внутри Docker контейнера:

```bash
# 1. Остановить все
sudo service telegrambot stop
pkill -9 -f "python.*bot.py"

# 2. Подождать 3 секунды
sleep 3

# 3. Запустить заново
sudo service telegrambot start
```

### Или использовать скрипт очистки:

```bash
bash /opt/telegrambot/cleanup-bot.sh
```

## 📋 Полная процедура для Docker

### Вариант 1: Использовать cleanup-bot.sh (рекомендуется)

```bash
# Внутри контейнера
root@container:/# bash /opt/telegrambot/cleanup-bot.sh
```

Скрипт автоматически:
- Найдет все процессы
- Остановит службу
- Завершит процессы
- Удалит lock файлы
- Проверит webhook
- Покажет инструкции по запуску

### Вариант 2: Вручную остановить и запустить

```bash
# Шаг 1: Остановить службу
root@container:/# sudo service telegrambot stop

# Шаг 2: Проверить процессы
root@container:/# ps aux | grep bot.py

# Шаг 3: Убить процессы (если есть)
root@container:/# pkill -9 -f "python.*bot.py"

# Шаг 4: Убедиться что нет процессов
root@container:/# ps aux | grep bot.py
# Должен показать только grep

# Шаг 5: Запустить заново
root@container:/# sudo service telegrambot start

# Шаг 6: Проверить статус
root@container:/# sudo service telegrambot status
```

### Вариант 3: Перезапуск контейнера (с хост-машины)

```bash
# Перезапустить весь контейнер
docker restart <container_name>

# Или с docker-compose
docker-compose restart

# Посмотреть логи
docker logs -f <container_name>
```

## 🔍 Диагностика

### Проверить запущенные процессы:

```bash
# Все процессы Python
ps aux | grep python

# Только bot.py
ps aux | grep bot.py | grep -v grep

# Показать PID и команду
pgrep -a -f "bot.py"
```

### Проверить статус службы:

```bash
# Статус
sudo service telegrambot status

# Или
systemctl status telegrambot 2>/dev/null
```

### Проверить логи:

```bash
# Последние 20 строк
tail -20 /opt/telegrambot/telegrambot.log

# Следить в реальном времени
tail -f /opt/telegrambot/telegrambot.log

# Найти ошибки
grep -i "error\|conflict" /opt/telegrambot/telegrambot.log
```

## 🎯 Правильный запуск бота

### ✅ ПРАВИЛЬНО - Через службу:

```bash
# Запустить службу
sudo service telegrambot start

# Проверить
sudo service telegrambot status

# Логи
tail -f /opt/telegrambot/telegrambot.log
```

### ✅ ПРАВИЛЬНО - Вручную (только для отладки):

```bash
# СНАЧАЛА остановить службу!
sudo service telegrambot stop

# Убедиться что нет других процессов
ps aux | grep bot.py

# Запустить вручную
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

### ❌ НЕПРАВИЛЬНО - Два экземпляра:

```bash
# ❌ НЕ ДЕЛАЙТЕ ТАК!
sudo service telegrambot start  # Запускает в фоне
python bot.py                   # Запускает второй экземпляр = КОНФЛИКТ!
```

## 🔐 Дополнительные проверки

### Проверить webhook:

```bash
# Получить токен
TOKEN=$(grep -o '"bot_token": *"[^"]*"' /opt/telegrambot/ven_bot.json | cut -d'"' -f4)

# Проверить webhook
curl "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"

# Удалить webhook (если есть)
curl "https://api.telegram.org/bot${TOKEN}/deleteWebhook"
```

### Проверить конфигурацию:

```bash
# Показать конфигурацию (без токена)
cat /opt/telegrambot/ven_bot.json | grep -v "bot_token"

# Проверить права
ls -la /opt/telegrambot/ven_bot.json

# Проверить что токен не пустой
grep "bot_token" /opt/telegrambot/ven_bot.json
```

## 📊 Мониторинг после запуска

### Проверить что бот работает:

```bash
# Процесс запущен?
ps aux | grep bot.py | grep -v grep

# Служба активна?
sudo service telegrambot status

# Логи без ошибок?
tail -20 /opt/telegrambot/telegrambot.log | grep -i error
```

### Отправить тестовое сообщение боту:

1. Откройте Telegram
2. Найдите своего бота
3. Отправьте `/start`
4. Бот должен ответить

Если не отвечает:
```bash
# Посмотрите логи в реальном времени
tail -f /opt/telegrambot/telegrambot.log

# И попробуйте команду снова
```

## 🆘 Если ничего не помогает

### 1. Полная остановка всех процессов:

```bash
# Убить абсолютно все Python процессы
pkill -9 python

# Подождать
sleep 5

# Запустить заново
sudo service telegrambot start
```

### 2. Удалить все lock файлы:

```bash
rm -f /opt/telegrambot/*.lock
rm -f /opt/telegrambot/*.pid
rm -f /opt/telegrambot/*.socket
```

### 3. Перезапустить контейнер (с хоста):

```bash
docker restart <container_name>
```

### 4. Создать новый токен:

1. [@BotFather](https://t.me/BotFather) → `/mybots`
2. Выбрать бота → API Token → Revoke current token
3. Скопировать новый токен
4. Обновить в контейнере:
   ```bash
   nano /opt/telegrambot/ven_bot.json
   # Заменить bot_token
   ```
5. Перезапустить бота

## 📚 Полезные ссылки

- **Полная инструкция:** [FIX_CONFLICT_ERROR.md](FIX_CONFLICT_ERROR.md)
- **Основная документация:** [README_Ubuntu.md](README_Ubuntu.md)
- **Шпаргалка команд:** [CHEATSHEET.md](CHEATSHEET.md)
- **Решение проблем Python 3.13:** [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md)

---

## 💡 Совет

**Сохраните эту команду** для быстрого решения:

```bash
sudo service telegrambot stop && pkill -9 -f "python.*bot.py" && sleep 3 && sudo service telegrambot start
```

Или просто:

```bash
bash /opt/telegrambot/cleanup-bot.sh
```

**Помните:** Один токен = один активный бот! 🤖
