#!/bin/bash

# =============================================================================
# Скрипт установки TelegramBolt для Debian/Ubuntu
# =============================================================================
# 
# Возможности:
#   - Telegram бот
#   - Веб-интерфейс с терминалом
#   - Гибкая настройка портов (5000/8080/3000/свой)
#   - SSL через Let's Encrypt или самоподписанный
#   - Автозапуск через systemd
#
# Использование:
#   ./setup.sh                    - Полная установка
#   ./quick-start.sh              - Быстрая установка
#   ./manage.sh                   - Панель управления
#
# Порты:
#   По умолчанию: 5000
#   Альтернативные: 8080, 3000
#   Настройка: config/domain.conf → WEB_PORT=8080
#
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Установка TelegramBolt${NC}"
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

echo -e "${GREEN}[2/9] Установка зависимостей...${NC}"
sudo apt install -y python3 python3-pip python3-venv git curl wget build-essential \
    libssl-dev libffi-dev python3-dev libzbar0 zbar-tools nginx certbot python3-certbot-nginx

echo -e "${GREEN}[3/7] Создание виртуального окружения Python...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}Виртуальное окружение создано${NC}"
else
    echo -e "${YELLOW}Виртуальное окружение уже существует, пропускаем...${NC}"
fi

# Создание симлинка python -> python3 в виртуальном окружении
if [ ! -e "venv/bin/python" ]; then
    ln -s python3 venv/bin/python
    echo -e "${GREEN}Создан симлинк python -> python3${NC}"
fi

echo -e "${GREEN}[4/7] Установка Python зависимостей...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}[5/9] Создание необходимых директорий...${NC}"
mkdir -p data/photos
mkdir -p config
mkdir -p logs
echo -e "${GREEN}Директории созданы${NC}"

echo -e "${GREEN}[6/9] Настройка конфигурации...${NC}"

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

# Настройка домена и SSL
echo -e "${GREEN}[7/9] Настройка домена и SSL (опционально)...${NC}"
read -p "Хотите настроить домен и SSL сертификат? (y/n): " SETUP_SSL
if [[ $SETUP_SSL =~ ^[Yy]$ ]]; then
    read -p "Введите ваш домен (например: bot.example.com): " DOMAIN
    
    # Проверка DNS
    echo -e "${YELLOW}Проверка DNS для $DOMAIN...${NC}"
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || wget -qO- ifconfig.me 2>/dev/null || echo "unknown")
    DOMAIN_IP=$(dig +short $DOMAIN 2>/dev/null | tail -n1)
    
    echo -e "${BLUE}IP вашего сервера: $SERVER_IP${NC}"
    echo -e "${BLUE}IP домена $DOMAIN: ${DOMAIN_IP:-не найден}${NC}"
    
    if [ -z "$DOMAIN_IP" ]; then
        echo -e "${RED}⚠️  ВНИМАНИЕ: Домен $DOMAIN не резолвится!${NC}"
        echo -e "${YELLOW}Возможные решения:${NC}"
        echo -e "  1. Убедитесь что домен указывает на IP: $SERVER_IP"
        echo -e "  2. Подождите пока DNS обновится (до 24 часов)"
        echo -e "  3. Используйте другой домен или сервис (DuckDNS, No-IP)"
        echo ""
        read -p "Продолжить настройку без SSL? (y/n): " CONTINUE
        if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Настройка SSL отменена${NC}"
            cat > config/domain.conf <<EOF
