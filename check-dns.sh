#!/bin/bash

# =============================================================================
# Скрипт диагностики и исправления SSL/DNS проблем
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}          ${GREEN}Диагностика SSL/DNS проблем${NC}                   ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Загрузка конфигурации
if [ -f config/domain.conf ]; then
    source config/domain.conf
    echo -e "${GREEN}Домен из конфигурации: $DOMAIN${NC}"
else
    read -p "Введите ваш домен: " DOMAIN
fi

echo ""
echo -e "${YELLOW}[1/6] Проверка IP сервера...${NC}"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || wget -qO- ifconfig.me 2>/dev/null)
echo -e "${GREEN}IP вашего сервера: $SERVER_IP${NC}"

echo ""
echo -e "${YELLOW}[2/6] Проверка DNS резолвинга...${NC}"
echo -e "Проверка локально:"
DOMAIN_IP=$(dig +short $DOMAIN 2>/dev/null | tail -n1)
if [ -n "$DOMAIN_IP" ]; then
    echo -e "${GREEN}✓ Локальный DNS: $DOMAIN -> $DOMAIN_IP${NC}"
else
    echo -e "${RED}✗ Локальный DNS не резолвится${NC}"
fi

echo ""
echo -e "Проверка через Google DNS (8.8.8.8):"
DOMAIN_IP_GOOGLE=$(dig @8.8.8.8 +short $DOMAIN 2>/dev/null | tail -n1)
if [ -n "$DOMAIN_IP_GOOGLE" ]; then
    echo -e "${GREEN}✓ Google DNS: $DOMAIN -> $DOMAIN_IP_GOOGLE${NC}"
else
    echo -e "${RED}✗ Google DNS не резолвится${NC}"
fi

echo ""
echo -e "Проверка через Cloudflare DNS (1.1.1.1):"
DOMAIN_IP_CF=$(dig @1.1.1.1 +short $DOMAIN 2>/dev/null | tail -n1)
if [ -n "$DOMAIN_IP_CF" ]; then
    echo -e "${GREEN}✓ Cloudflare DNS: $DOMAIN -> $DOMAIN_IP_CF${NC}"
else
    echo -e "${RED}✗ Cloudflare DNS не резолвится${NC}"
fi

echo ""
echo -e "${YELLOW}[3/6] Сравнение IP адресов...${NC}"
if [ "$SERVER_IP" = "$DOMAIN_IP" ] || [ "$SERVER_IP" = "$DOMAIN_IP_GOOGLE" ] || [ "$SERVER_IP" = "$DOMAIN_IP_CF" ]; then
    echo -e "${GREEN}✓ IP совпадают! DNS настроен правильно${NC}"
    DNS_OK=true
else
    echo -e "${RED}✗ IP не совпадают!${NC}"
    echo -e "${YELLOW}Сервер: $SERVER_IP${NC}"
    echo -e "${YELLOW}Домен:  ${DOMAIN_IP:-не найден}${NC}"
    DNS_OK=false
fi

echo ""
echo -e "${YELLOW}[4/6] Проверка портов...${NC}"
if sudo ss -tulpn | grep -q ':80 '; then
    echo -e "${GREEN}✓ Порт 80 открыт${NC}"
else
    echo -e "${RED}✗ Порт 80 не слушается${NC}"
fi

if sudo ss -tulpn | grep -q ':443 '; then
    echo -e "${GREEN}✓ Порт 443 открыт${NC}"
else
    echo -e "${YELLOW}⚠ Порт 443 не слушается (нормально если SSL не настроен)${NC}"
fi

