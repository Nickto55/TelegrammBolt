#!/bin/bash

# Диагностика и исправление ошибки 502 Bad Gateway
# Для TelegrammBolt

echo "=========================================="
echo "TelegrammBolt - Исправление 502 Bad Gateway"
echo "=========================================="
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[INFO]${NC} 502 Bad Gateway означает:"
echo "  - Nginx работает и принимает запросы"
echo "  - НО не может подключиться к Flask (порт 5000)"
echo ""

# Проверка 1: Nginx работает?
echo -e "${YELLOW}[1/5]${NC} Проверка Nginx..."
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Nginx запущен"
else
    echo -e "  ${RED}✗${NC} Nginx не запущен"
    echo "  Запустите: sudo systemctl start nginx"
    exit 1
fi

# Проверка 2: Порт 5000 слушается?
echo -e "${YELLOW}[2/5]${NC} Проверка Flask (порт 5000)..."
if netstat -tuln 2>/dev/null | grep -q ':5000 ' || ss -tuln 2>/dev/null | grep -q ':5000 '; then
    echo -e "  ${GREEN}✓${NC} Порт 5000 слушается"
    
    # Показать какой процесс
    PROCESS=$(sudo lsof -i :5000 2>/dev/null | grep LISTEN | awk '{print $1}' | head -1)
    echo "  Процесс: $PROCESS"
else
    echo -e "  ${RED}✗${NC} Порт 5000 НЕ слушается"
    echo ""
    echo "  ПРОБЛЕМА: Flask не запущен!"
    echo ""
fi

# Проверка 3: Бот запущен?
echo -e "${YELLOW}[3/5]${NC} Проверка бота (bot.py)..."
if pgrep -f "python.*bot.py" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Бот запущен"
    ps aux | grep "[p]ython.*bot.py" | head -1 | awk '{print "  PID:", $2, "CPU:", $3"%", "MEM:", $4"%"}'
else
    echo -e "  ${RED}✗${NC} Бот НЕ запущен"
    echo ""
    echo "  ПРОБЛЕМА: bot.py не работает!"
    echo ""
fi

# Проверка 4: Flask отвечает?
echo -e "${YELLOW}[4/5]${NC} Проверка доступности Flask..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/login 2>/dev/null | grep -q "200\|302"; then
    echo -e "  ${GREEN}✓${NC} Flask отвечает на localhost:5000"
else
    echo -e "  ${RED}✗${NC} Flask НЕ отвечает"
    
    # Попробуем узнать почему
    if ! pgrep -f "python.*bot.py" > /dev/null; then
        echo "  Причина: bot.py не запущен"
    elif ! netstat -tuln 2>/dev/null | grep -q ':5000 '; then
        echo "  Причина: Flask не слушает порт 5000"
    else
        echo "  Причина: Flask зависает или ошибка"
    fi
fi

# Проверка 5: Логи Nginx
echo -e "${YELLOW}[5/5]${NC} Последние ошибки Nginx..."
if [ -f /var/log/nginx/telegrambot_error.log ]; then
    ERRORS=$(sudo tail -5 /var/log/nginx/telegrambot_error.log 2>/dev/null | grep -i "upstream\|connection refused\|timeout")
    if [ -n "$ERRORS" ]; then
        echo -e "  ${RED}✗${NC} Обнаружены ошибки:"
        echo "$ERRORS" | sed 's/^/    /'
    else
        echo -e "  ${GREEN}✓${NC} Ошибок upstream не найдено"
    fi
else
    echo "  Лог-файл не найден"
fi

echo ""
echo "=========================================="
echo "Диагноз"
echo "=========================================="
echo ""

# Определение проблемы
PROBLEM=""

if ! pgrep -f "python.*bot.py" > /dev/null; then
    PROBLEM="bot_not_running"
    echo -e "${RED}ПРОБЛЕМА:${NC} Бот (bot.py) не запущен"
    echo ""
    echo "Flask запускается внутри bot.py через threading."
    echo "Если бот не работает, Flask тоже не работает."
    echo ""
    echo -e "${GREEN}РЕШЕНИЕ:${NC}"
    echo "  cd /opt/telegrambot"
    echo "  python3 bot.py"
    echo ""
    echo "Или через systemd:"
    echo "  sudo systemctl start telegrambot"
    echo ""

