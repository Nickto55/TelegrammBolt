#!/bin/bash
################################################################################
# TelegrammBolt - Полный установочный скрипт с интерактивной настройкой
# Версия: 2.0
# Автор: Nickto55
# Дата: 17 октября 2025
################################################################################

set -e  # Остановка при любой ошибке

# ============================================
# Цвета для вывода
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# ============================================
# Функции для вывода
# ============================================
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

section() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
    echo ""
}

prompt() {
    echo -e "${PURPLE}[?]${NC} $1"
}

# ============================================
# Глобальные переменные
# ============================================
BOT_DIR="/opt/telegrambot"
BOT_USER="telegrambot"
SERVICE_FILE="/etc/systemd/system/telegrambot.service"
PYTHON_VERSION=""
BOT_TOKEN=""
ADMIN_IDS=""
SMTP_ENABLED="no"
SMTP_SERVER=""
SMTP_PORT=""
SMTP_USER=""
SMTP_PASSWORD=""
WEB_ENABLED="yes"
WEB_PORT="5000"
HTTPS_ENABLED="no"
DOMAIN_NAME=""

# ============================================
# Баннер
# ============================================
show_banner() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗  ║
║   ╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗ ║
║      ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║ ║
║      ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║ ║
║      ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║ ║
║      ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ║
║                                                               ║
║             TELEGRAMMBOLT - Автоматический установщик         ║
║                         Версия 2.0                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo ""
}

# ============================================
# Проверка прав root
# ============================================
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Этот скрипт должен запускаться с правами root (используйте sudo)"
    fi
}

# ============================================
# Проверка системы
# ============================================
check_system() {
    section "Проверка системы"
    
    log "Проверка операционной системы..."
    
    if ! command -v lsb_release &> /dev/null; then
        warn "lsb_release не найден. Установка..."
        apt-get update -qq
        apt-get install -y lsb-release
    fi
    
    DISTRIB=$(lsb_release -si)
    VERSION=$(lsb_release -sr)
    
    success "Обнаружена система: $DISTRIB $VERSION"
    
    if [[ "$DISTRIB" != "Ubuntu" && "$DISTRIB" != "Debian" ]]; then
        error "Поддерживаются только Ubuntu и Debian. Обнаружено: $DISTRIB"
    fi
    
    # Проверка Docker
    if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        warn "Обнаружено Docker окружение"
        DOCKER_ENV=true
    else
        DOCKER_ENV=false
    fi
}

# ============================================
# Проверка Python
# ============================================
check_python() {
    section "Проверка Python"
    
    if ! command -v python3 &> /dev/null; then
        error "Python 3 не найден. Установите Python 3.9+"
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    success "Python версия: $PYTHON_VERSION"
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 9 ]]; then
        error "Требуется Python 3.9+. Обнаружено: $PYTHON_VERSION"
    fi
    
    if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 13 ]]; then
        warn "Обнаружен Python 3.13+. Возможны проблемы совместимости."
        warn "Рекомендуется Python 3.11 или 3.12"
        sleep 2
    fi
}

# ============================================
# Обновление системы
# ============================================
update_system() {
    section "Обновление системы"
    
    log "Обновление списка пакетов..."
    apt-get update -qq
    
    log "Установка системных зависимостей..."
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        unzip \
        build-essential \
        nginx \
        certbot \
        python3-certbot-nginx \
        jq
    
    success "Системные зависимости установлены"
}

# ============================================
# Интерактивная настройка - Bot Token
# ============================================
configure_bot_token() {
    section "Настройка Telegram Бота"
    
    echo ""
    log "Для работы бота нужен токен от @BotFather"
    log "Как получить токен:"
    echo "  1. Откройте Telegram"
    echo "  2. Найдите @BotFather"
    echo "  3. Отправьте команду: /newbot"
    echo "  4. Следуйте инструкциям"
    echo "  5. Скопируйте токен (формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)"
    echo ""
    
    while true; do
        echo ""
        echo -ne "${PURPLE}[?]${NC} Введите токен бота: "
        read -r BOT_TOKEN
        
        # Убираем возможные пробелы в начале и конце
        BOT_TOKEN=$(echo "$BOT_TOKEN" | xargs)
        
        if [[ -z "$BOT_TOKEN" ]]; then
            error "Токен не может быть пустым!"
            continue
        fi
        
        # Базовая проверка формата токена
        if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
            warn "Токен имеет неправильный формат!"
            warn "Ожидаемый формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
            echo -ne "Продолжить с этим токеном? (y/n): "
            read -r -n 1 REPLY
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                break
            fi
        else
            success "Токен принят"
            break
        fi
    done
}

