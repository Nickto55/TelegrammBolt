# 🚀 Быстрый старт TelegrammBolt на Debian/Ubuntu

## Автоматическая установка (5 минут)

### Шаг 1: Скачайте и запустите установщик

**Стандартная установка:**
```bash
wget https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup.sh
chmod +x setup.sh
./setup.sh
```

**Альтернатива для старых версий Debian (если возникает ошибка с пакетами):**
```bash
wget https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup_minimal.sh
chmod +x setup_minimal.sh
sudo ./setup_minimal.sh
```

### Шаг 2: Получите токен бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и скопируйте токен

### Шаг 3: Получите свой Telegram ID

1. Откройте [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте команду `/start`
3. Скопируйте ваш ID

### Шаг 4: Настройте конфигурацию

```bash
sudo nano /opt/telegrambot/ven_bot.json
```

Вставьте ваши данные:
```json
{
  "BOT_TOKEN": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
  "ADMIN_IDS": ["123456789"]
}
```

Сохраните: `Ctrl+O`, `Enter`, выйдите: `Ctrl+X`

### Шаг 5: Запустите бота

```bash
sudo systemctl start telegrambot
sudo systemctl enable telegrambot
```

### Шаг 6: Проверьте статус

```bash
sudo systemctl status telegrambot
```

Если всё OK — увидите `active (running)` 🟢

## Полезные команды

```bash
# Просмотр логов в реальном времени
sudo journalctl -u telegrambot -f

# Перезапуск бота
sudo systemctl restart telegrambot

# Остановка бота
sudo systemctl stop telegrambot

# Ручной запуск для тестирования
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

## Настройка SMTP (опционально)

Для отправки отчетов по email:

```bash
sudo nano /opt/telegrambot/smtp_config.json
```

Пример для Gmail:
```json
{
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": 587,
  "SMTP_USER": "your_email@gmail.com",
  "SMTP_PASSWORD": "your_app_password",
  "FROM_NAME": "TelegrammBolt"
}
```

> 💡 Для Gmail используйте [App Password](https://support.google.com/accounts/answer/185833)

## Возможные проблемы

### sudo: systemctl: command not found

Эта ошибка возникает в системах без systemd (контейнеры Docker, WSL1, старые версии).

**Решение:**
Скрипт автоматически создаст init.d службу. Используйте команды:

```bash
# Запуск
sudo service telegrambot start

# Проверка статуса
sudo service telegrambot status

# Остановка
sudo service telegrambot stop

# Перезапуск
sudo service telegrambot restart
```

**Ручной запуск (альтернатива):**
```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

### Unable to locate package software-properties-common

Эта ошибка возникает на старых версиях Debian. Решение:

```bash
# Используйте минимальную версию установщика
wget https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup_minimal.sh
chmod +x setup_minimal.sh
sudo ./setup_minimal.sh
```

### AttributeError: 'Updater' object has no attribute '_Updater__polling_cleanup_cb'

Эта ошибка возникает при использовании Python 3.13. Решение:

**Вариант 1 (быстрое решение):**
```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/pip install --upgrade python-telegram-bot
sudo systemctl restart telegrambot
```

**Вариант 2 (для Ubuntu):**
```bash
# Установить Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv

# Пересоздать окружение
cd /opt/telegrambot
sudo rm -rf .venv
sudo -u telegrambot python3.12 -m venv .venv
sudo -u telegrambot .venv/bin/pip install --upgrade pip
sudo -u telegrambot .venv/bin/pip install -r requirements.txt
sudo systemctl restart telegrambot
```

**Подробная документация:** [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md)

### Бот не отвечает

```bash
# Проверьте логи
sudo journalctl -u telegrambot -n 50

# Проверьте конфигурацию
sudo nano /opt/telegrambot/ven_bot.json
```

### Ошибка прав доступа

```bash
sudo chown -R telegrambot:telegrambot /opt/telegrambot
sudo systemctl restart telegrambot
```

### Проблемы с Python зависимостями

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/pip install --upgrade -r requirements.txt
sudo systemctl restart telegrambot
```

## Что дальше?

- 📖 Полная документация: [README_Ubuntu.md](README_Ubuntu.md)
- 🐛 Сообщить об ошибке: [GitHub Issues](https://github.com/Nickto55/TelegrammBolt/issues)
- 📧 Настройка SMTP: [SMTP_SETUP_INSTRUCTIONS.md](SMTP_SETUP_INSTRUCTIONS.md)

---

**Готово!** 🎉 Откройте Telegram и отправьте `/start` вашему боту!
