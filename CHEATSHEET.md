# 📋 TelegrammBolt - Шпаргалка команд

## 🚀 Быстрая установка

### Из ветки web (с веб-интерфейсом)
```bash
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/web/setup.sh | bash
```

### Из основной ветки (только бот)
```bash
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup.sh | bash
```

## 📦 Управление службами

### Docker (рекомендуется для контейнеров)
```bash
# Запуск бота в Docker
cd /opt/telegrambot
.venv/bin/python bot.py

# В фоне
nohup .venv/bin/python bot.py > bot.log 2>&1 &

# Остановка
pkill -f bot.py

# Проверка статуса
ps aux | grep bot.py

# Логи
tail -f bot.log
```

### Systemd
```bash
# Запуск
sudo systemctl start telegrambot
sudo systemctl start telegrambot-web

# Остановка
sudo systemctl stop telegrambot
sudo systemctl stop telegrambot-web

# Перезапуск
sudo systemctl restart telegrambot telegrambot-web

# Статус
sudo systemctl status telegrambot telegrambot-web

# Логи
sudo journalctl -u telegrambot -f
sudo journalctl -u telegrambot-web -f
```

### Docker
```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Логи
docker-compose logs -f

# Статус
docker-compose ps
```

## 🔗 Получение ссылки на веб-интерфейс

```bash
# Способ 1: Скрипт
bash /opt/telegrambot/show-web-url.sh

# Способ 2: API
curl http://localhost:5000/api/server-info

# Способ 3: Браузер
http://ваш-IP:5000/show-url
```

## 🔄 Обновление

### Из ветки web
```bash
cd /opt/telegrambot
sudo systemctl stop telegrambot telegrambot-web
sudo -u telegrambot git pull origin web
sudo -u telegrambot .venv/bin/pip install --upgrade -r requirements.txt
sudo systemctl start telegrambot telegrambot-web
```

### Из основной ветки
```bash
cd /opt/telegrambot
sudo systemctl stop telegrambot
sudo -u telegrambot git pull origin main
sudo -u telegrambot .venv/bin/pip install --upgrade -r requirements.txt
sudo systemctl start telegrambot
```

## 🔧 Настройка

### Редактирование конфигурации
```bash
# Токен бота
sudo nano /opt/telegrambot/ven_bot.json

# Email настройки
sudo nano /opt/telegrambot/smtp_config.json

# Веб-приложение
sudo nano /opt/telegrambot/web_app.py
```

### Проверка конфигурации
```bash
# Проверить токен
cat /opt/telegrambot/ven_bot.json | jq .

# Проверить права
ls -la /opt/telegrambot/

# Проверить зависимости
/opt/telegrambot/.venv/bin/pip list
```

## 🐛 Отладка

### ⚡ Быстрые решения

| Ошибка | Команда |
|--------|---------|
| `externally-managed-environment` | `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` |
| `systemd-analyze not found` | Это нормально для Docker, запускайте: `python bot.py` |
| `ImportError` | `./emergency-fix.sh` или `pip install --force-reinstall -r requirements.txt` |
| `Conflict: terminated` | `pkill -f bot.py && sleep 3 && python bot.py` |

### Проверка логов
```bash
# Бот
sudo journalctl -u telegrambot -n 50 --no-pager

# Веб-интерфейс
sudo journalctl -u telegrambot-web -n 50 --no-pager

# Nginx
sudo tail -f /var/log/nginx/error.log

# Docker
docker logs telegrambot --tail 50
```

### Типичные ошибки

**Ошибка импорта** → см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md#-importerror-cannot-import-name-show_pdf_export_menu)

**Конфликт бота** → см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md#-ошибка-подключения-к-telegram-api)

**Python 3.13** → см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md#-конфликт-версий-python)

### Проверка портов
```bash
# Проверить открытые порты
sudo netstat -tulpn | grep LISTEN

# Проверить 5000 (веб)
sudo netstat -tulpn | grep 5000

# Проверить процессы
ps aux | grep python
```

### Тестовый запуск
```bash
# Бот
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py

# Веб
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python web_app.py
```

## 🌐 Веб-интерфейс

### URL endpoints
```
/                    - Главная (редирект на /login)
/login              - Страница входа
/dashboard          - Панель управления
/dse                - Список ДСЕ
/reports            - Отчеты
/chat               - Чат
/show-url           - Информация о сервере
/api/server-info    - API информация о сервере
/api/dse            - API для ДСЕ
/api/export/excel   - Экспорт Excel
/api/export/pdf     - Экспорт PDF
```