echo ""
echo -e "${YELLOW}[5/6] Проверка firewall...${NC}"
if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "80.*ALLOW"; then
        echo -e "${GREEN}✓ UFW: порт 80 открыт${NC}"
    else
        echo -e "${YELLOW}⚠ UFW: порт 80 не открыт${NC}"
        read -p "Открыть порт 80? (y/n): " OPEN_80
        if [[ $OPEN_80 =~ ^[Yy]$ ]]; then
            sudo ufw allow 80/tcp
            echo -e "${GREEN}✓ Порт 80 открыт${NC}"
        fi
    fi
    
    if sudo ufw status | grep -q "443.*ALLOW"; then
        echo -e "${GREEN}✓ UFW: порт 443 открыт${NC}"
    else
        echo -e "${YELLOW}⚠ UFW: порт 443 не открыт${NC}"
        read -p "Открыть порт 443? (y/n): " OPEN_443
        if [[ $OPEN_443 =~ ^[Yy]$ ]]; then
            sudo ufw allow 443/tcp
            echo -e "${GREEN}✓ Порт 443 открыт${NC}"
        fi
    fi
else
    echo -e "${BLUE}ℹ UFW не установлен${NC}"
fi

echo ""
echo -e "${YELLOW}[6/6] Проверка доступности извне...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "000" ]; then
    echo -e "${GREEN}✓ HTTP доступен (код: $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ HTTP недоступен${NC}"
fi

HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTPS_CODE" != "000" ]; then
    echo -e "${GREEN}✓ HTTPS доступен (код: $HTTPS_CODE)${NC}"
else
    echo -e "${YELLOW}⚠ HTTPS недоступен (нормально если SSL не настроен)${NC}"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                  ${GREEN}Результаты${NC}                             ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$DNS_OK" = true ]; then
    echo -e "${GREEN}✓ DNS настроен правильно${NC}"
    echo ""
    echo "Теперь вы можете получить SSL сертификат:"
    echo -e "${CYAN}sudo certbot --nginx -d $DOMAIN${NC}"
    echo ""
    echo "Или через панель управления:"
    echo -e "${CYAN}./manage.sh${NC} -> выберите '7. Настройка SSL/Домена'"
else
    echo -e "${RED}✗ Проблемы с DNS${NC}"
    echo ""
    echo -e "${YELLOW}Рекомендации:${NC}"
    echo ""
    
    if [[ $DOMAIN == *.duckdns.org ]]; then
        echo "1. Обновите IP в DuckDNS:"
        DUCKDNS_SUBDOMAIN=$(echo $DOMAIN | sed 's/.duckdns.org//')
        echo -e "   ${CYAN}https://www.duckdns.org${NC}"
        echo -e "   Или через API: ${CYAN}curl \"https://www.duckdns.org/update?domains=$DUCKDNS_SUBDOMAIN&token=YOUR_TOKEN&ip=\"${NC}"
        echo ""
        echo "2. Создайте скрипт автообновления IP:"
        echo -e "   ${CYAN}./manage.sh${NC} -> '7. Настройка SSL/Домена' -> настроить DuckDNS"
        echo ""
    fi
    
    echo "3. Подождите распространения DNS (до 24 часов)"
    echo -e "   Мониторинг: ${CYAN}watch -n 10 'dig +short $DOMAIN'${NC}"
    echo ""
    echo "4. Проверьте DNS через онлайн инструменты:"
    echo -e "   ${CYAN}https://dnschecker.org${NC}"
    echo ""
    echo "5. Если DNS не работает долго, смените провайдера:"
    echo "   - No-IP (https://www.noip.com)"
    echo "   - Dynu (https://www.dynu.com)"
    echo "   - Cloudflare (https://cloudflare.com)"
    echo ""
    WEB_PORT=$(grep -E "^WEB_PORT=" config/domain.conf 2>/dev/null | cut -d'=' -f2 || echo "5000")
    echo "6. Временно используйте HTTP без SSL:"
    echo -e "   ${CYAN}http://$SERVER_IP:${WEB_PORT}${NC}"
    echo -e "   ${GRAY}(порт можно изменить в config/domain.conf)${NC}"
fi

echo ""
echo -e "${BLUE}Подробная инструкция: ${CYAN}SSL_TROUBLESHOOTING.md${NC}"
echo ""