DOMAIN=localhost
WEB_PORT=5000
SSL_ENABLED=false
EOF
            continue
        fi
    elif [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
        echo -e "${YELLOW}⚠️  IP домена ($DOMAIN_IP) не совпадает с IP сервера ($SERVER_IP)${NC}"
        read -p "Продолжить? (y/n): " CONTINUE
        if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
            cat > config/domain.conf <<EOF
DOMAIN=localhost
WEB_PORT=5000
SSL_ENABLED=false
EOF
            continue
        fi
    else
        echo -e "${GREEN}✓ DNS настроен правильно${NC}"
    fi
    
    read -p "Введите email для Let's Encrypt: " SSL_EMAIL
    
    echo ""
    echo -e "${YELLOW}Выберите порт для веб-интерфейса:${NC}"
    echo "  1. 5000 (по умолчанию)"
    echo "  2. 8080"
    echo "  3. 3000"
    echo "  4. Свой порт"
    read -p "Выберите (1-4): " PORT_CHOICE
    
    case $PORT_CHOICE in
        1) WEB_PORT=5000 ;;
        2) WEB_PORT=8080 ;;
        3) WEB_PORT=3000 ;;
        4) read -p "Введите номер порта: " WEB_PORT ;;
        *) 
            echo -e "${YELLOW}Неверный выбор, используется порт 5000${NC}"
            WEB_PORT=5000
            ;;
    esac
    
    echo -e "${GREEN}✓ Выбран порт: $WEB_PORT${NC}"
    
    # Проверка открытых портов
    echo -e "${YELLOW}Проверка firewall...${NC}"
    if command -v ufw &> /dev/null; then
        sudo ufw allow 80/tcp >/dev/null 2>&1
        sudo ufw allow 443/tcp >/dev/null 2>&1
        echo -e "${GREEN}✓ Порты 80, 443 открыты${NC}"
    fi
    
    # Создание конфигурации nginx
    sudo tee /etc/nginx/sites-available/telegrambot > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Для проверки Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Активация конфигурации
    sudo ln -sf /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/
    
    # Проверка конфигурации nginx
    if sudo nginx -t 2>&1 | grep -q "successful"; then
        sudo systemctl reload nginx
        echo -e "${GREEN}✓ Nginx настроен${NC}"
    else
        echo -e "${RED}✗ Ошибка в конфигурации nginx${NC}"
        sudo nginx -t
        read -p "Нажмите Enter для продолжения..."
    fi
    
    # Получение SSL сертификата
    echo -e "${YELLOW}Получение SSL сертификата...${NC}"
    echo -e "${BLUE}Выберите метод получения SSL:${NC}"
    echo "1. Let's Encrypt через nginx (бесплатный, требует валидный домен)"
    echo "2. Let's Encrypt через standalone (бесплатный, требует валидный домен)"
    echo "3. Самоподписанный сертификат (для тестирования, без домена)"
    echo "4. Пропустить SSL (использовать только HTTP)"
    read -p "Ваш выбор (1/2/3/4): " SSL_METHOD
    
    SSL_SUCCESS=false
    SELF_SIGNED=false
    case $SSL_METHOD in
        1)
            if sudo certbot --nginx -d $DOMAIN --email $SSL_EMAIL --agree-tos --non-interactive 2>&1; then
                SSL_SUCCESS=true
            else
                echo -e "${RED}✗ Не удалось получить SSL сертификат через nginx${NC}"
                echo -e "${YELLOW}Попробуйте другой метод или проверьте DNS${NC}"
                read -p "Создать самоподписанный сертификат вместо этого? (y/n): " CREATE_SELF
                if [[ $CREATE_SELF =~ ^[Yy]$ ]]; then
                    SSL_METHOD=3
                fi
            fi
            ;;
        2)
            echo -e "${YELLOW}Остановка nginx для standalone режима...${NC}"
            sudo systemctl stop nginx
            if sudo certbot certonly --standalone -d $DOMAIN --email $SSL_EMAIL --agree-tos --non-interactive 2>&1; then
                SSL_SUCCESS=true
                # Обновляем конфигурацию nginx для SSL
                sudo tee /etc/nginx/sites-available/telegrambot > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
            else
                echo -e "${RED}✗ Не удалось получить SSL сертификат через standalone${NC}"
            fi
            sudo systemctl start nginx
            ;;
        3)
            echo -e "${YELLOW}Создание самоподписанного SSL сертификата...${NC}"
            
            # Создание директории для сертификатов
            sudo mkdir -p /etc/ssl/telegrambot
            
            # Генерация приватного ключа и сертификата
            echo -e "${BLUE}Введите информацию для сертификата (можно оставить пустым):${NC}"
            read -p "Страна (RU): " SSL_COUNTRY
            SSL_COUNTRY=${SSL_COUNTRY:-RU}
            read -p "Регион/Область: " SSL_STATE
            SSL_STATE=${SSL_STATE:-Moscow}
            read -p "Город: " SSL_CITY
            SSL_CITY=${SSL_CITY:-Moscow}
            read -p "Организация: " SSL_ORG
            SSL_ORG=${SSL_ORG:-TelegramBot}
            
            # Создание самоподписанного сертификата на 10 лет
            sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
                -keyout /etc/ssl/telegrambot/privkey.pem \
                -out /etc/ssl/telegrambot/fullchain.pem \
                -subj "/C=$SSL_COUNTRY/ST=$SSL_STATE/L=$SSL_CITY/O=$SSL_ORG/CN=$DOMAIN" 2>/dev/null
            
            if [ -f /etc/ssl/telegrambot/privkey.pem ] && [ -f /etc/ssl/telegrambot/fullchain.pem ]; then
                echo -e "${GREEN}✓ Самоподписанный сертификат создан${NC}"
                SSL_SUCCESS=true
                SELF_SIGNED=true
                
                # Настройка nginx для самоподписанного сертификата
                sudo tee /etc/nginx/sites-available/telegrambot > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    ssl_certificate /etc/ssl/telegrambot/fullchain.pem;
    ssl_certificate_key /etc/ssl/telegrambot/privkey.pem;
    
    # Отключаем проверку для самоподписанных
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
                sudo nginx -t && sudo systemctl reload nginx
                
                echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Самоподписанный сертификат!${NC}"
                echo -e "${YELLOW}Браузер покажет предупреждение о безопасности.${NC}"
                echo -e "${YELLOW}Это нормально для самоподписанных сертификатов.${NC}"
            else
                echo -e "${RED}✗ Ошибка создания сертификата${NC}"
            fi
            ;;
        4)
            echo -e "${YELLOW}SSL пропущен, используется только HTTP${NC}"
            ;;
    esac
    
    # Сохранение настроек
    cat > config/domain.conf <<EOF
