#!/bin/bash
# Скрипт для показа ссылки на веб-интерфейс
# Использование: ./show-web-url.sh

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     TelegrammBolt Web Interface URL            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Определение окружения
if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    ENVIRONMENT="Docker"
else
    ENVIRONMENT="Native"
fi

echo -e "${YELLOW}Environment:${NC} $ENVIRONMENT"
echo ""

# Функция получения IP
get_public_ip() {
    curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo ""
}

get_local_ip() {
    hostname -I 2>/dev/null | awk '{print $1}' || ip route get 1 2>/dev/null | awk '{print $7}' || echo "localhost"
}

# Получение IP адресов
PUBLIC_IP=$(get_public_ip)
LOCAL_IP=$(get_local_ip)

# Определение порта
if [ -f /.dockerenv ]; then
    # В Docker - используем внешний порт из docker-compose или 5000
    PORT=${WEB_PORT:-5000}
else
    # Нативная установка
    PORT=5000
fi

# Проверка доступности веб-интерфейса
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    STATUS="${GREEN}✅ Online${NC}"
else
    STATUS="${YELLOW}⚠️  Not responding${NC}"
fi

echo -e "${CYAN}Status:${NC} $STATUS"
echo ""
echo -e "${CYAN}🌐 Access URLs:${NC}"
echo ""

# Вывод ссылок
if [ "$ENVIRONMENT" = "Docker" ]; then
    echo -e "  ${GREEN}➜${NC} Container: http://localhost:${PORT}"
    
    if [ ! -z "$PUBLIC_IP" ] && [ "$PUBLIC_IP" != "$LOCAL_IP" ]; then
        echo -e "  ${GREEN}➜${NC} Public:    http://${PUBLIC_IP}:${PORT}"
    fi
    
    if [ "$LOCAL_IP" != "localhost" ]; then
        echo -e "  ${GREEN}➜${NC} Local:     http://${LOCAL_IP}:${PORT}"
    fi
else
    # Нативная установка
    echo -e "  ${GREEN}➜${NC} Local:     http://localhost:${PORT}"
    
    if [ ! -z "$PUBLIC_IP" ] && [ "$PUBLIC_IP" != "$LOCAL_IP" ]; then
        echo -e "  ${GREEN}➜${NC} Public:    http://${PUBLIC_IP}:${PORT}"
    fi
    
    if [ "$LOCAL_IP" != "localhost" ]; then
        echo -e "  ${GREEN}➜${NC} Network:   http://${LOCAL_IP}:${PORT}"
    fi
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Основная ссылка для копирования
MAIN_URL="http://${PUBLIC_IP:-$LOCAL_IP}:${PORT}"

echo -e "${BLUE}📋 Copy this URL:${NC}"
echo ""
echo -e "   ${GREEN}${MAIN_URL}${NC}"
echo ""

# QR код (если установлен qrencode)
if command -v qrencode &> /dev/null; then
    echo -e "${CYAN}📱 QR Code:${NC}"
    echo ""
    qrencode -t ANSI "$MAIN_URL"
    echo ""
fi

# Дополнительная информация
echo -e "${YELLOW}💡 Tips:${NC}"
echo ""
if [ "$ENVIRONMENT" = "Docker" ]; then
    echo "  • Use public IP for external access"
    echo "  • Check Docker port mapping: docker ps"
    echo "  • View logs: docker logs telegrambot"
else
    echo "  • Use public IP for external access"
    echo "  • Check service: systemctl status telegrambot-web"
    echo "  • View logs: journalctl -u telegrambot-web -f"
fi
echo ""

# Информация о Telegram Login
echo -e "${CYAN}🔐 Telegram Login Setup:${NC}"
echo ""
echo "  1. Open @BotFather in Telegram"
echo "  2. Send: /mybots → [Your Bot] → Bot Settings → Domain"
echo "  3. Set domain: ${PUBLIC_IP:-$LOCAL_IP}"
echo "     (or your actual domain if you have one)"
echo ""

echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