# ============================================
# Интерактивная настройка - Admin IDs
# ============================================
configure_admin_ids() {
    echo ""
    log "Настройка администраторов бота"
    log "Как узнать свой Telegram ID:"
    echo "  1. Откройте Telegram"
    echo "  2. Найдите @userinfobot"
    echo "  3. Отправьте команду: /start"
    echo "  4. Бот пришлет ваш ID (например: 123456789)"
    echo ""
    
    while true; do
        echo ""
        echo -ne "${PURPLE}[?]${NC} Введите ID администратора(ов) через запятую: "
        read -r ADMIN_IDS
        
        # Убираем пробелы
        ADMIN_IDS=$(echo "$ADMIN_IDS" | xargs)
        
        if [[ -z "$ADMIN_IDS" ]]; then
            error "Нужен хотя бы один администратор!"
            continue
        fi
        
        # Проверка формата
        if [[ "$ADMIN_IDS" =~ ^[0-9,\ ]+$ ]]; then
            success "ID администраторов: $ADMIN_IDS"
            break
        else
            warn "Неправильный формат! Используйте только цифры и запятые."
        fi
    done
}

# ============================================
# Интерактивная настройка - SMTP (опционально)
# ============================================
configure_smtp() {
    section "Настройка Email (опционально)"
    
    echo ""
    log "Email используется для отправки отчетов"
    echo ""
    
    echo -ne "${PURPLE}[?]${NC} Настроить Email? (y/n): "
    read -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SMTP_ENABLED="yes"
        
        echo ""
        echo -ne "SMTP сервер (например: smtp.gmail.com): "
        read -r SMTP_SERVER
        
        echo -ne "SMTP порт (обычно 587): "
        read -r SMTP_PORT
        SMTP_PORT=${SMTP_PORT:-587}
        
        echo -ne "Email адрес: "
        read -r SMTP_USER
        
        echo -ne "Email пароль: "
        read -r -s SMTP_PASSWORD
        echo ""
        
        success "SMTP настроен"
    else
        log "SMTP пропущен. Можно настроить позже в config/smtp_config.json"
    fi
}

# ============================================
# Интерактивная настройка - Веб-интерфейс
# ============================================
configure_web() {
    section "Настройка веб-интерфейса"
    
    echo ""
    echo -ne "${PURPLE}[?]${NC} Включить веб-интерфейс? (Y/n): "
    read -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        WEB_ENABLED="yes"
        
        echo ""
        echo -ne "Порт для веб-интерфейса (по умолчанию 5000): "
        read -r WEB_PORT
        WEB_PORT=${WEB_PORT:-5000}
        
        success "Веб-интерфейс будет доступен на порту $WEB_PORT"
        
        # HTTPS
        echo ""
        log "═══════════════════════════════════════════════════════"
        log "Настройка HTTPS (опционально)"
        log "═══════════════════════════════════════════════════════"
        echo ""
        log "Варианты настройки SSL/HTTPS:"
        echo ""
        echo "  1. Let's Encrypt (требуется домен)"
        echo "     • Бесплатный SSL сертификат"
        echo "     • Требуется доменное имя (example.com)"
        echo "     • DNS должен указывать на этот сервер"
        echo ""
        echo "  2. Самоподписанный сертификат"
        echo "     • Работает без домена"
        echo "     • Браузер покажет предупреждение безопасности"
        echo "     • Подходит для локального использования"
        echo ""
        echo "  3. Без HTTPS (только HTTP)"
        echo "     • Без шифрования"
        echo "     • Для тестирования или локальной сети"
        echo ""
        log "Бесплатные домены: DuckDNS (duckdns.org), No-IP (noip.com)"
        echo ""
        
        echo -ne "${PURPLE}[?]${NC} Выберите вариант (1-Let's Encrypt / 2-Самоподписанный / N-Без HTTPS): "
        read -r HTTPS_CHOICE
        
        case "${HTTPS_CHOICE}" in
            1)
                HTTPS_ENABLED="letsencrypt"
                echo ""
                echo -ne "Введите доменное имя (например: bot.example.com): "
                read -r DOMAIN_NAME
                
                if [[ -z "$DOMAIN_NAME" ]]; then
                    warn "Доменное имя не указано. HTTPS будет пропущен."
                    HTTPS_ENABLED="no"
                else
                    success "Let's Encrypt будет настроен для $DOMAIN_NAME"
                fi
                ;;
            2)
                HTTPS_ENABLED="selfsigned"
                echo ""
                log "Будет создан самоподписанный SSL сертификат"
                warn "⚠️  Браузер будет показывать предупреждение безопасности"
                log "Это нормально для локального использования"
                success "Самоподписанный сертификат будет создан"
                ;;
            *)
                HTTPS_ENABLED="no"
                log "HTTPS отключен. Веб-интерфейс будет доступен по HTTP"
                ;;
        esac
    else
        WEB_ENABLED="no"
        log "Веб-интерфейс отключен"
    fi
}