DOMAIN=$DOMAIN
SSL_EMAIL=$SSL_EMAIL
WEB_PORT=$WEB_PORT
SSL_ENABLED=$SSL_SUCCESS
SELF_SIGNED=$SELF_SIGNED
EOF
    
    if [ "$SSL_SUCCESS" = true ]; then
        if [ "$SELF_SIGNED" = true ]; then
            echo -e "${GREEN}✓ Самоподписанный SSL сертификат установлен для $DOMAIN${NC}"
            echo -e "${GREEN}✓ Ваш сайт: https://$DOMAIN${NC}"
            echo -e "${YELLOW}⚠️  Браузер будет предупреждать о безопасности${NC}"
            echo -e "${YELLOW}Это нормально для самоподписанных сертификатов${NC}"
            echo -e "${BLUE}Чтобы убрать предупреждение, добавьте сертификат в доверенные:${NC}"
            echo -e "${CYAN}sudo cp /etc/ssl/telegrambot/fullchain.pem /usr/local/share/ca-certificates/telegrambot.crt${NC}"
            echo -e "${CYAN}sudo update-ca-certificates${NC}"
        else
            echo -e "${GREEN}✓ SSL сертификат успешно установлен для $DOMAIN${NC}"
            echo -e "${GREEN}✓ Ваш сайт: https://$DOMAIN${NC}"
        fi
        
        # Настройка автообновления SSL только для Let's Encrypt
        if [ "$SELF_SIGNED" != true ]; then
            echo -e "${YELLOW}Настройка автообновления SSL...${NC}"
            (sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | sudo crontab -
            echo -e "${GREEN}✓ Автообновление SSL настроено (проверка каждый день в 3:00)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  SSL не установлен. Используйте: http://$DOMAIN${NC}"
    fi
else
    echo -e "${YELLOW}Настройка домена и SSL пропущена${NC}"
    cat > config/domain.conf <<EOF
DOMAIN=localhost
WEB_PORT=5000
SSL_ENABLED=false
EOF
fi

echo -e "${GREEN}[8/9] Создание systemd сервисов...${NC}"

# Создание systemd сервиса для бота
sudo tee /etc/systemd/system/telegrambot.service > /dev/null <<EOF
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 $(pwd)/bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Создание systemd сервиса для веб-интерфейса
sudo tee /etc/systemd/system/telegramweb.service > /dev/null <<EOF
[Unit]
Description=Telegram Bot Web Interface
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 $(pwd)/web/web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo -e "${GREEN}Systemd сервисы созданы${NC}"

echo -e "${GREEN}[9/9] Создание скриптов управления...${NC}"

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

# Создание панели управления
cat > manage.sh <<'MGEOF'
#!/bin/bash

# =============================================================================
# TelegrammBot - Панель Управления 
# =============================================================================

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Функция очистки экрана
clear_screen() {
    clear
}

# Получение статуса сервиса
get_service_status() {
    if systemctl is-active --quiet $1; then
        echo -e "${GREEN}●${NC} Running"
    else
        echo -e "${RED}●${NC} Stopped"
    fi
}

# Получение времени работы
get_uptime() {
    if systemctl is-active --quiet $1; then
        systemctl show $1 --property=ActiveEnterTimestamp --value | cut -d' ' -f1-2
    else
        echo "N/A"
    fi
}

# Показать главное меню
show_menu() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}         ${GREEN}TelegrammBot - Панель Управления${NC}              ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Статус сервисов
    BOT_STATUS=$(get_service_status telegrambot)
    WEB_STATUS=$(get_service_status telegramweb)
    NGINX_STATUS=$(get_service_status nginx)
    
    echo -e "${BLUE}[Статус Сервисов]${NC}"
    echo -e "  Telegram Bot:     $BOT_STATUS"
    echo -e "  Web Interface:    $WEB_STATUS"
    echo -e "  Nginx:            $NGINX_STATUS"
    echo ""
    
    # Загрузка конфигурации
    if [ -f config/domain.conf ]; then
        source config/domain.conf
        echo -e "${BLUE}[Конфигурация]${NC}"
        echo -e "  Домен:            ${YELLOW}$DOMAIN${NC}"
        echo -e "  Порт:             ${YELLOW}$WEB_PORT${NC}"
        echo -e "  SSL:              ${YELLOW}$SSL_ENABLED${NC}"
        echo ""
    fi
    
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}1.${NC} Запустить все сервисы                                ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}2.${NC} Остановить все сервисы                               ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}3.${NC} Перезапустить все сервисы                            ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${YELLOW}4.${NC} Управление Telegram Bot                              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${YELLOW}5.${NC} Управление Web интерфейсом                           ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}6.${NC} Просмотр логов                                       ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}7.${NC} Настройка SSL/Домена                                 ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}8.${NC} Обновить сертификат SSL                              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}9.${NC} Редактировать конфигурацию                           ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${BLUE}10.${NC} Мониторинг системы                                   ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${BLUE}11.${NC} Резервное копирование                                ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}12.${NC} Обновить с Git                                       ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${RED}13.${NC} Удалить все данные                                   ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${RED}0.${NC} Выход                                                ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Управление ботом
manage_bot() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}           ${GREEN}Управление Telegram Bot${NC}                      ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "1. Запустить бот"
    echo "2. Остановить бот"
    echo "3. Перезапустить бот"
    echo "4. Статус бота"
    echo "5. Логи бота (live)"
    echo "0. Назад"
    echo ""
    read -p "Выберите действие: " choice
    
    case $choice in
        1) sudo systemctl start telegrambot && echo -e "${GREEN}✓ Бот запущен${NC}" ;;
        2) sudo systemctl stop telegrambot && echo -e "${YELLOW}✓ Бот остановлен${NC}" ;;
        3) sudo systemctl restart telegrambot && echo -e "${GREEN}✓ Бот перезапущен${NC}" ;;
        4) sudo systemctl status telegrambot ;;
        5) sudo journalctl -u telegrambot -f ;;
        0) return ;;
    esac
    read -p "Нажмите Enter для продолжения..."
}

