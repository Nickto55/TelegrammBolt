# Установка TelegrammBolt

## Быстрая установка (Ubuntu/Debian)

### Шаг 1: Скачайте установщик

```bash
wget https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup.sh
chmod +x setup.sh
```

### Шаг 2: Запустите установку

```bash
sudo ./setup.sh
```

Установщик проведет вас через все настройки:

1. **Telegram Bot**
   - Токен от @BotFather
   - ID администраторов

2. **Email (опционально)**
   - SMTP сервер
   - Email и пароль

3. **Веб-интерфейс**
   - Порт (по умолчанию 5000)
   - HTTPS (Let's Encrypt / Самоподписанный / Без SSL)

---

## Что проверяет установщик

✅ Операционная система (Ubuntu/Debian)  
✅ Версия Python (требуется 3.9+)  
✅ Свободное место (минимум 2GB)  
✅ Оперативная память (рекомендуется 512MB+)  
✅ Подключение к интернету  
✅ Доступность GitHub  
✅ Валидность токена бота через Telegram API  
✅ DNS настройки (для Let's Encrypt)  

---

## Защита от ошибок

### 1. Проверка токена бота
- Формат токена
- Длина (минимум 30 символов)
- Валидация через Telegram API
- Получение имени бота

### 2. Проверка ID администраторов
- Формат (только цифры)
- Длина ID (5-15 цифр)
- Предупреждение о подозрительных ID

### 3. Проверка SMTP
- Формат сервера (domain.com)
- Валидация порта (1-65535)
- Формат email адреса
- Минимальная длина пароля
- Предупреждение для Gmail (пароль приложения)

### 4. Проверка веб-настроек
- Занятость порта
- Формат доменного имени
- DNS проверка для Let's Encrypt
- Проверка сертификатов

### 5. Установка зависимостей
- Поштучная установка пакетов при ошибках
- Проверка критичных пакетов
- Резервное копирование при обновлении
- Валидация JSON файлов

---

## Что устанавливает скрипт

### Системные пакеты
- python3, python3-pip, python3-venv
- git, curl, wget, unzip
- build-essential
- nginx
- certbot, python3-certbot-nginx
- jq, openssl, ca-certificates

### Python окружение
- Виртуальное окружение `.venv`
- Все зависимости из `requirements.txt`
- python-telegram-bot, Flask, requests и др.

### Структура проекта
```
/opt/telegrambot/
├── bot/              # Telegram бот
├── web/              # Веб-интерфейс
├── config/           # Конфигурация
│   ├── ven_bot.json  # Настройки бота
│   └── smtp_config.json
├── data/             # Данные
├── photos/           # Загруженные фото
├── logs/             # Логи
└── .venv/            # Python окружение
```

### Systemd служба
- Автозапуск при загрузке
- Автоматический перезапуск при сбоях
- Логирование через journalctl
- Ограничения безопасности

### Nginx (если включен веб)
- Reverse proxy на Flask
- WebSocket поддержка
- Логирование
- Таймауты и лимиты

### HTTPS (опционально)
- **Let's Encrypt**: Бесплатный SSL, автообновление
- **Самоподписанный**: SSL без домена
- **Без HTTPS**: HTTP (не рекомендуется)

---

## Управление ботом

### Запуск/остановка
```bash
sudo systemctl start telegrambot    # Запустить
sudo systemctl stop telegrambot     # Остановить
sudo systemctl restart telegrambot  # Перезапустить
sudo systemctl status telegrambot   # Статус
```

### Логи
```bash
sudo journalctl -u telegrambot -f        # Логи в реальном времени
sudo journalctl -u telegrambot -n 100    # Последние 100 строк
sudo journalctl -u telegrambot --since "1 hour ago"
```

### Автозапуск
```bash
sudo systemctl enable telegrambot   # Включить
sudo systemctl disable telegrambot  # Выключить
```

---

## Обновление бота

```bash
cd /opt/telegrambot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegrambot
```

---

## Настройка HTTPS

### Let's Encrypt (с доменом)

1. Убедитесь, что домен указывает на ваш сервер
2. Запустите установщик и выберите вариант 1
3. Или вручную:
   ```bash
   sudo certbot --nginx -d ваш-домен.com
   ```

Автообновление сертификата:
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Самоподписанный сертификат

Уже создан установщиком в `/etc/nginx/ssl/`

Для обхода предупреждения браузера:
- Chrome: введите `thisisunsafe`
- Firefox: "Дополнительно" → "Принять риск"

---

## Диагностика

### Проверка системы
```bash
cd /opt/telegrambot
.venv/bin/python utils.py check
```

### Список пользователей
```bash
.venv/bin/python utils.py users
```

### Поиск заявки
```bash
.venv/bin/python utils.py find <ID>
```

### Проверка конфигурации
```bash
cat /opt/telegrambot/config/ven_bot.json
```

### Проверка Nginx
```bash
sudo nginx -t
sudo systemctl status nginx
```

---

## Решение проблем

### Бот не запускается

1. Проверьте логи:
   ```bash
   sudo journalctl -u telegrambot -n 50
   ```

2. Проверьте токен:
   ```bash
   cat /opt/telegrambot/config/ven_bot.json
   ```

3. Запустите вручную для отладки:
   ```bash
   cd /opt/telegrambot
   sudo -u telegrambot .venv/bin/python bot/bot.py
   ```

### Веб-интерфейс недоступен

1. Проверьте Nginx:
   ```bash
   sudo systemctl status nginx
   sudo nginx -t
   ```

2. Проверьте логи Nginx:
   ```bash
   sudo tail -f /var/log/nginx/telegrambot_error.log
   ```

3. Проверьте что Flask запущен:
   ```bash
   ss -tlnp | grep 5000
   ```

### Let's Encrypt не работает

1. Проверьте DNS:
   ```bash
   dig ваш-домен.com
   ```

2. Проверьте порт 80:
   ```bash
   sudo ss -tlnp | grep :80
   ```

3. Проверьте файрвол:
   ```bash
   sudo ufw status
   sudo ufw allow 80
   sudo ufw allow 443
   ```

### ModuleNotFoundError

1. Проверьте `__init__.py`:
   ```bash
   ls -la /opt/telegrambot/*/`__init__.py`
   ```

2. Пересоздайте, если отсутствуют:
   ```bash
   touch /opt/telegrambot/bot/__init__.py
   touch /opt/telegrambot/web/__init__.py
   touch /opt/telegrambot/config/__init__.py
   ```

---

## Безопасность

### Защита конфигурации
- `ven_bot.json` имеет права 600 (только владелец)
- `smtp_config.json` имеет права 600
- Бот работает от отдельного пользователя

### Обновление пароля веб-интерфейса
1. Откройте веб-интерфейс
2. Зайдите в настройки
3. Смените пароль

### Файрвол
```bash
sudo ufw enable
sudo ufw allow 22         # SSH
sudo ufw allow 80         # HTTP
sudo ufw allow 443        # HTTPS
sudo ufw status
```

---

## Поддержка

- **GitHub Issues**: https://github.com/Nickto55/TelegrammBolt/issues
- **Документация**: README.md, UTILS.md, SECURITY.md
- **Примеры**: docs/

---

## Требования

- **ОС**: Ubuntu 20.04+ / Debian 10+
- **Python**: 3.9+
- **RAM**: Минимум 512MB (рекомендуется 1GB+)
- **Диск**: Минимум 2GB свободного места
- **Интернет**: Постоянное подключение
- **Домен**: Опционально (для Let's Encrypt)

---

## Лицензия

MIT License - см. LICENSE файл
