# Запуск TelegrammBolt без systemd

## Для контейнеров Docker, WSL1, старых систем

Если у вас система без systemd, используйте один из способов запуска:

### Способ 1: init.d служба (рекомендуется)

После установки через `setup.sh` или `setup_minimal.sh` автоматически создается init.d служба:

```bash
# Запуск
sudo service telegrambot start
# или
sudo /etc/init.d/telegrambot start

# Остановка
sudo service telegrambot stop

# Перезапуск
sudo service telegrambot restart

# Статус
sudo service telegrambot status
```

### Способ 2: Ручной запуск

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

### Способ 3: Использование screen/tmux

**С помощью screen:**
```bash
# Установка screen
sudo apt-get install screen

# Запуск в фоновом режиме
cd /opt/telegrambot
sudo -u telegrambot screen -dmS telegrambot .venv/bin/python bot.py

# Подключение к сессии
sudo -u telegrambot screen -r telegrambot

# Отключение от сессии: Ctrl+A, затем D
```

**С помощью tmux:**
```bash
# Установка tmux
sudo apt-get install tmux

# Запуск в фоновом режиме
cd /opt/telegrambot
sudo -u telegrambot tmux new-session -d -s telegrambot '.venv/bin/python bot.py'

# Подключение к сессии
sudo -u telegrambot tmux attach -t telegrambot

# Отключение от сессии: Ctrl+B, затем D
```

### Способ 4: Фоновый запуск с nohup

```bash
cd /opt/telegrambot
sudo -u telegrambot nohup .venv/bin/python bot.py > /var/log/telegrambot.log 2>&1 &

# Просмотр логов
tail -f /var/log/telegrambot.log

# Остановка (найти PID и завершить процесс)
ps aux | grep "python bot.py"
sudo kill <PID>
```

### Способ 5: Supervisor (для production)

```bash
# Установка
sudo apt-get install supervisor

# Создание конфигурации
sudo nano /etc/supervisor/conf.d/telegrambot.conf
```

Содержимое файла:
```ini
[program:telegrambot]
command=/opt/telegrambot/.venv/bin/python /opt/telegrambot/bot.py
directory=/opt/telegrambot
user=telegrambot
autostart=true
autorestart=true
stderr_logfile=/var/log/telegrambot.err.log
stdout_logfile=/var/log/telegrambot.out.log
```

Команды:
```bash
# Перечитать конфигурацию
sudo supervisorctl reread
sudo supervisorctl update

# Управление
sudo supervisorctl start telegrambot
sudo supervisorctl stop telegrambot
sudo supervisorctl restart telegrambot
sudo supervisorctl status telegrambot

# Логи
tail -f /var/log/telegrambot.out.log
```

## Автозапуск в Docker

Если используете Docker, добавьте в Dockerfile:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
```

Или используйте docker-compose.yml:

```yaml
version: '3'
services:
  telegrambot:
    build: .
    restart: always
    volumes:
      - ./ven_bot.json:/app/ven_bot.json
      - ./smtp_config.json:/app/smtp_config.json
      - ./bot_data.json:/app/bot_data.json
      - ./users_data.json:/app/users_data.json
    environment:
      - PYTHONUNBUFFERED=1
```

## Проверка работы

```bash
# Проверить запущенные процессы Python
ps aux | grep python

# Проверить, что бот отвечает
# Отправьте /start вашему боту в Telegram

# Мониторинг ресурсов
top -u telegrambot
```

## Остановка бота

```bash
# Через службу
sudo service telegrambot stop

# Вручную (найти PID)
ps aux | grep "python.*bot.py"
sudo kill <PID>

# Жесткая остановка
sudo pkill -f "python.*bot.py"
```

## Логи

```bash
# Если используется init.d служба, логи будут в syslog
sudo tail -f /var/log/syslog | grep telegrambot

# Для ручного запуска перенаправьте вывод
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py 2>&1 | tee bot.log
```