# ============================================
# Создание пользователя
# ============================================
create_bot_user() {
    section "Создание пользователя"
    
    if ! id "$BOT_USER" &>/dev/null; then
        log "Создание пользователя $BOT_USER..."
        useradd --system --shell /bin/bash --home "$BOT_DIR" --create-home "$BOT_USER"
        success "Пользователь $BOT_USER создан"
    else
        log "Пользователь $BOT_USER уже существует"
    fi
}

# ============================================
# Клонирование репозитория
# ============================================
clone_repository() {
    section "Установка файлов"
    
    local repo_url="https://github.com/Nickto55/TelegrammBolt.git"
    
    if [ -d "$BOT_DIR/.git" ]; then
        log "Обновление существующего репозитория..."
        cd "$BOT_DIR"
        sudo -u "$BOT_USER" git pull
    else
        log "Клонирование репозитория..."
        rm -rf "$BOT_DIR"
        git clone "$repo_url" "$BOT_DIR"
        chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"
    fi
    
    success "Файлы установлены в $BOT_DIR"
}

# ============================================
# Создание конфигурационных файлов
# ============================================
create_config_files() {
    section "Создание конфигурационных файлов"
    
    cd "$BOT_DIR"
    
    # Создаем директорию data если её нет
    mkdir -p data
    mkdir -p data/photos
    
    # ven_bot.json
    log "Создание data/ven_bot.json..."
    cat > data/ven_bot.json << EOF
{
    "bot_token": "$BOT_TOKEN",
    "admin_ids": [$(echo $ADMIN_IDS | sed 's/,/, /g')],
    "web_enabled": $([ "$WEB_ENABLED" == "yes" ] && echo "true" || echo "false"),
    "web_port": $WEB_PORT,
    "data_file": "data/bot_data.json",
    "users_file": "data/users_data.json",
    "photos_dir": "data/photos",
    "debug": false
}
EOF
    
    chown "$BOT_USER:$BOT_USER" data/ven_bot.json
    chmod 600 data/ven_bot.json
    success "Конфиг бота создан"
    
    # smtp_config.json (если настроен)
    if [ "$SMTP_ENABLED" == "yes" ]; then
        log "Создание data/smtp_config.json..."
        cat > data/smtp_config.json << EOF
{
    "smtp_server": "$SMTP_SERVER",
    "smtp_port": $SMTP_PORT,
    "smtp_user": "$SMTP_USER",
    "smtp_password": "$SMTP_PASSWORD",
    "from_email": "$SMTP_USER",
    "use_tls": true
}
EOF
        chown "$BOT_USER:$BOT_USER" data/smtp_config.json
        chmod 600 data/smtp_config.json
        success "SMTP конфиг создан"
    fi
    
    # Инициализация пустых JSON файлов
    echo '{}' > data/bot_data.json
    echo '{}' > data/users_data.json
    chown -R "$BOT_USER:$BOT_USER" data/
    
    success "Конфигурация завершена"
}

# ============================================
# Установка Python окружения
# ============================================
setup_python_env() {
    section "Установка Python зависимостей"
    
    cd "$BOT_DIR"
    
    # Создание виртуального окружения
    if [ ! -d ".venv" ]; then
        log "Создание виртуального окружения..."
        sudo -u "$BOT_USER" python3 -m venv .venv
    fi
    
    # Обновление pip
    log "Обновление pip..."
    sudo -u "$BOT_USER" .venv/bin/pip install --upgrade pip --quiet
    
    # Установка зависимостей
    log "Установка зависимостей (это может занять время)..."
    if sudo -u "$BOT_USER" .venv/bin/pip install -r requirements.txt --quiet; then
        success "Python зависимости установлены"
    else
        error "Ошибка установки зависимостей. Проверьте requirements.txt"
    fi
    
    # Проверка
    local tg_version=$(sudo -u "$BOT_USER" .venv/bin/pip list | grep python-telegram-bot | awk '{print $2}')
    if [ ! -z "$tg_version" ]; then
        success "python-telegram-bot: v$tg_version"
    fi
}