# Управление веб-интерфейсом
manage_web() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}           ${GREEN}Управление Web интерфейсом${NC}                   ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "1. Запустить веб-интерфейс"
    echo "2. Остановить веб-интерфейс"
    echo "3. Перезапустить веб-интерфейс"
    echo "4. Статус веб-интерфейса"
    echo "5. Логи веб-интерфейса (live)"
    echo "0. Назад"
    echo ""
    read -p "Выберите действие: " choice
    
    case $choice in
        1) sudo systemctl start telegramweb && echo -e "${GREEN}✓ Веб-интерфейс запущен${NC}" ;;
        2) sudo systemctl stop telegramweb && echo -e "${YELLOW}✓ Веб-интерфейс остановлен${NC}" ;;
        3) sudo systemctl restart telegramweb && echo -e "${GREEN}✓ Веб-интерфейс перезапущен${NC}" ;;
        4) sudo systemctl status telegramweb ;;
        5) sudo journalctl -u telegramweb -f ;;
        0) return ;;
    esac
    read -p "Нажмите Enter для продолжения..."
}

# Просмотр логов
view_logs() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}               ${GREEN}Просмотр логов${NC}                           ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "1. Логи Telegram Bot (последние 50 строк)"
    echo "2. Логи Web интерфейса (последние 50 строк)"
    echo "3. Логи Nginx (последние 50 строк)"
    echo "4. Логи Telegram Bot (live)"
    echo "5. Логи Web интерфейса (live)"
    echo "0. Назад"
    echo ""
    read -p "Выберите действие: " choice
    
    case $choice in
        1) sudo journalctl -u telegrambot -n 50 --no-pager ;;
        2) sudo journalctl -u telegramweb -n 50 --no-pager ;;
        3) sudo tail -n 50 /var/log/nginx/error.log ;;
        4) sudo journalctl -u telegrambot -f ;;
        5) sudo journalctl -u telegramweb -f ;;
        0) return ;;
    esac
    read -p "Нажмите Enter для продолжения..."
}

