#!/bin/bash

# =============================================================================
# Скрипт установки Telegram Bot для Debian/Ubuntu
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Установка Telegram Bot${NC}"
echo -e "${GREEN}========================================${NC}"

# Проверка прав sudo
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}Внимание: Скрипт запущен от root. Рекомендуется запускать от обычного пользователя с sudo.${NC}"
fi

# Проверка ОС
if [ ! -f /etc/debian_version ] && [ ! -f /etc/lsb-release ]; then
    echo -e "${RED}Ошибка: Этот скрипт предназначен только для Debian/Ubuntu${NC}"
    exit 1
fi

echo -e "${GREEN}[1/7] Обновление системы...${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "${GREEN}[2/7] Установка зависимостей...${NC}"
sudo apt install -y python3 python3-pip python3-venv git curl wget build-essential \
    libssl-dev libffi-dev python3-dev libzbar0 zbar-tools

echo -e "${GREEN}[3/7] Создание виртуального окружения Python...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}Виртуальное окружение создано${NC}"
else
    echo -e "${YELLOW}Виртуальное окружение уже существует, пропускаем...${NC}"
fi

echo -e "${GREEN}[4/7] Установка Python зависимостей...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}[5/7] Создание необходимых директорий...${NC}"
mkdir -p data/photos
mkdir -p config
echo -e "${GREEN}Директории созданы${NC}"

echo -e "${GREEN}[6/7] Настройка конфигурации...${NC}"

# Настройка Telegram Bot
CONFIG_FILE="config/ven_bot.json"
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}Файл $CONFIG_FILE уже существует. Пропускаем...${NC}"
else
    echo -e "${YELLOW}Настройка Telegram Bot конфигурации${NC}"
    read -p "Введите BOT_TOKEN (от @BotFather): " BOT_TOKEN
    read -p "Введите ваш Telegram ID (admin): " ADMIN_ID
    read -p "Введите имя бота (username без @): " BOT_USERNAME
    
    cat > "$CONFIG_FILE" <<EOF
{
  "BOT_TOKEN": "$BOT_TOKEN",
  "ADMIN_IDS": ["$ADMIN_ID"],
  "BOT_USERNAME": "$BOT_USERNAME"
}
EOF
    echo -e "${GREEN}Конфигурация бота сохранена в $CONFIG_FILE${NC}"
fi

# Настройка SMTP (опционально)
SMTP_CONFIG="config/smtp_config.json"
if [ -f "$SMTP_CONFIG" ]; then
    echo -e "${YELLOW}Файл $SMTP_CONFIG уже существует. Пропускаем...${NC}"
else
    read -p "Хотите настроить SMTP для отправки email? (y/n): " SETUP_SMTP
    if [[ $SETUP_SMTP =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Настройка SMTP${NC}"
        read -p "SMTP сервер (например smtp.gmail.com): " SMTP_SERVER
        read -p "SMTP порт (обычно 587): " SMTP_PORT
        read -p "Email для отправки: " SMTP_USER
        read -s -p "Пароль приложения: " SMTP_PASSWORD
        echo
        read -p "Имя отправителя: " FROM_NAME
        
        cat > "$SMTP_CONFIG" <<EOF
{
  "SMTP_SERVER": "$SMTP_SERVER",
  "SMTP_PORT": $SMTP_PORT,
  "SMTP_USER": "$SMTP_USER",
  "SMTP_PASSWORD": "$SMTP_PASSWORD",
  "FROM_NAME": "$FROM_NAME"
}
EOF
        echo -e "${GREEN}SMTP конфигурация сохранена в $SMTP_CONFIG${NC}"
    else
        echo -e "${YELLOW}SMTP настройка пропущена${NC}"
    fi
fi

echo -e "${GREEN}[7/7] Создание скриптов запуска...${NC}"

# Скрипт запуска бота
cat > start_bot.sh <<'EOF'
#!/bin/bash
source venv/bin/activate
python3 bot/bot.py
EOF
chmod +x start_bot.sh

# Скрипт запуска веб-интерфейса
cat > start_web.sh <<'EOF'
#!/bin/bash
source venv/bin/activate
python3 web/web_app.py
EOF
chmod +x start_web.sh

# Универсальный скрипт запуска
cat > start.sh <<'EOF'
#!/bin/bash

echo "Выберите что запустить:"
echo "1) Telegram Bot"
echo "2) Web интерфейс"
echo "3) Оба (в разных терминалах)"
read -p "Ваш выбор (1/2/3): " choice

case $choice in
    1)
        ./start_bot.sh
        ;;
    2)
        ./start_web.sh
        ;;
    3)
        echo "Запускаю бота..."
        gnome-terminal -- bash -c "./start_bot.sh; exec bash" 2>/dev/null || \
        xterm -e "./start_bot.sh" 2>/dev/null || \
        konsole -e "./start_bot.sh" 2>/dev/null || \
        (./start_bot.sh &)
        
        sleep 2
        echo "Запускаю веб-интерфейс..."
        gnome-terminal -- bash -c "./start_web.sh; exec bash" 2>/dev/null || \
        xterm -e "./start_web.sh" 2>/dev/null || \
        konsole -e "./start_web.sh" 2>/dev/null || \
        (./start_web.sh &)
        
        echo "Оба сервиса запущены"
        ;;
    *)
        echo "Неверный выбор"
        exit 1
        ;;
esac
EOF
chmod +x start.sh

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Установка завершена успешно!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Для запуска используйте:${NC}"
echo -e "  ${GREEN}./start.sh${NC}        - интерактивный выбор"
echo -e "  ${GREEN}./start_bot.sh${NC}    - только Telegram бот"
echo -e "  ${GREEN}./start_web.sh${NC}    - только Web интерфейс"
echo ""
echo -e "${YELLOW}Конфигурационные файлы:${NC}"
echo -e "  ${GREEN}config/ven_bot.json${NC}     - настройки бота"
echo -e "  ${GREEN}config/smtp_config.json${NC} - настройки email (опционально)"
echo ""
echo -e "${GREEN}Готово! Можете запускать проект.${NC}"
