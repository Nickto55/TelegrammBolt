#!/bin/bash
# Скрипт проверки установки TelegrammBolt

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔍 Проверка установки TelegrammBolt"
echo "===================================================="
echo

# Проверка пользователя
echo -n "Проверка пользователя telegrambot... "
if id "telegrambot" &>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Пользователь не найден"
    exit 1
fi

# Проверка директории
echo -n "Проверка директории /opt/telegrambot... "
if [ -d "/opt/telegrambot" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Директория не найдена"
    exit 1
fi

# Проверка виртуального окружения
echo -n "Проверка виртуального окружения... "
if [ -f "/opt/telegrambot/.venv/bin/python" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Виртуальное окружение не найдено"
    exit 1
fi

# Проверка основных файлов
echo -n "Проверка bot.py... "
if [ -f "/opt/telegrambot/bot.py" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Файл не найден"
    exit 1
fi

echo -n "Проверка config.py... "
if [ -f "/opt/telegrambot/config.py" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Файл не найден"
    exit 1
fi

echo -n "Проверка commands.py... "
if [ -f "/opt/telegrambot/commands.py" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Файл не найден"
    exit 1
fi

# Проверка конфигурации
echo -n "Проверка ven_bot.json... "
if [ -f "/opt/telegrambot/ven_bot.json" ]; then
    echo -e "${GREEN}✓${NC}"
    
    # Проверка содержимого
    if grep -q "YOUR_BOT_TOKEN_HERE" /opt/telegrambot/ven_bot.json; then
        echo -e "  ${YELLOW}⚠${NC} Токен бота не настроен!"
    fi
    
    if grep -q "YOUR_TELEGRAM_ID_HERE" /opt/telegrambot/ven_bot.json; then
        echo -e "  ${YELLOW}⚠${NC} ID администратора не настроен!"
    fi
else
    echo -e "${RED}✗${NC} Файл конфигурации не найден"
    exit 1
fi

# Проверка systemd службы
echo -n "Проверка systemd службы... "
if [ -f "/etc/systemd/system/telegrambot.service" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Служба не установлена"
    exit 1
fi

# Проверка статуса службы
echo -n "Проверка статуса службы... "
if systemctl is-enabled telegrambot.service &>/dev/null; then
    echo -e "${GREEN}✓${NC} (включена)"
else
    echo -e "${YELLOW}⚠${NC} Служба отключена"
fi

echo -n "Проверка активности службы... "
if systemctl is-active telegrambot.service &>/dev/null; then
    echo -e "${GREEN}✓${NC} (запущена)"
else
    echo -e "${YELLOW}⚠${NC} Служба остановлена"
fi

# Проверка Python зависимостей
echo -n "Проверка Python зависимостей... "
cd /opt/telegrambot
MISSING_DEPS=0

for package in telegram pandas openpyxl reportlab; do
    if ! sudo -u telegrambot .venv/bin/python -c "import $package" 2>/dev/null; then
        echo -e "${RED}✗${NC} Отсутствует пакет: $package"
        MISSING_DEPS=1
    fi
done

if [ $MISSING_DEPS -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
fi

# Проверка прав доступа
echo -n "Проверка прав доступа... "
OWNER=$(stat -c '%U' /opt/telegrambot)
if [ "$OWNER" = "telegrambot" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Неверный владелец: $OWNER"
fi

echo
echo "===================================================="
echo -e "${GREEN}✅ Проверка завершена!${NC}"
echo

# Дополнительная информация
echo "📊 Дополнительная информация:"
echo
echo "Версия Python:"
sudo -u telegrambot /opt/telegrambot/.venv/bin/python --version
echo

echo "Статус службы:"
systemctl status telegrambot.service --no-pager -l
echo

echo "Последние 10 строк логов:"
journalctl -u telegrambot -n 10 --no-pager
echo

echo "===================================================="
echo "Для просмотра логов в реальном времени:"
echo "  sudo journalctl -u telegrambot -f"
echo
echo "Для перезапуска службы:"
echo "  sudo systemctl restart telegrambot"
echo "===================================================="
