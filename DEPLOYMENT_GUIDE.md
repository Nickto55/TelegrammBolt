# 🚀 Полное руководство по развертыванию TelegrammBolt на Ubuntu

## ✅ Предварительная проверка

Убедитесь, что ваш проект готов к развертыванию:

### Файлы в репозитории должны включать:
- ✅ `bot.py` - основной файл бота
- ✅ `requirements.txt` - все Python зависимости
- ✅ `setup.sh` - автоматический установочный скрипт 
- ✅ `start_bot.sh` - скрипт запуска для Linux
- ✅ `telegrambot.service` - файл systemd службы
- ✅ `*.json.example` - шаблоны конфигурации
- ✅ `.gitignore` - исключает конфиденциальные файлы
- ✅ `README_Ubuntu.md` - подробная документация

### Файлы, которые НЕ должны попасть в репозиторий:
- ❌ `ven_bot.json` (содержит токен бота)
- ❌ `smtp_config.json` (содержит пароли)
- ❌ `*.json` с реальными данными пользователей
- ❌ Папка `.venv/`
- ❌ Файлы `__pycache__/`

---

## 🔧 Пошаговая инструкция развертывания

### Шаг 1: Подготовка GitHub репозитория

1. **Убедитесь, что все изменения зафиксированы:**
   ```bash
   git status
   git add .
   git commit -m "Подготовка к развертыванию на Ubuntu"
   git push origin main
   ```

### Шаг 2: Развертывание на Ubuntu сервере

#### Метод А: Автоматическая установка (рекомендуется)

```bash
# Подключитесь к серверу Ubuntu
ssh user@your-server-ip

# Запустите автоматическую установку
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup.sh | bash
```

#### Метод Б: Ручная установка

```bash
# 1. Подключитесь к серверу
ssh user@your-server-ip

# 2. Обновите систему
sudo apt update && sudo apt upgrade -y

# 3. Установите необходимые пакеты
sudo apt install -y python3 python3-pip python3-venv git curl

# 4. Создайте пользователя для бота
sudo useradd --system --shell /bin/bash --home /opt/telegrambot --create-home telegrambot

# 5. Клонируйте репозиторий
sudo git clone https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot
sudo chown -R telegrambot:telegrambot /opt/telegrambot

# 6. Настройте Python окружение
cd /opt/telegrambot
sudo -u telegrambot python3 -m venv .venv
sudo -u telegrambot .venv/bin/pip install -r requirements.txt

# 7. Сделайте скрипты исполняемыми
sudo chmod +x start_bot.sh setup.sh
```

### Шаг 3: Настройка конфигурации

```bash
# 1. Создайте файл конфигурации бота
sudo cp /opt/telegrambot/ven_bot.json.example /opt/telegrambot/ven_bot.json

# 2. Отредактируйте конфигурацию
sudo nano /opt/telegrambot/ven_bot.json
```

Замените содержимое файла:
```json
{
  "BOT_TOKEN": "ВАШ_ТОКЕН_БОТА_ОТ_BOTFATHER",
  "ADMIN_IDS": ["ВАШ_TELEGRAM_ID"]
}
```

### Шаг 4: Настройка systemd службы

```bash
# 1. Скопируйте файл службы
sudo cp /opt/telegrambot/telegrambot.service /etc/systemd/system/

# 2. Перезагрузите systemd
sudo systemctl daemon-reload

# 3. Включите автозапуск службы
sudo systemctl enable telegrambot

# 4. Запустите службу
sudo systemctl start telegrambot
```

### Шаг 5: Проверка работы

```bash
# Проверьте статус службы
sudo systemctl status telegrambot

# Просмотрите логи в реальном времени
sudo journalctl -u telegrambot -f

# Проверьте, что бот отвечает в Telegram
# Отправьте команду /start вашему боту
```

---

## 🔍 Диагностика проблем

### Частые проблемы и решения:

1. **Бот не отвечает:**
   ```bash
   sudo journalctl -u telegrambot -n 50
   # Проверьте токен в ven_bot.json
   ```

2. **Ошибка импорта модулей:**
   ```bash
   sudo -u telegrambot /opt/telegrambot/.venv/bin/pip install -r /opt/telegrambot/requirements.txt
   ```

3. **Проблемы с правами доступа:**
   ```bash
   sudo chown -R telegrambot:telegrambot /opt/telegrambot
   sudo chmod +x /opt/telegrambot/start_bot.sh
   ```

4. **Служба не запускается:**
   ```bash
   # Проверьте синтаксис файла службы
   sudo systemd-analyze verify /etc/systemd/system/telegrambot.service
   
   # Перезагрузите конфигурацию
   sudo systemctl daemon-reload
   sudo systemctl restart telegrambot
   ```

---

## 🔧 Управление ботом

### Основные команды:

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

# Ручной запуск (для отладки)
cd /opt/telegrambot
sudo -u telegrambot ./start_bot.sh
```

### Обновление бота:

```bash
# 1. Остановите службу
sudo systemctl stop telegrambot

# 2. Обновите код
cd /opt/telegrambot
sudo -u telegrambot git pull

# 3. Обновите зависимости (если изменились)
sudo -u telegrambot .venv/bin/pip install -r requirements.txt

# 4. Запустите службу
sudo systemctl start telegrambot
```

---

## 🔒 Безопасность

### Рекомендации:

1. **Регулярно обновляйте систему:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Настройте firewall:**
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 443  # если используете webhook
   ```

3. **Создайте резервные копии:**
   ```bash
   sudo tar -czf telegrambot-backup-$(date +%Y%m%d).tar.gz \
       -C /opt/telegrambot \
       ven_bot.json smtp_config.json *.json photos/
   ```

4. **Мониторинг логов:**
   ```bash
   # Настройте автоматические уведомления о сбоях
   sudo systemctl edit telegrambot.service
   ```

---

## 📊 Мониторинг

### Проверка статуса:

```bash
# Статус службы
systemctl is-active telegrambot

# Время последнего запуска
systemctl show telegrambot --property=ActiveEnterTimestamp

# Использование ресурсов
sudo systemctl status telegrambot

# Размер логов
sudo journalctl --disk-usage
sudo journalctl -u telegrambot --vacuum-time=7d  # очистка старых логов
```

---

## 📋 Чек-лист успешного развертывания

- [ ] Репозиторий содержит все необходимые файлы
- [ ] `.gitignore` исключает конфиденциальные данные
- [ ] Токен бота получен от @BotFather
- [ ] Telegram ID получен от @userinfobot
- [ ] Ubuntu сервер имеет доступ к интернету
- [ ] Python 3.8+ установлен на сервере
- [ ] Служба telegrambot запущена и активна
- [ ] Бот отвечает на команду /start в Telegram
- [ ] Логи не содержат ошибок
- [ ] Автозапуск службы включен

---

## ✅ После успешного развертывания

Ваш бот теперь:
- ✅ Работает как системная служба
- ✅ Автоматически запускается при перезагрузке
- ✅ Автоматически перезапускается при сбоях
- ✅ Ведет подробные логи
- ✅ Изолирован для безопасности

**Готово! 🎉 Ваш TelegrammBolt успешно развернут на Ubuntu!**