elif ! netstat -tuln 2>/dev/null | grep -q ':5000 '; then
    PROBLEM="flask_not_listening"
    echo -e "${RED}ПРОБЛЕМА:${NC} Flask не слушает порт 5000"
    echo ""
    echo "Возможные причины:"
    echo "  1. web_enabled=false в ven_bot.json"
    echo "  2. Порт 5000 занят другим процессом"
    echo "  3. Ошибка при запуске Flask"
    echo ""
    echo -e "${GREEN}РЕШЕНИЕ:${NC}"
    echo ""
    echo "1. Проверьте ven_bot.json:"
    echo "   cat /opt/telegrambot/ven_bot.json"
    echo "   Убедитесь: \"web_enabled\": true"
    echo ""
    echo "2. Проверьте что порт свободен:"
    echo "   sudo lsof -i :5000"
    echo ""
    echo "3. Перезапустите бота:"
    echo "   sudo systemctl restart telegrambot"
    echo ""

elif ! curl -s -o /dev/null http://127.0.0.1:5000/login 2>/dev/null; then
    PROBLEM="flask_not_responding"
    echo -e "${RED}ПРОБЛЕМА:${NC} Flask не отвечает на запросы"
    echo ""
    echo "Порт слушается, но Flask не отвечает."
    echo ""
    echo -e "${GREEN}РЕШЕНИЕ:${NC}"
    echo "  1. Посмотрите логи бота:"
    echo "     tail -50 /opt/telegrambot/bot.log"
    echo ""
    echo "  2. Перезапустите бота:"
    echo "     sudo systemctl restart telegrambot"
    echo ""
    echo "  3. Запустите вручную для отладки:"
    echo "     cd /opt/telegrambot"
    echo "     python3 bot.py"
    echo ""

else
    PROBLEM="unknown"
    echo -e "${GREEN}ВСЁ РАБОТАЕТ!${NC}"
    echo ""
    echo "Flask доступен, но Nginx выдаёт 502?"
    echo ""
    echo "Возможные причины:"
    echo "  1. Firewall блокирует localhost"
    echo "  2. SELinux блокирует подключение"
    echo "  3. Неверная конфигурация Nginx"
    echo ""
    echo -e "${GREEN}РЕШЕНИЕ:${NC}"
    echo "  1. Проверьте конфиг Nginx:"
    echo "     sudo nginx -t"
    echo ""
    echo "  2. Перезапустите Nginx:"
    echo "     sudo systemctl restart nginx"
    echo ""
    echo "  3. Проверьте SELinux (если есть):"
    echo "     sudo setenforce 0"
    echo ""
fi

echo ""
echo "=========================================="
echo "Быстрое исправление"
echo "=========================================="
echo ""

if [ "$PROBLEM" = "bot_not_running" ]; then
    echo "Хотите запустить бота сейчас? (y/n)"
    read -r -n 1 REPLY
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Запуск бота..."
        cd /opt/telegrambot
        
        # Проверяем есть ли systemd service
        if [ -f /etc/systemd/system/telegrambot.service ]; then
            sudo systemctl start telegrambot
            sleep 3
            if systemctl is-active --quiet telegrambot; then
                echo -e "${GREEN}✓ Бот запущен через systemd${NC}"
            else
                echo -e "${RED}✗ Не удалось запустить через systemd${NC}"
                echo "Запускаем вручную..."
                nohup python3 bot.py > bot.log 2>&1 &
                sleep 2
                echo -e "${GREEN}✓ Бот запущен в фоне${NC}"
            fi
        else
            echo "Запускаем бота в фоне..."
            nohup python3 bot.py > bot.log 2>&1 &
            sleep 2
            
            if pgrep -f "python.*bot.py" > /dev/null; then
                echo -e "${GREEN}✓ Бот запущен${NC}"
                echo "  PID: $(pgrep -f "python.*bot.py")"
                echo "  Логи: tail -f /opt/telegrambot/bot.log"
            else
                echo -e "${RED}✗ Не удалось запустить бота${NC}"
                echo "Проверьте логи: cat /opt/telegrambot/bot.log"
            fi
        fi
        
        # Проверка Flask
        echo ""
        echo "Ожидание запуска Flask (5 секунд)..."
        sleep 5
        
        if curl -s -o /dev/null http://127.0.0.1:5000/login 2>/dev/null; then
            echo -e "${GREEN}✓ Flask работает!${NC}"
            echo ""
            echo "Проверьте сайт в браузере:"
            echo "  https://$(curl -s ifconfig.me 2>/dev/null)/"
        else
            echo -e "${RED}✗ Flask всё ещё не отвечает${NC}"
            echo "Проверьте логи:"
            echo "  tail -50 /opt/telegrambot/bot.log"
        fi
    fi
fi

echo ""
echo "Готово!"