# Настройка SSL
setup_ssl() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}            ${GREEN}Настройка SSL/Домена${NC}                        ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    read -p "Введите ваш домен: " DOMAIN
    
    echo ""
    echo -e "${YELLOW}Выберите порт для веб-интерфейса:${NC}"
    echo "  1. 5000 (по умолчанию)"
    echo "  2. 8080"
    echo "  3. 3000"
    echo "  4. Свой порт"
    read -p "Выберите (1-4): " PORT_CHOICE
    
    case $PORT_CHOICE in
        1) WEB_PORT=5000 ;;
        2) WEB_PORT=8080 ;;
        3) WEB_PORT=3000 ;;
        4) read -p "Введите номер порта: " WEB_PORT ;;
        *) 
            echo -e "${YELLOW}Неверный выбор, используется порт 5000${NC}"
            WEB_PORT=5000
            ;;
    esac
    
    echo -e "${GREEN}✓ Выбран порт: $WEB_PORT${NC}"
    
    echo ""
    echo -e "${BLUE}Выберите тип SSL сертификата:${NC}"
    echo "1. Let's Encrypt (бесплатный, требует валидный домен)"
    echo "2. Самоподписанный (для тестирования, любой домен/IP)"
    read -p "Ваш выбор (1/2): " SSL_TYPE
    
    case $SSL_TYPE in
        1)
            read -p "Введите email для Let's Encrypt: " SSL_EMAIL
            
            # Создание конфигурации nginx
            sudo tee /etc/nginx/sites-available/telegrambot > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
            
            sudo ln -sf /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/
            sudo nginx -t && sudo systemctl reload nginx
            
            # Получение SSL
            echo -e "${YELLOW}Получение SSL сертификата от Let's Encrypt...${NC}"
            if sudo certbot --nginx -d $DOMAIN --email $SSL_EMAIL --agree-tos --non-interactive; then
                cat > config/domain.conf <<EOF