# ============================================
# Настройка Nginx (если включен веб)
# ============================================
configure_nginx() {
    if [ "$WEB_ENABLED" != "yes" ]; then
        return 0
    fi
    
    section "Настройка Nginx"
    
    local nginx_config="/etc/nginx/sites-available/telegrambot"
    local nginx_enabled="/etc/nginx/sites-enabled/telegrambot"
    
    log "Создание конфигурации Nginx..."
    
    cat > "$nginx_config" << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME:-_};

    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Включение сайта
    ln -sf "$nginx_config" "$nginx_enabled"
    
    # Удаление default сайта
    rm -f /etc/nginx/sites-enabled/default
    
    # Проверка конфигурации
    if nginx -t 2>/dev/null; then
        systemctl reload nginx
        success "Nginx настроен"
    else
        warn "Ошибка в конфигурации Nginx"
    fi
}

# ============================================
# Настройка HTTPS
# ============================================
setup_https() {
    if [ "$HTTPS_ENABLED" == "no" ]; then
        return 0
    fi
    
    section "Настройка HTTPS"
    
    if [ "$HTTPS_ENABLED" == "letsencrypt" ]; then
        # Let's Encrypt
        log "Получение SSL сертификата от Let's Encrypt..."
        log "Убедитесь что домен $DOMAIN_NAME указывает на этот сервер!"
        echo ""
        
        echo -ne "Продолжить получение сертификата? (y/n): "
        read -r -n 1 REPLY
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --email "admin@$DOMAIN_NAME"; then
                success "HTTPS настроен для $DOMAIN_NAME"
            else
                warn "Не удалось получить сертификат. Проверьте DNS настройки."
                log "Веб-интерфейс будет доступен по HTTP"
            fi
        else
            log "HTTPS пропущен. Можно настроить позже."
        fi
        
    elif [ "$HTTPS_ENABLED" == "selfsigned" ]; then
        # Самоподписанный сертификат
        log "Создание самоподписанного SSL сертификата..."
        
        local ssl_dir="/etc/nginx/ssl"
        mkdir -p "$ssl_dir"
        
        # Генерация сертификата
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$ssl_dir/selfsigned.key" \
            -out "$ssl_dir/selfsigned.crt" \
            -subj "/C=RU/ST=State/L=City/O=TelegrammBolt/CN=localhost" \
            2>/dev/null
        
        if [ $? -eq 0 ]; then
            chmod 600 "$ssl_dir/selfsigned.key"
            chmod 644 "$ssl_dir/selfsigned.crt"
            
            # Обновляем конфиг nginx для самоподписанного сертификата
            cat > /etc/nginx/sites-available/telegrambot << EOF
server {
    listen 80;
    server_name _;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name _;
    
    ssl_certificate $ssl_dir/selfsigned.crt;
    ssl_certificate_key $ssl_dir/selfsigned.key;
    
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
            
            systemctl restart nginx
            
            success "Самоподписанный SSL сертификат создан"
            warn "⚠️  Браузер покажет предупреждение - это нормально"
            log "Для доступа: https://$(curl -s ifconfig.me 2>/dev/null || echo 'ваш-IP')"
        else
            error "Не удалось создать сертификат"
            log "Веб-интерфейс будет доступен по HTTP"
        fi
    fi
}

# ============================================
# Установка systemd службы
# ============================================
setup_service() {
    if [ "$DOCKER_ENV" == "true" ]; then
        warn "Docker окружение - пропускаем systemd службу"
        return 0
    fi
    
    section "Установка системной службы"
    
    log "Создание systemd службы..."
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=TelegrammBolt Telegram Bot
After=network.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$BOT_DIR/.venv/bin/python $BOT_DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагрузка systemd
    systemctl daemon-reload
    systemctl enable telegrambot.service
    
    success "Служба установлена"
}

# ============================================
# Установка прав
# ============================================
set_permissions() {
    section "Установка прав доступа"
    
    chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"
    chmod 755 "$BOT_DIR"
    chmod 600 "$BOT_DIR/data/ven_bot.json"
    
    if [ -f "$BOT_DIR/data/smtp_config.json" ]; then
        chmod 600 "$BOT_DIR/data/smtp_config.json"
    fi
    
    success "Права доступа установлены"
}

# ============================================
# Финальная информация
# ============================================
show_final_info() {
    section "Установка завершена!"
    
    echo ""
    success "TelegrammBolt успешно установлен!"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}📁 Директория:${NC} $BOT_DIR"
    echo -e "${GREEN}👤 Пользователь:${NC} $BOT_USER"
    echo -e "${GREEN}🤖 Токен бота:${NC} ${BOT_TOKEN:0:20}..."
    echo -e "${GREEN}👨‍💼 Админы:${NC} $ADMIN_IDS"
    
    if [ "$WEB_ENABLED" == "yes" ]; then
        echo ""
        echo -e "${GREEN}🌐 Веб-интерфейс:${NC} Включен"
        
        if [ "$HTTPS_ENABLED" == "letsencrypt" ]; then
            echo -e "${GREEN}🔗 URL:${NC} https://$DOMAIN_NAME"
            echo -e "${GREEN}🔒 SSL:${NC} Let's Encrypt"
        elif [ "$HTTPS_ENABLED" == "selfsigned" ]; then
            local server_ip=$(curl -s ifconfig.me 2>/dev/null || echo "ваш-IP")
            echo -e "${GREEN}🔗 URL:${NC} https://$server_ip"
            echo -e "${YELLOW}🔒 SSL:${NC} Самоподписанный сертификат"
            echo -e "${YELLOW}⚠️  ${NC} Браузер покажет предупреждение - это нормально"
        else
            local server_ip=$(curl -s ifconfig.me 2>/dev/null || echo "ваш-IP")
            echo -e "${GREEN}🔗 URL:${NC} http://$server_ip:$WEB_PORT"
            echo -e "${YELLOW}⚠️  ${NC} HTTP (без шифрования)"
        fi
    fi
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}📝 Управление ботом:${NC}"
    echo ""
    
    if [ "$DOCKER_ENV" != "true" ]; then
        echo "  # Запустить бота:"
        echo "  sudo systemctl start telegrambot"
        echo ""
        echo "  # Остановить бота:"
        echo "  sudo systemctl stop telegrambot"
        echo ""
        echo "  # Перезапустить бота:"
        echo "  sudo systemctl restart telegrambot"
        echo ""
        echo "  # Посмотреть статус:"
        echo "  sudo systemctl status telegrambot"
        echo ""
        echo "  # Посмотреть логи:"
        echo "  sudo journalctl -u telegrambot -f"
    else
        echo "  # Запустить бота (Docker):"
        echo "  cd $BOT_DIR && .venv/bin/python bot.py"
    fi
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}📚 Документация:${NC}"
    echo "  • README.md - Основная информация"
    echo "  • docs/INSTALLATION.md - Полное руководство"
    echo "  • docs/TROUBLESHOOTING.md - Решение проблем"
    echo "  • docs/CHEATSHEET.md - Шпаргалка"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo -ne "Запустить бота сейчас? (Y/n): "
    read -r -n 1 REPLY
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        if [ "$DOCKER_ENV" != "true" ]; then
            log "Запуск бота..."
            systemctl start telegrambot
            sleep 2
            systemctl status telegrambot --no-pager
        else
            log "Запустите бота вручную:"
            echo "  cd $BOT_DIR && .venv/bin/python bot.py"
        fi
    fi
    
    echo ""
    success "Готово! Бот установлен и настроен."
    echo ""
}

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================
main() {
    show_banner
    
    check_root
    check_system
    check_python
    update_system
    
    # Интерактивная настройка
    configure_bot_token
    configure_admin_ids
    configure_smtp
    configure_web
    
    # Установка
    create_bot_user
    clone_repository
    create_config_files
    setup_python_env
    set_permissions
    
    # Веб и HTTPS
    if [ "$WEB_ENABLED" == "yes" ]; then
        configure_nginx
        setup_https
    fi
    
    # Служба
    setup_service
    
    # Финал
    show_final_info
}

# Запуск
main "$@"
