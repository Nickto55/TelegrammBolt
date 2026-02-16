#!/bin/bash
# Скрипт для настройки домена/SSL и обновления конфигурации Nginx с WebSocket

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$PROJECT_DIR/config/domain.conf"

NGINX_CONF="/etc/nginx/sites-available/telegrambot"
BACKUP_CONF="/etc/nginx/sites-available/telegrambot.backup.$(date +%Y%m%d_%H%M%S)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN=""
WEB_PORT="5000"
SSL_ENABLED="false"
SELF_SIGNED="false"
SSL_EMAIL=""

load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        DOMAIN=$(grep -E '^DOMAIN=' "$CONFIG_FILE" | head -n1 | cut -d'=' -f2-)
        WEB_PORT=$(grep -E '^WEB_PORT=' "$CONFIG_FILE" | head -n1 | cut -d'=' -f2-)
        SSL_ENABLED=$(grep -E '^SSL_ENABLED=' "$CONFIG_FILE" | head -n1 | cut -d'=' -f2-)
        SELF_SIGNED=$(grep -E '^SELF_SIGNED=' "$CONFIG_FILE" | head -n1 | cut -d'=' -f2-)
        SSL_EMAIL=$(grep -E '^SSL_EMAIL=' "$CONFIG_FILE" | head -n1 | cut -d'=' -f2-)
    fi

    WEB_PORT=${WEB_PORT:-5000}
    SSL_ENABLED=${SSL_ENABLED:-false}
    SELF_SIGNED=${SELF_SIGNED:-false}
}

save_config() {
    mkdir -p "$(dirname "$CONFIG_FILE")"
    cat > "$CONFIG_FILE" <<EOF
DOMAIN=$DOMAIN
SSL_EMAIL=$SSL_EMAIL
WEB_PORT=$WEB_PORT
SSL_ENABLED=$SSL_ENABLED
SELF_SIGNED=$SELF_SIGNED
EOF
}

write_nginx_http() {
    sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:$WEB_PORT/socket.io/;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF
}

write_nginx_https() {
    local cert_fullchain=$1
    local cert_privkey=$2

    sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate $cert_fullchain;
    ssl_certificate_key $cert_privkey;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:$WEB_PORT/socket.io/;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF
}

reload_nginx() {
    sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/telegrambot
    if sudo nginx -t 2>&1 | grep -q "successful"; then
        sudo systemctl reload nginx
        echo -e "${GREEN}✓ Nginx перезагружен${NC}"
    else
        echo -e "${RED}✗ Ошибка в конфигурации Nginx${NC}"
        sudo nginx -t || true
        if [ -f "$BACKUP_CONF" ]; then
            sudo cp "$BACKUP_CONF" "$NGINX_CONF"
            sudo systemctl reload nginx || true
            echo -e "${YELLOW}Восстановлена резервная копия конфигурации${NC}"
        fi
        exit 1
    fi
}

check_dns() {
    local server_ip
    local domain_ip
    server_ip=$(curl -s ifconfig.me 2>/dev/null || wget -qO- ifconfig.me 2>/dev/null || echo "")
    domain_ip=$(dig +short "$DOMAIN" 2>/dev/null | tail -n1)

    echo -e "${BLUE}IP сервера: ${server_ip:-unknown}${NC}"
    echo -e "${BLUE}IP домена:  ${domain_ip:-не найден}${NC}"

    if [ -z "$domain_ip" ]; then
        echo -e "${YELLOW}DNS ещё не обновился. SSL Let's Encrypt может не сработать.${NC}"
        return 1
    fi

    if [ -n "$server_ip" ] && [ "$server_ip" != "$domain_ip" ]; then
        echo -e "${YELLOW}IP домена не совпадает с IP сервера.${NC}"
        return 1
    fi

    echo -e "${GREEN}DNS выглядит корректно${NC}"
    return 0
}