DOMAIN=$DOMAIN
SSL_EMAIL=$SSL_EMAIL
WEB_PORT=$WEB_PORT
SSL_ENABLED=true
SELF_SIGNED=false
EOF
                echo -e "${GREEN}✓ SSL успешно настроен для $DOMAIN${NC}"
            else
                echo -e "${RED}✗ Ошибка получения SSL сертификата${NC}"
            fi
            ;;
        2)
            echo -e "${YELLOW}Создание самоподписанного SSL сертификата...${NC}"
            
            # Создание директории для сертификатов
            sudo mkdir -p /etc/ssl/telegrambot
            
            # Генерация самоподписанного сертификата
            sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
                -keyout /etc/ssl/telegrambot/privkey.pem \
                -out /etc/ssl/telegrambot/fullchain.pem \
                -subj "/C=RU/ST=Moscow/L=Moscow/O=TelegramBot/CN=$DOMAIN" 2>/dev/null
            
            if [ -f /etc/ssl/telegrambot/privkey.pem ]; then
                # Создание конфигурации nginx для SSL
                sudo tee /etc/nginx/sites-available/telegrambot > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    ssl_certificate /etc/ssl/telegrambot/fullchain.pem;
    ssl_certificate_key /etc/ssl/telegrambot/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
                
                sudo ln -sf /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/
                sudo nginx -t && sudo systemctl reload nginx
                
                cat > config/domain.conf <<EOF
DOMAIN=$DOMAIN
WEB_PORT=$WEB_PORT
SSL_ENABLED=true
SELF_SIGNED=true
EOF
                
                echo -e "${GREEN}✓ Самоподписанный SSL сертификат создан${NC}"
                echo -e "${GREEN}✓ Ваш сайт: https://$DOMAIN${NC}"
                echo -e "${YELLOW}⚠️  Браузер будет показывать предупреждение о безопасности${NC}"
                echo -e "${YELLOW}Это нормально для самоподписанных сертификатов${NC}"
            else
                echo -e "${RED}✗ Ошибка создания сертификата${NC}"
            fi
            ;;
    esac
    
    read -p "Нажмите Enter для продолжения..."
}

# Обновление SSL
renew_ssl() {
    echo -e "${YELLOW}Обновление SSL сертификата...${NC}"
    sudo certbot renew
    echo -e "${GREEN}✓ SSL сертификат обновлен${NC}"
    read -p "Нажмите Enter для продолжения..."
}

# Редактирование конфигурации
edit_config() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}          ${GREEN}Редактирование конфигурации${NC}                  ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "1. Конфигурация бота (ven_bot.json)"
    echo "2. Конфигурация SMTP (smtp_config.json)"
    echo "3. Конфигурация домена (domain.conf)"
    echo "0. Назад"
    echo ""
    read -p "Выберите файл: " choice
    
    case $choice in
        1) ${EDITOR:-nano} config/ven_bot.json ;;
        2) ${EDITOR:-nano} config/smtp_config.json ;;
        3) ${EDITOR:-nano} config/domain.conf ;;
        0) return ;;
    esac
}