### Тестирование API
```bash
# Информация о сервере
curl http://localhost:5000/api/server-info

# Список ДСЕ (требует авторизации)
curl -H "Cookie: session=..." http://localhost:5000/api/dse

# Экспорт Excel
curl -O http://localhost:5000/api/export/excel
```

## 🔐 Безопасность

### Права доступа
```bash
# Проверить владельца
ls -la /opt/telegrambot/

# Исправить права
sudo chown -R telegrambot:telegrambot /opt/telegrambot
sudo chmod 644 /opt/telegrambot/ven_bot.json
sudo chmod 644 /opt/telegrambot/smtp_config.json
```

### SSL сертификат
```bash
# Получить сертификат
sudo certbot --nginx -d bot.example.com

# Проверить срок действия
sudo certbot certificates

# Обновить сертификат
sudo certbot renew
```

### Firewall
```bash
# Открыть порты
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5000/tcp  # Только для разработки

# Проверить статус
sudo ufw status
```

## 📊 Мониторинг

### Использование ресурсов
```bash
# Процессы
htop

# Память
free -h

# Диск
df -h

# Процессы бота
ps aux | grep telegrambot
```

### Docker мониторинг
```bash
# Статистика контейнеров
docker stats

# Использование места
docker system df

# Логи определенного контейнера
docker logs telegrambot -f --since 10m
```

## 🔄 Переключение веток

### На ветку web
```bash
cd /opt/telegrambot
sudo systemctl stop telegrambot telegrambot-web
sudo -u telegrambot git fetch origin
sudo -u telegrambot git checkout web
sudo -u telegrambot git pull origin web
sudo -u telegrambot .venv/bin/pip install -r requirements.txt
sudo systemctl start telegrambot telegrambot-web
```

### На основную ветку
```bash
cd /opt/telegrambot
sudo systemctl stop telegrambot telegrambot-web
sudo -u telegrambot git checkout main
sudo -u telegrambot git pull origin main
sudo systemctl start telegrambot
```

## 📦 Бэкап

### Создание бэкапа
```bash
# Создать архив
sudo tar -czf telegrambot-backup-$(date +%Y%m%d).tar.gz \
  /opt/telegrambot/ven_bot.json \
  /opt/telegrambot/smtp_config.json \
  /opt/telegrambot/bot_data.json \
  /opt/telegrambot/users_data.json \
  /opt/telegrambot/RezultBot.xlsx \
  /opt/telegrambot/photos/

# Скопировать в безопасное место
scp telegrambot-backup-*.tar.gz user@backup-server:/backups/
```

### Восстановление
```bash
# Остановить службы
sudo systemctl stop telegrambot telegrambot-web

# Распаковать
sudo tar -xzf telegrambot-backup-*.tar.gz -C /

# Исправить права
sudo chown -R telegrambot:telegrambot /opt/telegrambot

# Запустить
sudo systemctl start telegrambot telegrambot-web
```

## 🎯 Быстрые действия

### Полная переустановка
```bash
# Удалить
sudo systemctl stop telegrambot telegrambot-web
sudo rm -rf /opt/telegrambot
sudo userdel telegrambot

# Установить заново
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/web/setup.sh | bash
```

### Очистка логов
```bash
# Системные логи
sudo journalctl --vacuum-time=7d

# Docker логи
docker system prune -a

# Логи приложения
rm -f /opt/telegrambot/logs/*.log
```

### Экспорт данных
```bash
# Excel
curl -O http://localhost:5000/api/export/excel

# Копировать все данные
cp /opt/telegrambot/*.json /backup/
cp /opt/telegrambot/*.xlsx /backup/
```

## 🆘 Аварийное восстановление

### Бот не запускается
```bash
# 1. Проверить логи
sudo journalctl -u telegrambot -n 50

# 2. Проверить конфигурацию
cat /opt/telegrambot/ven_bot.json

# 3. Проверить зависимости
/opt/telegrambot/.venv/bin/pip check

# 4. Тестовый запуск
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

### Веб-интерфейс недоступен
```bash
# 1. Проверить службу
sudo systemctl status telegrambot-web

# 2. Проверить порт
sudo netstat -tulpn | grep 5000

# 3. Проверить nginx
sudo nginx -t
sudo systemctl status nginx

# 4. Тестовый запуск
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python web_app.py
```

## 📚 Полезные ссылки

- **[README.md](README.md)** - Основная документация
- **[INSTALLATION.md](INSTALLATION.md)** - Полное руководство по установке
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Решение всех проблем

---

**Сохраните эту шпаргалку для быстрого доступа!** 📋
