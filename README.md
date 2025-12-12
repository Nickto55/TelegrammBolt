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
- Установит все необходимые зависимости (Python, Nginx, Certbot)
- Создаст виртуальное окружение Python
- Установит Python пакеты
- Настроит конфигурацию (попросит ввести токены)
- Настроит домен и SSL сертификат (опционально)
- Создаст systemd сервисы для автозапуска
- Установит панель управления

### 3. Что нужно подготовить перед установкой

**Обязательно:**
- `BOT_TOKEN` - получите от [@BotFather](https://t.me/BotFather) в Telegram
- `ADMIN_ID` - ваш Telegram ID (узнайте у [@userinfobot](https://t.me/userinfobot))
- `BOT_USERNAME` - имя вашего бота без @

**Опционально (для email уведомлений):**
- SMTP сервер (например, Gmail)
- Email и пароль приложения

## Запуск проекта

### Панель управления (рекомендуется)
```bash
./manage.sh
```

Интерактивная панель в стиле X-UI с возможностями:
- Запуск/остановка/перезапуск всех сервисов
- Мониторинг статуса в реальном времени
- Просмотр логов
- Настройка и обновление SSL сертификатов
- Редактирование конфигурации
- Резервное копирование данных
- Мониторинг системы

### Управление через systemd (автозапуск)
```bash
# Запуск сервисов
sudo systemctl start telegrambot
sudo systemctl start telegramweb

# Добавить в автозагрузку
sudo systemctl enable telegrambot
sudo systemctl enable telegramweb

# Проверить статус
sudo systemctl status telegrambot
sudo systemctl status telegramweb
```

### Традиционные скрипты

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
### config/domain.conf (если настроен SSL)
Настройки домена и SSL:
```bash
DOMAIN=bot.example.com
SSL_EMAIL=admin@example.com
WEB_PORT=5000
SSL_ENABLED=true
```

## SSL и Домен

### Первоначальная настройка
## Возможные проблемы

### Ошибка: "Permission denied"
```bash
chmod +x setup.sh manage.sh
```

### Порт 5000 или 80 занят
Проверьте какой процесс использует порт:
```bash
sudo lsof -ti:5000 | xargs kill -9  # Для порта 5000
sudo lsof -ti:80 | xargs kill -9    # Для порта 80
```

### SSL сертификат не получается
1. Проверьте что домен указывает на ваш IP
2. Убедитесь что порты 80 и 443 открыты
3. Проверьте firewall: `sudo ufw allow 80,443/tcp`

### Сервисы не запускаются
Проверьте логи:
```bash
sudo journalctl -u telegrambot -n 50
sudo journalctl -u telegramweb -n 50
```

### Python версия < 3.8
Обновите Python:
```bash
sudo apt update
sudo apt install python3.10
```

## Команды управления

### Просмотр логов
```bash
# Через панель управления
./manage.sh  # Выберите "6. Просмотр логов"

# Напрямую
sudo journalctl -u telegrambot -f    # Live логи бота
sudo journalctl -u telegramweb -f    # Live логи веб
tail -f /var/log/nginx/access.log    # Логи nginx
```

### Резервное копирование
```bash
# Через панель управления
./manage.sh  # Выберите "11. Резервное копирование"

# Вручную
tar -czf backup_$(date +%Y%m%d).tar.gz config/ data/
```

### Обновление проекта
```bash
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart telegrambot telegramweb
``` config/           # Конфигурационные файлы
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

## Диагностика DNS и SSL

### Быстрая проверка
```bash
chmod +x check-dns.sh
./check-dns.sh
```

Этот скрипт автоматически проверит и покажет:
- IP вашего сервера
- DNS резолвинг домена (локально и через Google/Cloudflare DNS)
- Совпадение IP сервера и домена
- Открытые порты (80, 443)
- Настройки firewall
- Доступность HTTP/HTTPS
- Рекомендации по исправлению проблем

### Проблемы с DuckDNS

Если используете DuckDNS (*.duckdns.org):

1. **Обновите IP адрес:**
   ```bash
   # Узнайте текущий IP
   curl ifconfig.me
   
   # Обновите в панели DuckDNS или через API
   curl "https://www.duckdns.org/update?domains=ваш_поддомен&token=ваш_токен&ip="
   ```

2. **Проверьте DNS:**
   ```bash
   dig +short ваш_домен.duckdns.org
   # Должен вернуть IP вашего сервера
   ```

3. **Если DNS не работает** - см. детальную инструкцию:
   ```bash
   cat SSL_TROUBLESHOOTING.md
   ```

### Альтернативные методы SSL

Если автоматический метод не работает:

**Standalone режим (рекомендуется для DuckDNS):**
```bash
sudo systemctl stop nginx
sudo certbot certonly --standalone -d ваш_домен.com
sudo systemctl start nginx
```

**Использование без SSL (для тестирования):**
```bash
# Доступ по HTTP без HTTPS
http://ваш_домен.com
# или по IP
http://ваш_IP:5000
```

Детальная инструкция: **SSL_TROUBLESHOOTING.md**

## Документация

-  **SELF_SIGNED_SSL.md** - Полное руководство по самоподписанным SSL сертификатам
-  **SSL_TROUBLESHOOTING.md** - Решение проблем с DNS и SSL (DuckDNS, Let's Encrypt)
-  **README.md** - Основная документация (этот файл)

### Быстрые ссылки:

**SSL и HTTPS:**
- [Создать самоподписанный SSL](SELF_SIGNED_SSL.md) - не требует домена, работает сразу
- [Настроить Let's Encrypt SSL](SSL_TROUBLESHOOTING.md) - бесплатный SSL для домена
- [Проблемы с DuckDNS](SSL_TROUBLESHOOTING.md#duckdns) - DNS не работает

**Управление:**
- Панель управления: `./manage.sh`
- Диагностика DNS/SSL: `./check-dns.sh`
- Установка: `./setup.sh`

---

**Важно**: Храните токены и пароли в безопасности. Не публикуйте файлы из `config/` в публичных репозиториях.
