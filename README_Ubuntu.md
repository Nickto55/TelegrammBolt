# TelegrammBolt - Telegram Bot для управления ДСЕ

## Описание

TelegrammBolt - это Telegram бот для учета и управления данными о деталях, узлах и процессах. Бот поддерживает работу с фотографиями, генерацию отчетов, чат с пользователями и интеграцию с внешними системами.

## Возможности

### Telegram Bot
- 📋 Учет проблем и замечаний по различным категориям
- 📸 Работа с фотографиями и их обработка
- 💬 Система чатов между пользователями
- 📊 Генерация PDF отчетов
- 📧 Отправка отчетов по email (Excel / Текст)
- 👥 Система прав доступа пользователей
- ⏰ Мониторинг и уведомления
- 🔄 Автоматический перезапуск при сбоях

### 🌐 Веб-интерфейс (НОВОЕ!)
- 🔐 Авторизация через Telegram (Login Widget)
- 📊 Веб-панель управления ДСЕ
- 📈 Интерактивная статистика
- 💬 Веб-чат с пользователями
- 📥 Экспорт данных (Excel, PDF)
- 📱 Адаптивный дизайн (работает на всех устройствах)
- 🔒 HTTPS защита
- 🚀 REST API для интеграций

## Системные требования

- **ОС:** Ubuntu 18.04+, Debian 9+, или совместимые
- **Python:** 3.9-3.12 (рекомендуется 3.11 или 3.12)
  - ⚠️ Python 3.13+ поддерживается, но требует обновленную версию python-telegram-bot
- **Память:** Минимум 512 MB RAM
- **Диск:** Минимум 500 MB свободного места
- **Сеть:** Доступ к Telegram API

> 📌 **Примечание:** Если у вас Python 3.13, см. [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md)

## Установка на Ubuntu/Debian

### Автоматическая установка (рекомендуется)

1. **Скачайте и запустите установочный скрипт:**
   ```bash
   wget https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup.sh
   chmod +x setup.sh
   ./setup.sh
   ```
   
   **Для старых версий Debian (если возникает ошибка с пакетами):**
   ```bash
   wget https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup_minimal.sh
   chmod +x setup_minimal.sh
   sudo ./setup_minimal.sh
   ```

2. **Настройте конфигурацию бота:**
   ```bash
   sudo nano /opt/telegrambot/ven_bot.json
   ```
   
   Замените значения в файле:
   ```json
   {
     "BOT_TOKEN": "ВАШ_ТОКЕН_БОТА",
     "ADMIN_IDS": ["ВАШ_TELEGRAM_ID"]
   }
   ```

3. **Запустите бота:**
   ```bash
   sudo systemctl start telegrambot
   sudo systemctl enable telegrambot
   ```

### Ручная установка

#### Предварительные требования

- Ubuntu 20.04+ или Debian 11+
- Python 3.8+
- Git

#### Пошаговая установка

1. **Обновите систему:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Установите необходимые пакеты:**
   ```bash
   sudo apt install -y python3 python3-pip python3-venv git curl wget build-essential
   ```

3. **Создайте пользователя для бота:**
   ```bash
   sudo useradd --system --shell /bin/bash --home /opt/telegrambot --create-home telegrambot
   ```

4. **Клонируйте репозиторий:**
   ```bash
   sudo git clone https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot
   sudo chown -R telegrambot:telegrambot /opt/telegrambot
   ```

5. **Создайте виртуальное окружение:**
   ```bash
   cd /opt/telegrambot
   sudo -u telegrambot python3 -m venv .venv
   sudo -u telegrambot .venv/bin/pip install --upgrade pip
   sudo -u telegrambot .venv/bin/pip install -r requirements.txt
   ```

6. **Настройте конфигурацию:**
   ```bash
   sudo -u telegrambot cp ven_bot.json.example ven_bot.json
   sudo nano /opt/telegrambot/ven_bot.json
   ```

