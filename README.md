# Telegram Bot - Система управления ДСЕ

Telegram бот с веб-интерфейсом для управления и учета.

## Системные требования

- **ОС**: Debian 10+ или Ubuntu 18.04+
- **Python**: 3.8+
- **Память**: минимум 512 MB RAM
- **Место**: ~200 MB свободного места

## Быстрая установка

### 1. Клонируйте репозиторий
```bash
git clone <your-repo-url>
cd TelegrammBolt
```

### 2. Запустите скрипт установки
```bash
chmod +x setup.sh
./setup.sh
```

Скрипт автоматически:
- Обновит систему
- Установит все необходимые зависимости
- Создаст виртуальное окружение Python
- Установит Python пакеты
- Настроит конфигурацию (попросит ввести токены)

### 3. Что нужно подготовить перед установкой

**Обязательно:**
- `BOT_TOKEN` - получите от [@BotFather](https://t.me/BotFather) в Telegram
- `ADMIN_ID` - ваш Telegram ID (узнайте у [@userinfobot](https://t.me/userinfobot))
- `BOT_USERNAME` - имя вашего бота без @

**Опционально (для email уведомлений):**
- SMTP сервер (например, Gmail)
- Email и пароль приложения

## Запуск проекта

После установки используйте один из скриптов:

### Интерактивный выбор
```bash
./start.sh
```
Выберите что запустить: бот, веб-интерфейс или оба.

### Только Telegram бот
```bash
./start_bot.sh
```

### Только веб-интерфейс
```bash
./start_web.sh
```
По умолчанию доступен на http://localhost:5000

## Структура проекта

```
TelegrammBolt/
├── bot/              # Telegram бот
├── web/              # Веб-интерфейс (Flask)
├── config/           # Конфигурационные файлы
├── data/             # Данные и фото
├── setup.sh          # Скрипт установки
├── start.sh          # Скрипт запуска
└── requirements.txt  # Python зависимости
```

## Конфигурация

### config/ven_bot.json
Основные настройки бота:
```json
{
  "BOT_TOKEN": "your_bot_token",
  "ADMIN_IDS": ["your_telegram_id"],
  "BOT_USERNAME": "your_bot_username"
}
```

### config/smtp_config.json (опционально)
Настройки email:
```json
{
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": 587,
  "SMTP_USER": "your_email@gmail.com",
  "SMTP_PASSWORD": "your_app_password",
  "FROM_NAME": "Bot Name"
}
```

## Возможные проблемы

### Ошибка: "Permission denied"
```bash
chmod +x setup.sh
```

### Порт 5000 занят
Измените порт в `web/web_app.py` или остановите процесс:
```bash
sudo lsof -ti:5000 | xargs kill -9
```

### Python версия < 3.8
Обновите Python:
```bash
sudo apt update
sudo apt install python3.10
```

## Поддержка

Если возникли проблемы при установке, проверьте:
1. Версию ОС: `lsb_release -a`
2. Версию Python: `python3 --version`
3. Наличие sudo прав
4. Подключение к интернету

---

**Важно**: Храните токены и пароли в безопасности. Не публикуйте файлы из `config/` в публичных репозиториях.