# Мониторинг системы
system_monitor() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}            ${GREEN}Мониторинг системы${NC}                          ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${BLUE}[CPU и Память]${NC}"
    top -bn1 | head -n 5
    echo ""
    
    echo -e "${BLUE}[Использование диска]${NC}"
    df -h | grep -E '^/dev/'
    echo ""
    
    echo -e "${BLUE}[Сетевые подключения на стандартных портах]${NC}"
    ss -tunlp 2>/dev/null | grep -E ':(5000|5001|8080|3000|80|443)' || echo "Нет активных подключений"
    echo ""
    
    echo -e "${BLUE}[Порты веб-интерфейса]${NC}"
    for PORT in 5000 5001 8080 3000; do
        if ss -tunlp 2>/dev/null | grep -q ":$PORT "; then
            echo -e "${GREEN}✓ Порт $PORT: занят${NC}"
        else
            echo -e "${YELLOW}○ Порт $PORT: свободен${NC}"
        fi
    done
    echo ""
    
    read -p "Нажмите Enter для продолжения..."
}

# Резервное копирование
backup_data() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}          ${GREEN}Резервное копирование${NC}                        ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    BACKUP_DIR="backups"
    mkdir -p $BACKUP_DIR
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    echo -e "${YELLOW}Создание резервной копии...${NC}"
    tar -czf $BACKUP_FILE config/ data/ 2>/dev/null
    
    if [ -f "$BACKUP_FILE" ]; then
        echo -e "${GREEN}✓ Резервная копия создана: $BACKUP_FILE${NC}"
        echo -e "${BLUE}Размер: $(du -h $BACKUP_FILE | cut -f1)${NC}"
    else
        echo -e "${RED}✗ Ошибка создания резервной копии${NC}"
    fi
    
    read -p "Нажмите Enter для продолжения..."
}