7. **Установите systemd службу:**
   ```bash
   sudo cp /opt/telegrambot/telegrambot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable telegrambot
   sudo systemctl start telegrambot
   ```

## Конфигурация

### Основная конфигурация (ven_bot.json)

```json
{
  "BOT_TOKEN": "токен_вашего_бота_от_BotFather",
  "ADMIN_IDS": ["ваш_telegram_id"]
}
```

### Настройка SMTP (smtp_config.json)

Для отправки отчетов по email настройте SMTP:

```json
{
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": 587,
  "SMTP_USER": "your_email@gmail.com",
  "SMTP_PASSWORD": "your_app_password",
  "FROM_NAME": "Бот учета ДСЕ"
}
```

### Получение токена бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен

### Получение Telegram ID

1. Найдите [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте команду `/start`
3. Скопируйте ваш ID

## Управление службой

### Основные команды

```bash
# Запуск службы
sudo systemctl start telegrambot

# Остановка службы
sudo systemctl stop telegrambot

# Перезапуск службы
sudo systemctl restart telegrambot

# Статус службы
sudo systemctl status telegrambot

# Просмотр логов
sudo journalctl -u telegrambot -f

# Просмотр логов за последний час
sudo journalctl -u telegrambot --since "1 hour ago"
```

### Ручной запуск для тестирования

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

Или используйте скрипт запуска:
```bash
sudo -u telegrambot ./start_bot.sh
```

## Структура проекта

```
/opt/telegrambot/
├── bot.py                  # Основной файл бота
├── config.py              # Конфигурация
├── commands.py            # Обработчики команд
├── chat_manager.py        # Управление чатами
├── user_manager.py        # Управление пользователями
├── dse_manager.py         # Управление ДСЕ
├── dse_watcher.py         # Мониторинг ДСЕ
├── pdf_generator.py       # Генерация PDF
├── gui_manager.py         # Интерфейс пользователя
├── requirements.txt       # Python зависимости
├── start_bot.sh          # Скрипт запуска для Linux
├── setup.sh              # Установочный скрипт
├── telegrambot.service   # Конфигурация systemd
├── ven_bot.json          # Конфигурация бота
├── smtp_config.json      # Конфигурация SMTP
└── photos/               # Директория для фото
```

## Логирование

Бот использует стандартное логирование Python и systemd journal:

```bash
# Все логи службы
sudo journalctl -u telegrambot

# Логи в реальном времени
sudo journalctl -u telegrambot -f

# Логи с определенной даты
sudo journalctl -u telegrambot --since "2024-01-01"

# Логи за последние 100 строк
sudo journalctl -u telegrambot -n 100
```

## Безопасность

Служба настроена с повышенной безопасностью:

- Запуск от имени непривилегированного пользователя
- Ограничение доступа к файловой системе
- Изоляция временных файлов
- Ограничение системных вызовов

## Обновление

### Автоматическое обновление

```bash
cd /opt/telegrambot
sudo -u telegrambot git pull
sudo systemctl restart telegrambot
```

### Обновление зависимостей

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/pip install --upgrade -r requirements.txt
sudo systemctl restart telegrambot
```

## Резервное копирование

Регулярно создавайте резервные копии:

```bash
# Создание резервной копии конфигурации и данных
sudo tar -czf telegrambot-backup-$(date +%Y%m%d).tar.gz \
    -C /opt/telegrambot \
    ven_bot.json smtp_config.json *.json photos/

# Восстановление из резервной копии
sudo tar -xzf telegrambot-backup-YYYYMMDD.tar.gz -C /opt/telegrambot/
sudo chown -R telegrambot:telegrambot /opt/telegrambot/
sudo systemctl restart telegrambot
```

## Мониторинг

### Проверка состояния

```bash
# Статус службы
systemctl is-active telegrambot

# Время последнего запуска
systemctl show telegrambot --property=ActiveEnterTimestamp

# Использование ресурсов
systemctl status telegrambot
```

### Настройка уведомлений при сбоях

Создайте скрипт для уведомлений:

```bash
sudo nano /opt/telegrambot/notify-failure.sh
```

```bash
#!/bin/bash
# Уведомление о сбое службы
curl -s -X POST "https://api.telegram.org/botТОКЕН/sendMessage" \
    -d chat_id="ВАШ_ID" \
    -d text="⚠️ TelegrammBolt service failed on $(hostname)"
```

Добавьте в systemd службу:
```ini
[Unit]
OnFailure=notify-failure.service
```

## Устранение неполадок

### Общие проблемы

1. **Бот не отвечает:**
   ```bash
   sudo systemctl status telegrambot
   sudo journalctl -u telegrambot -n 50
   ```

2. **Ошибка токена:**
   - Проверьте правильность токена в `ven_bot.json`
   - Убедитесь, что бот не заблокирован

3. **Проблемы с правами:**
   ```bash
   sudo chown -R telegrambot:telegrambot /opt/telegrambot
   ```

4. **Ошибки Python:**
   ```bash
   cd /opt/telegrambot
   sudo -u telegrambot .venv/bin/python -m pip install --upgrade -r requirements.txt
   ```

### Отладка

Для детальной отладки запустите бота в режиме отладки:

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

Или с переменными окружения для дополнительной отладки:

```bash
cd /opt/telegrambot
sudo -u telegrambot PYTHONUNBUFFERED=1 .venv/bin/python bot.py
```

## 📚 Документация

### Установка и настройка бота
- **[QUICKSTART_Debian.md](QUICKSTART_Debian.md)** - Быстрый старт бота (5 минут)
- **[README_Ubuntu.md](README_Ubuntu.md)** - Этот файл, полная инструкция по боту
- **[SMTP_SETUP_INSTRUCTIONS.md](SMTP_SETUP_INSTRUCTIONS.md)** - Настройка email

### 🌐 Веб-интерфейс
- **[WEB_QUICKSTART.md](WEB_QUICKSTART.md)** ⚡ - Быстрый старт веб-интерфейса (10 минут)
- **[WEB_SETUP.md](WEB_SETUP.md)** - Полная инструкция по настройке веб-интерфейса
- **nginx.conf** - Конфигурация Nginx для production
- **web_app.py** - Главный файл веб-приложения

### Устранение проблем
- **[QUICK_FIX.md](QUICK_FIX.md)** ⚡ - Быстрые команды для частых проблем
- **[PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md)** - Проблемы с Python 3.13
- **[DOCKER_PYTHON_FIX.md](DOCKER_PYTHON_FIX.md)** - Решения для Docker
- **[NO_SYSTEMD.md](NO_SYSTEMD.md)** - Запуск без systemd (Docker, WSL1)

### Changelog и история
- **[CHANGELOG.md](CHANGELOG.md)** - История изменений проекта

### Скрипты установки
- **setup.sh** - Основной установщик (автоопределение systemd/init.d)
- **setup_minimal.sh** - Минимальная установка для старых систем
- **check_installation.sh** - Проверка корректности установки

## Частые проблемы и решения

### Python 3.13: AttributeError с Updater
```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/pip install --upgrade python-telegram-bot
sudo systemctl restart telegrambot
```
Подробно: [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md)

### systemctl: command not found
Система без systemd (Docker, WSL1). Используйте:
```bash
sudo service telegrambot start
```
Подробно: [NO_SYSTEMD.md](NO_SYSTEMD.md)

### Unable to locate package software-properties-common
Старый Debian. Используйте:
```bash
wget https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup_minimal.sh
sudo bash setup_minimal.sh
```

## Поддержка

- **GitHub:** https://github.com/Nickto55/TelegrammBolt
- **Issues:** https://github.com/Nickto55/TelegrammBolt/issues

## Лицензия

Этот проект распространяется под лицензией MIT. См. файл LICENSE для подробностей.