configure_domain_ssl() {
    load_config

    echo -e "${BLUE}Текущие настройки:${NC}"
    echo "  Домен: ${DOMAIN:-не задан}"
    echo "  Порт: ${WEB_PORT}"
    echo "  SSL:  ${SSL_ENABLED}"
    echo ""

    read -p "Введите домен (Enter = оставить как есть): " domain_input
    if [ -n "$domain_input" ]; then
        DOMAIN="$domain_input"
    fi

    read -p "Введите порт (Enter = $WEB_PORT): " port_input
    if [ -n "$port_input" ]; then
        if [[ "$port_input" =~ ^[0-9]+$ ]]; then
            WEB_PORT="$port_input"
        else
            echo -e "${YELLOW}Неверный порт. Оставляю $WEB_PORT${NC}"
        fi
    fi

    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}Домен не задан. Отмена.${NC}"
        return
    fi

    echo ""
    echo -e "${BLUE}Выберите тип SSL:${NC}"
    echo "1) Let's Encrypt (через nginx)"
    echo "2) Let's Encrypt (standalone)"
    echo "3) Самоподписанный сертификат"
    echo "4) Без SSL (HTTP)"
    read -p "Ваш выбор (1-4): " ssl_choice

    SSL_ENABLED="false"
    SELF_SIGNED="false"

    if [ -f "$NGINX_CONF" ]; then
        sudo cp "$NGINX_CONF" "$BACKUP_CONF"
        echo -e "${GREEN}✓ Резервная копия: $BACKUP_CONF${NC}"
    fi

    case "$ssl_choice" in
        1)
            check_dns || true
            read -p "Email для Let's Encrypt: " SSL_EMAIL
            if ! command -v certbot &>/dev/null; then
                echo -e "${RED}certbot не найден. Установите certbot и повторите.${NC}"
                return
            fi

            write_nginx_http
            reload_nginx

            echo -e "${YELLOW}Получение сертификата Let's Encrypt...${NC}"
            if sudo certbot --nginx -d "$DOMAIN" --email "$SSL_EMAIL" --agree-tos --non-interactive; then
                SSL_ENABLED="true"
                SELF_SIGNED="false"
            else
                echo -e "${RED}Не удалось получить сертификат Let's Encrypt${NC}"
                return
            fi

            write_nginx_https "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "/etc/letsencrypt/live/$DOMAIN/privkey.pem"
            reload_nginx
            ;;
        2)
            check_dns || true
            read -p "Email для Let's Encrypt: " SSL_EMAIL
            if ! command -v certbot &>/dev/null; then
                echo -e "${RED}certbot не найден. Установите certbot и повторите.${NC}"
                return
            fi

            echo -e "${YELLOW}Остановка nginx для standalone...${NC}"
            sudo systemctl stop nginx
            if sudo certbot certonly --standalone -d "$DOMAIN" --email "$SSL_EMAIL" --agree-tos --non-interactive; then
                SSL_ENABLED="true"
                SELF_SIGNED="false"
                write_nginx_https "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "/etc/letsencrypt/live/$DOMAIN/privkey.pem"
                sudo systemctl start nginx
                reload_nginx
            else
                sudo systemctl start nginx
                echo -e "${RED}Не удалось получить сертификат Let's Encrypt${NC}"
                return
            fi
            ;;
        3)
            echo -e "${YELLOW}Создание самоподписанного сертификата...${NC}"
            sudo mkdir -p /etc/ssl/telegrambot
            sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
                -keyout /etc/ssl/telegrambot/privkey.pem \
                -out /etc/ssl/telegrambot/fullchain.pem \
                -subj "/C=RU/ST=Moscow/L=Moscow/O=TelegramBolt/CN=$DOMAIN" 2>/dev/null

            if [ -f /etc/ssl/telegrambot/privkey.pem ] && [ -f /etc/ssl/telegrambot/fullchain.pem ]; then
                SSL_ENABLED="true"
                SELF_SIGNED="true"
                write_nginx_https "/etc/ssl/telegrambot/fullchain.pem" "/etc/ssl/telegrambot/privkey.pem"
                reload_nginx
            else
                echo -e "${RED}Не удалось создать самоподписанный сертификат${NC}"
                return
            fi
            ;;
        4)
            write_nginx_http
            reload_nginx
            SSL_ENABLED="false"
            SELF_SIGNED="false"
            ;;
        *)
            echo -e "${YELLOW}Неверный выбор. Отмена.${NC}"
            return
            ;;
    esac

    save_config

    if [ "$SSL_ENABLED" = "true" ]; then
        echo -e "${GREEN}Готово! Доступ: https://$DOMAIN${NC}"
    else
        echo -e "${GREEN}Готово! Доступ: http://$DOMAIN${NC}"
    fi
}

renew_certificate() {
    load_config

    if [ "$SSL_ENABLED" != "true" ]; then
        echo -e "${YELLOW}SSL не включен в config/domain.conf${NC}"
        return
    fi

    if [ "$SELF_SIGNED" = "true" ]; then
        echo -e "${YELLOW}Самоподписанный сертификат не обновляется через certbot${NC}"
        return
    fi

    if ! command -v certbot &>/dev/null; then
        echo -e "${RED}certbot не найден. Установите certbot и повторите.${NC}"
        return
    fi

    echo -e "${YELLOW}Обновление сертификата Let's Encrypt...${NC}"
    sudo certbot renew --quiet --post-hook "systemctl reload nginx"
    echo -e "${GREEN}Сертификат обновлен${NC}"
}

echo -e "${BLUE}Настройка домена и SSL + Nginx WebSocket${NC}"
echo "1) Настроить домен и SSL"
echo "2) Обновить сертификат (Let's Encrypt)"
echo "0) Выход"
read -p "Ваш выбор: " main_choice

case "$main_choice" in
    1) configure_domain_ssl ;;
    2) renew_certificate ;;
    0) exit 0 ;;
    *) echo -e "${YELLOW}Неверный выбор${NC}" ;;
esac