# Обновление с Git
update_from_git() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}              ${GREEN}Обновление с Git${NC}                         ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Проверяем что находимся в git репозитории
    if [ ! -d ".git" ]; then
        echo -e "${RED}✗ Ошибка: Текущая директория не является git репозиторием${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    echo -e "${BLUE}Текущая ветка:${NC} $(git branch --show-current)"
    echo -e "${BLUE}Последний коммит:${NC}"
    git log -1 --oneline
    echo ""
    
    read -p "Создать резервную копию перед обновлением? (y/n): " backup_choice
    if [ "$backup_choice" = "y" ] || [ "$backup_choice" = "Y" ]; then
        echo -e "${YELLOW}Создание резервной копии...${NC}"
        BACKUP_DIR="backups"
        mkdir -p $BACKUP_DIR
        BACKUP_FILE="$BACKUP_DIR/backup_before_update_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar -czf $BACKUP_FILE config/ data/ 2>/dev/null
        echo -e "${GREEN}✓ Резервная копия создана: $BACKUP_FILE${NC}"
        echo ""
    fi
    
    echo -e "${YELLOW}Проверка обновлений...${NC}"
    git fetch origin
    
    CURRENT=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/$(git branch --show-current))
    
    if [ "$CURRENT" = "$REMOTE" ]; then
        echo -e "${GREEN}✓ Установлена последняя версия${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    echo -e "${YELLOW}Найдены обновления:${NC}"
    git log HEAD..origin/$(git branch --show-current) --oneline
    echo ""
    
    read -p "Продолжить обновление? (y/n): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo -e "${YELLOW}Обновление отменено${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    echo -e "${YELLOW}Остановка сервисов...${NC}"
    sudo systemctl stop telegrambot telegramweb
    
    echo -e "${YELLOW}Загрузка обновлений...${NC}"
    git pull origin $(git branch --show-current)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Код обновлён${NC}"
        
        # Проверяем изменения в requirements.txt
        if git diff HEAD@{1} HEAD --name-only | grep -q "requirements.txt"; then
            echo -e "${YELLOW}Обновление Python зависимостей...${NC}"
            source venv/bin/activate
            pip install -r requirements.txt --upgrade
        fi
        
        echo -e "${YELLOW}Запуск сервисов...${NC}"
        sudo systemctl start telegrambot telegramweb
        
        echo ""
        echo -e "${GREEN}✓ Обновление завершено успешно!${NC}"
        echo -e "${BLUE}Новая версия:${NC}"
        git log -1 --oneline
    else
        echo -e "${RED}✗ Ошибка при обновлении${NC}"
        echo -e "${YELLOW}Восстановление сервисов...${NC}"
        sudo systemctl start telegrambot telegramweb
    fi
    
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Основной цикл
while true; do
    show_menu
    read -p "Выберите действие: " choice
    
    case $choice in
        1)
            echo -e "${YELLOW}Запуск всех сервисов...${NC}"
            sudo systemctl start telegrambot telegramweb nginx
            echo -e "${GREEN}✓ Все сервисы запущены${NC}"
            sleep 2
            ;;
        2)
            echo -e "${YELLOW}Остановка всех сервисов...${NC}"
            sudo systemctl stop telegrambot telegramweb
            echo -e "${YELLOW}✓ Все сервисы остановлены${NC}"
            sleep 2
            ;;
        3)
            echo -e "${YELLOW}Перезапуск всех сервисов...${NC}"
            sudo systemctl restart telegrambot telegramweb nginx
            echo -e "${GREEN}✓ Все сервисы перезапущены${NC}"
            sleep 2
            ;;
        4) manage_bot ;;
        5) manage_web ;;
        6) view_logs ;;
        7) setup_ssl ;;
        8) renew_ssl ;;
        9) edit_config ;;
        10) system_monitor ;;
        11) backup_data ;;
        12) update_from_git ;;
        13)
            read -p "Вы уверены? Это удалит ВСЕ данные! (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                sudo systemctl stop telegrambot telegramweb
                rm -rf data/* config/*.json
                echo -e "${RED}✓ Данные удалены${NC}"
            fi
            sleep 2
            ;;
        0)
            echo -e "${GREEN}Выход...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Неверный выбор${NC}"
            sleep 1
            ;;
    esac
done
MGEOF
chmod +x manage.sh

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Установка завершена успешно!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}🎮 Панель управления (рекомендуется):${NC}"
echo -e "  ${GREEN}./manage.sh${NC}"
echo ""
echo -e "${YELLOW}Главные опции manage.sh:${NC}"
echo -e "  ${CYAN}Опция 6${NC}  - Запустить веб + терминал (выбор порта)"
echo -e "  ${CYAN}Опция 11${NC} - Детальный статус (процессы + порты)"
echo -e "  ${CYAN}Опция 13${NC} - Настройка systemd (автозапуск)"
echo ""
echo -e "${YELLOW}⚙️  Настройка портов:${NC}"
echo -e "  ${GREEN}config/domain.conf${NC} → WEB_PORT=8080"
echo -e "  ${GREEN}./manage.sh${NC} → Опция 6 → Выбрать порт"
echo -e "  ${GREEN}WEB_PORT=8080 ./manage.sh${NC}"
echo ""
echo -e "${YELLOW}📋 Конфигурационные файлы:${NC}"
echo -e "  ${GREEN}config/ven_bot.json${NC}     - настройки бота"
echo -e "  ${GREEN}config/smtp_config.json${NC} - настройки email"
echo -e "  ${GREEN}config/domain.conf${NC}      - домен, SSL, порты"
echo ""
echo -e "${YELLOW}📖 Документация:${NC}"
echo -e "  ${GREEN}README.md${NC}               - главная документация"
echo -e "  ${GREEN}PORTS_CONFIGURATION.md${NC}  - настройка портов"
echo ""
echo -e "${GREEN}🚀 Готово! Запустите: ${CYAN}./manage.sh${NC}"
echo ""
