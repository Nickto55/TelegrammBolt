#!/bin/bash
# TelegrammBolt - Минимальная установка для Debian/Ubuntu
# Этот скрипт использует только базовые пакеты

set -e

echo "🚀 TelegrammBolt - Минимальная установка"
echo "============================================================"

# Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get install -y python3 python3-pip python3-venv git curl wget build-essential

# Создание пользователя
echo "👤 Создание пользователя telegrambot..."
if ! id "telegrambot" &>/dev/null; then
    useradd --system --shell /bin/bash --home /opt/telegrambot --create-home telegrambot
fi

# Клонирование репозитория
echo "📥 Клонирование репозитория..."
if [ -d "/opt/telegrambot/.git" ]; then
    cd /opt/telegrambot
    sudo -u telegrambot git pull
else
    rm -rf /opt/telegrambot
    git clone https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot
fi

chown -R telegrambot:telegrambot /opt/telegrambot

# Установка Python окружения
echo "🐍 Установка Python окружения..."
cd /opt/telegrambot
sudo -u telegrambot python3 -m venv .venv
sudo -u telegrambot .venv/bin/pip install --upgrade pip
sudo -u telegrambot .venv/bin/pip install -r requirements.txt

# Создание конфигурации
echo "⚙️ Создание конфигурации..."
if [ ! -f "ven_bot.json" ]; then
    sudo -u telegrambot bash -c 'cat > ven_bot.json << EOF
{
  "BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
  "ADMIN_IDS": ["YOUR_TELEGRAM_ID_HERE"]
}
EOF'
fi

if [ ! -f "smtp_config.json" ]; then
    sudo -u telegrambot bash -c 'cat > smtp_config.json << EOF
{
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": 587,
  "SMTP_USER": "your_email@gmail.com",
  "SMTP_PASSWORD": "your_app_password",
  "FROM_NAME": "TelegrammBolt"
}
EOF'
fi

# Установка systemd службы
echo "🔧 Установка службы..."
cp /opt/telegrambot/telegrambot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable telegrambot.service

echo
echo "============================================================"
echo "✅ Установка завершена!"
echo
echo "📋 Следующие шаги:"
echo "1. Настройте конфигурацию:"
echo "   nano /opt/telegrambot/ven_bot.json"
echo
echo "2. Запустите бота:"
echo "   systemctl start telegrambot"
echo
echo "3. Проверьте статус:"
echo "   systemctl status telegrambot"
echo
echo "4. Просмотр логов:"
echo "   journalctl -u telegrambot -f"
echo "============================================================"
