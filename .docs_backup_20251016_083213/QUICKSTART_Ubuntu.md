# TelegrammBolt - Быстрый старт для Ubuntu

## Автоматическая установка

```bash
# Скачиваем и запускаем установочный скрипт
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/setup.sh | bash

# Настраиваем конфигурацию
sudo nano /opt/telegrambot/ven_bot.json

# Запускаем бота
sudo systemctl start telegrambot
sudo systemctl enable telegrambot

# Проверяем статус
sudo systemctl status telegrambot
```

## Ручная установка

```bash
# 1. Клонируем репозиторий
git clone https://github.com/Nickto55/TelegrammBolt.git
cd TelegrammBolt

# 2. Создаем виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# 3. Устанавливаем зависимости
pip install -r requirements.txt

# 4. Настраиваем конфигурацию
cp ven_bot.json.example ven_bot.json
nano ven_bot.json

# 5. Делаем скрипт исполняемым и запускаем
chmod +x start_bot.sh
./start_bot.sh
```

## Управление службой

```bash
# Запуск/остановка/перезапуск
sudo systemctl start telegrambot
sudo systemctl stop telegrambot
sudo systemctl restart telegrambot

# Просмотр логов
sudo journalctl -u telegrambot -f

# Статус службы
sudo systemctl status telegrambot
```

Подробная документация: [README_Ubuntu.md](README_Ubuntu.md)