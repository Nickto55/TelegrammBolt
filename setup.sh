#!/bin/bash
#
# TelegrammBolt - Полный установочный скрипт с интерактивной настройкой
# Версия: 2.1
# Автор: Nickto55
# Дата: 20 октября 2025
#
################################################################################

set -e  # Остановка при любой ошибке
set -u  # Ошибка при использовании неинициализированных переменных
set -o pipefail  # Ошибка в любой части pipeline

# Обработчик ошибок
trap 'error_handler $? $LINENO' ERR

error_handler() {
    local exit_code=$1
    local line_number=$2
    echo ""
    error "Ошибка на строке $line_number (код: $exit_code)"
    echo ""
    warn "Установка прервана. Для отладки:"
    echo "  - Проверьте логи выше"
    echo "  - Запустите скрипт снова"
    echo "  - Обратитесь в поддержку: https://github.com/Nickto55/TelegrammBolt/issues"
    echo ""
    exit $exit_code
}

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
    echo -e "${GREEN}[OK]${NC} $1"
}

section() {
    echo ""
    echo -e "${CYAN}===============================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}===============================================${NC}"
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
BOT_USERNAME=""
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
    
    # Проверка что мы не в реальном root аккаунте
    if [ "$HOME" = "/root" ] && [ "$SUDO_USER" = "" ]; then
        warn "Вы запустили скрипт из-под root аккаунта"
        warn "Рекомендуется использовать: sudo ./setup.sh"
    fi
}

# ============================================
# Проверка системы
# ============================================
check_system() {
    section "Проверка системы"
    
    log "Проверка операционной системы..."
    
    # Проверка доступности интернета
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        error "Нет подключения к интернету! Проверьте сетевые настройки."
    fi
    
    if ! command -v lsb_release &> /dev/null; then
        warn "lsb_release не найден. Установка..."
        if ! apt-get update -qq; then
            error "Не удалось обновить список пакетов. Проверьте /etc/apt/sources.list"
        fi
        if ! apt-get install -y lsb-release; then
            error "Не удалось установить lsb-release"
        fi
    fi
    
    DISTRIB=$(lsb_release -si)
    VERSION=$(lsb_release -sr)
    
    success "Обнаружена система: $DISTRIB $VERSION"
    
    if [[ "$DISTRIB" != "Ubuntu" && "$DISTRIB" != "Debian" ]]; then
        error "Поддерживаются только Ubuntu и Debian. Обнаружено: $DISTRIB"
    fi
    
    # Проверка версии для Ubuntu
    if [[ "$DISTRIB" == "Ubuntu" ]]; then
        local major_version=$(echo "$VERSION" | cut -d. -f1)
        if [[ $major_version -lt 20 ]]; then
            warn "Обнаружена Ubuntu $VERSION. Рекомендуется Ubuntu 20.04+"
        fi
    fi
    
    # Проверка свободного места (минимум 2GB)
    local free_space=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    if [[ $free_space -lt 2 ]]; then
        error "Недостаточно свободного места: ${free_space}GB (требуется минимум 2GB)"
    fi
    success "Свободное место: ${free_space}GB"
    
    # Проверка RAM (минимум 512MB)
    local total_ram=$(free -m | awk 'NR==2{print $2}')
    if [[ $total_ram -lt 512 ]]; then
        warn "Мало RAM: ${total_ram}MB (рекомендуется минимум 512MB)"
    fi
    log "RAM: ${total_ram}MB"
    
    # Проверка Docker
    if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        warn "Обнаружено Docker окружение"
        DOCKER_ENV=true
    else
        DOCKER_ENV=false
    fi
    
    # Проверка архитектуры
    local arch=$(uname -m)
    if [[ "$arch" != "x86_64" && "$arch" != "aarch64" ]]; then
        warn "Необычная архитектура: $arch (может быть несовместимость)"
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
    
    # Попытка исправить сломанные пакеты
    if ! apt-get update -qq 2>/dev/null; then
        warn "Стандартное обновление не удалось. Исправление..."
        apt-get update --fix-missing -qq || {
            error "Не удалось обновить список пакетов. Возможные причины:
  - Нет интернета
  - Неправильные репозитории в /etc/apt/sources.list
  - Проблемы с apt
  
Попробуйте вручную: sudo apt-get update"
        }
    fi
    
    log "Установка системных зависимостей..."
    
    local packages=(
        "python3"
        "python3-pip"
        "python3-venv"
        "git"
        "curl"
        "wget"
        "unzip"
        "build-essential"
        "nginx"
        "certbot"
        "python3-certbot-nginx"
        "jq"
        "openssl"
        "ca-certificates"
    )
    
    local failed_packages=()
    
    for pkg in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $pkg"; then
            log "Установка: $pkg"
            if ! apt-get install -y -qq "$pkg" 2>/dev/null; then
                warn "Не удалось установить: $pkg"
                failed_packages+=("$pkg")
            fi
        else
            log "Уже установлен: $pkg"
        fi
    done
    
    if [ ${#failed_packages[@]} -gt 0 ]; then
        warn "Не удалось установить пакеты: ${failed_packages[*]}"
        warn "Попробуйте установить вручную: sudo apt-get install ${failed_packages[*]}"
        
        # Проверка критичных пакетов
        for critical in "python3" "python3-pip" "python3-venv" "git"; do
            if [[ " ${failed_packages[@]} " =~ " ${critical} " ]]; then
                error "Критичный пакет не установлен: $critical. Установка невозможна."
            fi
        done
    fi
    
    success "Системные зависимости установлены"
}

# ============================================
# Интерактивная настройка - Bot Token
# ============================================
configure_bot_token() {
    section "Настройка Telegram Бота"
    
    # Проверка существующего конфига
    if [ -f "$BOT_DIR/config/ven_bot.json" ]; then
        log "Обнаружен существующий конфиг бота"
        
        # Пытаемся прочитать токен
        if command -v jq &> /dev/null; then
            local existing_token=$(jq -r '.BOT_TOKEN // empty' "$BOT_DIR/config/ven_bot.json" 2>/dev/null)
            if [ ! -z "$existing_token" ] && [ "$existing_token" != "null" ]; then
                echo ""
                echo -ne "Использовать существующий токен (${existing_token:0:20}...)? (Y/n): "
                read -r -n 1 REPLY
                echo
                if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                    BOT_TOKEN="$existing_token"
                    success "Используется существующий токен"
                    return 0
                fi
            fi
        fi
    fi
    
    echo ""
    log "Для работы бота нужен токен от @BotFather"
    log "Как получить токен:"
    echo "  1. Откройте Telegram"
    echo "  2. Найдите @BotFather"
    echo "  3. Отправьте команду: /newbot"
    echo "  4. Следуйте инструкциям"
    echo "  5. Скопируйте токен (формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)"
    echo ""
    
    local attempts=0
    local max_attempts=5
    
    while true; do
        ((attempts++))
        
        if [ $attempts -gt $max_attempts ]; then
            error "Превышено количество попыток ввода токена"
        fi
        
        echo ""
        echo -ne "${PURPLE}[?]${NC} Введите токен бота (попытка $attempts/$max_attempts): "
        read -r BOT_TOKEN
        
        # Убираем возможные пробелы, табы, переводы строк
        BOT_TOKEN=$(echo "$BOT_TOKEN" | tr -d '[:space:]')
        
        if [[ -z "$BOT_TOKEN" ]]; then
            warn "Токен не может быть пустым!"
            continue
        fi
        
        # Проверка длины
        if [ ${#BOT_TOKEN} -lt 30 ]; then
            warn "Токен слишком короткий (${#BOT_TOKEN} символов). Ожидается минимум 30"
            continue
        fi
        
        # Базовая проверка формата
        if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
            warn "Токен имеет неправильный формат!"
            warn "Ожидаемый формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
            warn "Ваш токен: ${BOT_TOKEN:0:50}..."
            echo -ne "Продолжить с этим токеном? (y/n): "
            read -r -n 1 REPLY
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                break
            fi
        else
            # Попытка проверить токен через API
            log "Проверка токена через Telegram API..."
            local api_response=$(curl -s -m 10 "https://api.telegram.org/bot${BOT_TOKEN}/getMe" 2>/dev/null || echo "")
            
            if [ ! -z "$api_response" ]; then
                if echo "$api_response" | grep -q '"ok":true'; then
                    BOT_USERNAME=$(echo "$api_response" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
                    success "Токен валидный! Бот: @$BOT_USERNAME"
                    break
                elif echo "$api_response" | grep -q '"ok":false'; then
                    warn "Telegram API вернул ошибку: токен невалидный"
                    continue
                fi
            else
                warn "Не удалось проверить токен (нет ответа от API)"
                warn "Username бота не получен. Укажите его вручную позже в config/ven_bot.json"
                BOT_USERNAME=""
                echo -ne "Продолжить с этим токеном? (y/n): "
                read -r -n 1 REPLY
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    break
                fi
            fi
        fi
    done
    
    # Если username не получен, попросим ввести вручную
    if [ -z "$BOT_USERNAME" ]; then
        echo ""
        warn "Username бота не был получен автоматически"
        log "Username нужен для Telegram Login Widget в веб-интерфейсе"
        echo ""
        echo -ne "${PURPLE}[?]${NC} Введите username бота (без @, например: MyBot) или пропустите (Enter): "
        read -r BOT_USERNAME
        
        # Убираем @ если пользователь добавил
        BOT_USERNAME=$(echo "$BOT_USERNAME" | tr -d '@' | tr -d '[:space:]')
        
        if [ ! -z "$BOT_USERNAME" ]; then
            success "Username: @$BOT_USERNAME"
        else
            warn "Username не указан. Telegram Login в веб-интерфейсе не будет работать."
            warn "Добавьте позже в config/ven_bot.json: \"BOT_USERNAME\": \"YourBotUsername\""
        fi
    fi
}

# ============================================
# Интерактивная настройка - Admin IDs
# ============================================
configure_admin_ids() {
    # Проверка существующего конфига
    if [ -f "$BOT_DIR/config/ven_bot.json" ]; then
        if command -v jq &> /dev/null; then
            local existing_ids=$(jq -r '.ADMIN_IDS // [] | join(",")' "$BOT_DIR/config/ven_bot.json" 2>/dev/null)
            if [ ! -z "$existing_ids" ] && [ "$existing_ids" != "null" ] && [ "$existing_ids" != "" ]; then
                echo ""
                echo -ne "Использовать существующих админов ($existing_ids)? (Y/n): "
                read -r -n 1 REPLY
                echo
                if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                    ADMIN_IDS="$existing_ids"
                    success "Используются существующие ID админов"
                    return 0
                fi
            fi
        fi
    fi
    
    echo ""
    log "Настройка администраторов бота"
    log "Как узнать свой Telegram ID:"
    echo "  1. Откройте Telegram"
    echo "  2. Найдите @userinfobot"
    echo "  3. Отправьте команду: /start"
    echo "  4. Бот пришлет ваш ID (например: 123456789)"
    echo ""
    
    local attempts=0
    local max_attempts=5
    
    while true; do
        ((attempts++))
        
        if [ $attempts -gt $max_attempts ]; then
            error "Превышено количество попыток ввода ID"
        fi
        
        echo ""
        echo -ne "${PURPLE}[?]${NC} Введите ID администратора(ов) через запятую (попытка $attempts/$max_attempts): "
        read -r ADMIN_IDS
        
        # Убираем пробелы и табы
        ADMIN_IDS=$(echo "$ADMIN_IDS" | tr -d '[:space:]')
        
        if [[ -z "$ADMIN_IDS" ]]; then
            warn "Нужен хотя бы один администратор!"
            continue
        fi
        
        # Проверка формата
        if [[ "$ADMIN_IDS" =~ ^[0-9,]+$ ]]; then
            # Проверка что ID валидные (Telegram ID обычно 9-10 цифр)
            local invalid_ids=()
            IFS=',' read -ra IDS <<< "$ADMIN_IDS"
            for id in "${IDS[@]}"; do
                if [ ${#id} -lt 5 ] || [ ${#id} -gt 15 ]; then
                    invalid_ids+=("$id")
                fi
            done
            
            if [ ${#invalid_ids[@]} -gt 0 ]; then
                warn "Подозрительные ID (слишком короткие/длинные): ${invalid_ids[*]}"
                echo -ne "Продолжить с этими ID? (y/n): "
                read -r -n 1 REPLY
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    continue
                fi
            fi
            
            success "ID администраторов: $ADMIN_IDS"
            break
        else
            warn "Неправильный формат! Используйте только цифры и запятые."
            warn "Пример: 123456789,987654321"
        fi
    done
}

# ============================================
# Интерактивная настройка - SMTP
# ============================================
configure_smtp() {
    section "Настройка Email (опционально)"
    
    # Проверка существующего конфига
    if [ -f "$BOT_DIR/config/smtp_config.json" ]; then
        log "Обнаружен существующий SMTP конфиг"
        if command -v jq &> /dev/null; then
            local existing_server=$(jq -r '.SMTP_SERVER // empty' "$BOT_DIR/config/smtp_config.json" 2>/dev/null)
            if [ ! -z "$existing_server" ]; then
                echo ""
                echo -ne "Использовать существующий SMTP ($existing_server)? (Y/n): "
                read -r -n 1 REPLY
                echo
                if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                    SMTP_ENABLED="yes"
                    success "Используется существующая SMTP конфигурация"
                    return 0
                fi
            fi
        fi
    fi
    
    echo ""
    log "Email используется для отправки отчетов"
    echo ""
    
    echo -ne "${PURPLE}[?]${NC} Настроить Email? (y/n): "
    read -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SMTP_ENABLED="yes"
        
        echo ""
        log "Популярные SMTP серверы:"
        echo "  Gmail:     smtp.gmail.com (порт 587)"
        echo "  Yandex:    smtp.yandex.ru (порт 587)"
        echo "  Mail.ru:   smtp.mail.ru (порт 587)"
        echo "  Outlook:   smtp-mail.outlook.com (порт 587)"
        echo ""
        
        # SMTP сервер
        while true; do
            echo -ne "SMTP сервер: "
            read -r SMTP_SERVER
            SMTP_SERVER=$(echo "$SMTP_SERVER" | xargs)
            
            if [[ -z "$SMTP_SERVER" ]]; then
                warn "SMTP сервер не может быть пустым"
                continue
            fi
            
            # Базовая проверка формата
            if [[ "$SMTP_SERVER" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                break
            else
                warn "Неправильный формат сервера. Ожидается: smtp.example.com"
            fi
        done
        
        # SMTP порт
        while true; do
            echo -ne "SMTP порт (обычно 587 или 465): "
            read -r SMTP_PORT
            SMTP_PORT=${SMTP_PORT:-587}
            
            if [[ "$SMTP_PORT" =~ ^[0-9]+$ ]] && [ "$SMTP_PORT" -gt 0 ] && [ "$SMTP_PORT" -lt 65536 ]; then
                break
            else
                warn "Неправильный порт. Используйте число от 1 до 65535"
            fi
        done
        
        # Email адрес
        while true; do
            echo -ne "Email адрес: "
            read -r SMTP_USER
            SMTP_USER=$(echo "$SMTP_USER" | xargs)
            
            if [[ -z "$SMTP_USER" ]]; then
                warn "Email не может быть пустым"
                continue
            fi
            
            # Проверка формата email
            if [[ "$SMTP_USER" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                break
            else
                warn "Неправильный формат email. Ожидается: user@example.com"
            fi
        done
        
        # Пароль
        while true; do
            echo -ne "Email пароль (не будет отображаться): "
            read -r -s SMTP_PASSWORD
            echo ""
            
            if [[ -z "$SMTP_PASSWORD" ]]; then
                warn "Пароль не может быть пустым"
                continue
            fi
            
            if [ ${#SMTP_PASSWORD} -lt 4 ]; then
                warn "Пароль слишком короткий"
                continue
            fi
            
            break
        done
        
        success "SMTP настроен: $SMTP_SERVER:$SMTP_PORT ($SMTP_USER)"
        
        # Предупреждение для Gmail
        if [[ "$SMTP_SERVER" == *"gmail"* ]]; then
            warn "Для Gmail нужно использовать 'Пароль приложения', а не обычный пароль!"
            warn "Создайте пароль приложения: https://myaccount.google.com/apppasswords"
        fi
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
        
        # Порт
        while true; do
            echo ""
            echo -ne "Порт для веб-интерфейса (по умолчанию 5000, Enter для 5000): "
            read -r WEB_PORT
            WEB_PORT=${WEB_PORT:-5000}
            
            # Проверка что порт - число
            if [[ ! "$WEB_PORT" =~ ^[0-9]+$ ]]; then
                warn "Порт должен быть числом!"
                continue
            fi
            
            # Проверка диапазона
            if [ "$WEB_PORT" -lt 1024 ]; then
                warn "Порт $WEB_PORT < 1024 (требуются права root)"
            elif [ "$WEB_PORT" -gt 65535 ]; then
                warn "Порт $WEB_PORT > 65535 (недопустимо)"
                continue
            fi
            
            # Проверка что порт свободен
            if ss -tlnp 2>/dev/null | grep -q ":$WEB_PORT "; then
                warn "Порт $WEB_PORT уже используется!"
                ss -tlnp 2>/dev/null | grep ":$WEB_PORT " || true
                echo -ne "Использовать этот порт в любом случае? (y/n): "
                read -r -n 1 REPLY
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    continue
                fi
            fi
            
            break
        done
        
        success "Веб-интерфейс будет доступен на порту $WEB_PORT"
        
        # HTTPS
        echo ""
        log "==================================================="
        log "Настройка HTTPS (опционально)"
        log "==================================================="
        echo ""
        log "Варианты настройки SSL/HTTPS:"
        echo ""
        echo "  1. Let's Encrypt (требуется домен)"
        echo "     - Бесплатный SSL сертификат"
        echo "     - Требуется доменное имя (example.com)"
        echo "     - DNS должен указывать на этот сервер"
        echo "     - Автоматическое обновление сертификата"
        echo ""
        echo "  2. Самоподписанный сертификат"
        echo "     - Работает без домена"
        echo "     - Браузер покажет предупреждение безопасности"
        echo "     - Подходит для локального использования/тестирования"
        echo ""
        echo "  3. Без HTTPS (только HTTP)"
        echo "     - Без шифрования"
        echo "     - НЕ рекомендуется для продакшена"
        echo "     - Подходит для локальной сети"
        echo ""
        warn "ВАЖНО: Для удаленного доступа рекомендуется HTTPS!"
        echo ""
        log "Бесплатные домены: DuckDNS (duckdns.org), No-IP (noip.com), Freenom"
        echo ""
        
        echo -ne "${PURPLE}[?]${NC} Выберите вариант (1-Let's Encrypt / 2-Самоподписанный / N-Без HTTPS): "
        read -r HTTPS_CHOICE
        
        case "${HTTPS_CHOICE}" in
            1)
                HTTPS_ENABLED="letsencrypt"
                echo ""
                
                while true; do
                    echo -ne "Введите доменное имя (например: bot.example.com): "
                    read -r DOMAIN_NAME
                    DOMAIN_NAME=$(echo "$DOMAIN_NAME" | xargs | tr '[:upper:]' '[:lower:]')
                    
                    if [[ -z "$DOMAIN_NAME" ]]; then
                        warn "Доменное имя не может быть пустым"
                        echo -ne "Пропустить HTTPS? (y/n): "
                        read -r -n 1 REPLY
                        echo
                        if [[ $REPLY =~ ^[Yy]$ ]]; then
                            HTTPS_ENABLED="no"
                            break
                        fi
                        continue
                    fi
                    
                    # Проверка формата домена
                    if [[ ! "$DOMAIN_NAME" =~ ^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$ ]]; then
                        warn "Неправильный формат домена!"
                        warn "Ожидается: example.com или subdomain.example.com"
                        continue
                    fi
                    
                    # Проверка что домен не localhost/IP
                    if [[ "$DOMAIN_NAME" == "localhost" ]] || [[ "$DOMAIN_NAME" =~ ^[0-9.]+$ ]]; then
                        warn "Let's Encrypt не работает с localhost или IP адресами!"
                        warn "Используйте вариант 2 (самоподписанный сертификат)"
                        continue
                    fi
                    
                    success "Let's Encrypt будет настроен для $DOMAIN_NAME"
                    break
                done
                ;;
            2)
                HTTPS_ENABLED="selfsigned"
                echo ""
                log "Будет создан самоподписанный SSL сертификат"
                warn "!!! Браузер будет показывать предупреждение безопасности"
                log "Это нормально для локального использования"
                warn "Для обхода предупреждения в Chrome: введите 'thisisunsafe'"
                success "Самоподписанный сертификат будет создан"
                ;;
            *)
                HTTPS_ENABLED="no"
                warn "HTTPS отключен. Данные передаются БЕЗ шифрования!"
                warn "Не рекомендуется для удаленного доступа!"
                log "Веб-интерфейс будет доступен по HTTP"
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
        
        if ! useradd --system --shell /bin/bash --home "$BOT_DIR" --create-home "$BOT_USER" 2>&1 | tee /tmp/useradd.log; then
            # Попытка без --create-home если не сработало
            if ! useradd --system --shell /bin/bash --home "$BOT_DIR" "$BOT_USER"; then
                cat /tmp/useradd.log
                error "Не удалось создать пользователя $BOT_USER"
            fi
        fi
        
        success "Пользователь $BOT_USER создан"
    else
        log "Пользователь $BOT_USER уже существует"
        
        # Проверка домашней директории
        local user_home=$(getent passwd "$BOT_USER" | cut -d: -f6)
        if [ "$user_home" != "$BOT_DIR" ]; then
            warn "Домашняя директория пользователя: $user_home (ожидается $BOT_DIR)"
        fi
    fi
    
    # Проверка что пользователь создан
    if ! id "$BOT_USER" &>/dev/null; then
        error "Пользователь $BOT_USER не существует после создания!"
    fi
}

# ============================================
# Клонирование репозитория
# ============================================
clone_repository() {
    section "Установка файлов"
    
    local repo_url="https://github.com/Nickto55/TelegrammBolt.git"
    
    # Проверка доступности GitHub
    if ! ping -c 1 github.com &> /dev/null; then
        error "GitHub недоступен. Проверьте интернет или DNS настройки."
    fi
    
    if [ -d "$BOT_DIR/.git" ]; then
        log "Обнаружен существующий репозиторий"
        
        # Сохраняем конфиги перед обновлением
        local backup_dir="/tmp/telegrambot_backup_$(date +%s)"
        mkdir -p "$backup_dir"
        
        if [ -d "$BOT_DIR/config" ]; then
            log "Резервное копирование конфигов..."
            cp -r "$BOT_DIR/config" "$backup_dir/" 2>/dev/null || true
        fi
        
        if [ -d "$BOT_DIR/data" ]; then
            log "Резервное копирование данных..."
            cp -r "$BOT_DIR/data" "$backup_dir/" 2>/dev/null || true
        fi
        
        log "Обновление репозитория..."
        cd "$BOT_DIR"
        
        # Сброс локальных изменений
        if ! sudo -u "$BOT_USER" git fetch origin 2>/dev/null; then
            warn "Не удалось обновить из удаленного репозитория"
        fi
        
        sudo -u "$BOT_USER" git reset --hard origin/main 2>/dev/null || {
            warn "Не удалось сбросить к origin/main. Попытка pull..."
            sudo -u "$BOT_USER" git pull || warn "Git pull не удался"
        }
        
        # Восстанавливаем конфиги
        if [ -d "$backup_dir/config" ]; then
            log "Восстановление конфигов..."
            cp -r "$backup_dir/config/"* "$BOT_DIR/config/" 2>/dev/null || true
        fi
        
        if [ -d "$backup_dir/data" ]; then
            log "Восстановление данных..."
            cp -r "$backup_dir/data/"* "$BOT_DIR/data/" 2>/dev/null || true
        fi
        
        rm -rf "$backup_dir"
        success "Репозиторий обновлен"
    else
        log "Клонирование репозитория..."
        
        # Удаляем если директория существует но это не git репо
        if [ -d "$BOT_DIR" ]; then
            warn "Директория $BOT_DIR существует. Создание резервной копии..."
            mv "$BOT_DIR" "${BOT_DIR}_old_$(date +%s)"
        fi
        
        # Клонирование с проверкой
        if ! git clone --depth 1 "$repo_url" "$BOT_DIR" 2>&1 | tee /tmp/git_clone.log; then
            cat /tmp/git_clone.log
            error "Не удалось клонировать репозиторий. Проверьте доступ к GitHub."
        fi
        
        chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"
        success "Репозиторий клонирован"
    fi
    
    # Проверка что клонирование успешно
    if [ ! -f "$BOT_DIR/requirements.txt" ]; then
        error "Репозиторий клонирован неполностью. requirements.txt не найден."
    fi
    
    success "Файлы установлены в $BOT_DIR"
}

# ============================================
# Создание конфигурационных файлов
# ============================================
create_config_files() {
    section "Создание конфигурационных файлов"
    
    cd "$BOT_DIR"
    
    # Создаем директории если их нет
    log "Создание структуры директорий..."
    mkdir -p config bot web data photos/temp logs
    
    # __init__.py для пакетов
    log "Создание __init__.py файлов..."
    touch config/__init__.py
    touch bot/__init__.py
    touch web/__init__.py
    
    # Проверка что bot.py и другие файлы существуют
    if [ ! -f "bot/bot.py" ]; then
        error "bot/bot.py не найден! Проверьте что репозиторий склонирован правильно."
    fi
    
    if [ ! -f "web/web_app.py" ] && [ "$WEB_ENABLED" == "yes" ]; then
        warn "web/web_app.py не найден! Веб-интерфейс может не работать."
    fi
    
    # ven_bot.json
    log "Создание config/ven_bot.json..."
    
    # Преобразуем ADMIN_IDS в JSON массив
    local admin_ids_json="["
    IFS=',' read -ra IDS <<< "$ADMIN_IDS"
    for i in "${!IDS[@]}"; do
        admin_ids_json+="${IDS[$i]}"
        if [ $i -lt $((${#IDS[@]} - 1)) ]; then
            admin_ids_json+=", "
        fi
    done
    admin_ids_json+="]"
    
    cat > config/ven_bot.json << EOF
{
    "BOT_TOKEN": "$BOT_TOKEN",
    "BOT_USERNAME": "$BOT_USERNAME",
    "ADMIN_IDS": $admin_ids_json,
    "WEB_ENABLED": $([ "$WEB_ENABLED" == "yes" ] && echo "true" || echo "false"),
    "WEB_PORT": $WEB_PORT,
    "LOG_LEVEL": "INFO",
    "TIMEZONE": "Europe/Moscow"
}
EOF
    
    if [ ! -f "config/ven_bot.json" ]; then
        error "Не удалось создать config/ven_bot.json"
    fi
    
    chown "$BOT_USER:$BOT_USER" config/ven_bot.json
    chmod 600 config/ven_bot.json
    success "Конфиг бота создан"
    
    # smtp_config.json (если настроен)
    if [ "$SMTP_ENABLED" == "yes" ]; then
        log "Создание config/smtp_config.json..."
        cat > config/smtp_config.json << EOF
{
    "SMTP_SERVER": "$SMTP_SERVER",
    "SMTP_PORT": $SMTP_PORT,
    "SMTP_USER": "$SMTP_USER",
    "SMTP_PASSWORD": "$SMTP_PASSWORD",
    "FROM_EMAIL": "$SMTP_USER",
    "USE_TLS": true,
    "USE_SSL": false
}
EOF
        
        if [ ! -f "config/smtp_config.json" ]; then
            error "Не удалось создать config/smtp_config.json"
        fi
        
        chown "$BOT_USER:$BOT_USER" config/smtp_config.json
        chmod 600 config/smtp_config.json
        success "SMTP конфиг создан"
    fi
    
    # Инициализация пустых JSON файлов
    log "Создание файлов данных..."
    
    [ ! -f "data/bot_data.json" ] && echo '{}' > data/bot_data.json
    [ ! -f "data/users_data.json" ] && echo '{}' > data/users_data.json
    [ ! -f "data/chat_data.json" ] && echo '{}' > data/chat_data.json
    [ ! -f "data/watched_dse.json" ] && echo '{}' > data/watched_dse.json
    
    # Проверка JSON файлов
    for json_file in data/*.json; do
        if [ -f "$json_file" ]; then
            if ! python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
                warn "Файл $json_file содержит неправильный JSON. Пересоздание..."
                echo '{}' > "$json_file"
            fi
        fi
    done
    
    chown -R "$BOT_USER:$BOT_USER" data/ photos/ logs/
    chmod 755 data photos logs
    chmod 755 photos/temp
    
    success "Конфигурация завершена"
    
    # Вывод структуры для проверки
    log "Структура проекта:"
    tree -L 2 -a "$BOT_DIR" 2>/dev/null || ls -la "$BOT_DIR"
}

# ============================================
# Установка Python окружения
# ============================================
setup_python_env() {
    section "Установка Python зависимостей"
    
    cd "$BOT_DIR"
    
    # Проверка наличия requirements.txt
    if [ ! -f "requirements.txt" ]; then
        error "requirements.txt не найден в $BOT_DIR"
    fi
    
    # Создание виртуального окружения
    if [ ! -d ".venv" ]; then
        log "Создание виртуального окружения..."
        if ! sudo -u "$BOT_USER" python3 -m venv .venv 2>&1 | tee /tmp/venv_create.log; then
            cat /tmp/venv_create.log
            error "Не удалось создать виртуальное окружение. Проверьте python3-venv."
        fi
    else
        log "Виртуальное окружение уже существует"
    fi
    
    # Проверка что venv создан правильно
    if [ ! -f ".venv/bin/python" ]; then
        error "Виртуальное окружение повреждено. Удалите .venv и запустите снова."
    fi
    
    # Обновление pip
    log "Обновление pip..."
    if ! sudo -u "$BOT_USER" .venv/bin/pip install --upgrade pip setuptools wheel --quiet 2>&1 | tee /tmp/pip_upgrade.log; then
        warn "Не удалось обновить pip. Продолжаем с текущей версией..."
    fi
    
    # Показать версию pip
    local pip_version=$(sudo -u "$BOT_USER" .venv/bin/pip --version | awk '{print $2}')
    log "pip версия: $pip_version"
    
    # Установка зависимостей
    log "Установка зависимостей (это может занять 3-5 минут)..."
    log "Прогресс установки:"
    
    local failed_packages=()
    local installed_count=0
    local total_count=$(wc -l < requirements.txt)
    
    # Попытка установить все сразу
    if sudo -u "$BOT_USER" .venv/bin/pip install -r requirements.txt 2>&1 | tee /tmp/pip_install.log; then
        success "Все зависимости установлены успешно"
    else
        warn "Массовая установка не удалась. Установка по одному..."
        
        # Установка по одному пакету
        while IFS= read -r package; do
            # Пропускаем пустые строки и комментарии
            [[ -z "$package" || "$package" =~ ^[[:space:]]*# ]] && continue
            
            log "[$((++installed_count))/$total_count] Установка: $package"
            
            if ! sudo -u "$BOT_USER" .venv/bin/pip install "$package" --quiet 2>/dev/null; then
                warn "Не удалось установить: $package"
                failed_packages+=("$package")
            fi
        done < requirements.txt
    fi
    
    if [ ${#failed_packages[@]} -gt 0 ]; then
        warn "Не удалось установить следующие пакеты:"
        printf '  - %s\n' "${failed_packages[@]}"
        
        # Проверка критичных пакетов
        for critical in "python-telegram-bot" "flask" "requests"; do
            if [[ " ${failed_packages[@]} " =~ " ${critical}" ]]; then
                error "Критичный пакет не установлен: $critical. Бот не будет работать."
            fi
        done
        
        warn "Некритичные пакеты можно установить позже"
    fi
    
    # Проверка установленных пакетов
    log "Проверка установленных пакетов..."
    
    local tg_version=$(sudo -u "$BOT_USER" .venv/bin/pip list 2>/dev/null | grep python-telegram-bot | awk '{print $2}')
    local flask_version=$(sudo -u "$BOT_USER" .venv/bin/pip list 2>/dev/null | grep -w Flask | awk '{print $2}')
    
    if [ -z "$tg_version" ]; then
        error "python-telegram-bot не установлен!"
    else
        success "python-telegram-bot: v$tg_version"
    fi
    
    if [ ! -z "$flask_version" ]; then
        success "Flask: v$flask_version"
    fi
    
    # Создание файла с версиями для отладки
    log "Сохранение списка установленных пакетов..."
    sudo -u "$BOT_USER" .venv/bin/pip freeze > "$BOT_DIR/installed_packages.txt"
    
    success "Python окружение настроено"
}

# ============================================
# Настройка Nginx
# ============================================
configure_nginx() {
    if [ "$WEB_ENABLED" != "yes" ]; then
        return 0
    fi
    
    section "Настройка Nginx"
    
    # Проверка что nginx установлен
    if ! command -v nginx &> /dev/null; then
        error "Nginx не установлен. Запустите update_system снова."
    fi
    
    local nginx_config="/etc/nginx/sites-available/telegrambot"
    local nginx_enabled="/etc/nginx/sites-enabled/telegrambot"
    
    # Резервная копия существующей конфигурации
    if [ -f "$nginx_config" ]; then
        log "Создание резервной копии конфигурации Nginx..."
        cp "$nginx_config" "${nginx_config}.backup.$(date +%s)"
    fi
    
    log "Создание конфигурации Nginx..."
    
    cat > "$nginx_config" << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME:-_};

    # Защита от больших запросов
    client_max_body_size 50M;
    
    # Таймауты
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
    send_timeout 600;

    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket поддержка (если нужна)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Логи
    access_log /var/log/nginx/telegrambot_access.log;
    error_log /var/log/nginx/telegrambot_error.log;
}
EOF
    
    # Включение сайта
    ln -sf "$nginx_config" "$nginx_enabled"
    
    # Удаление default сайта (с подтверждением)
    if [ -f /etc/nginx/sites-enabled/default ]; then
        log "Удаление default конфигурации Nginx..."
        rm -f /etc/nginx/sites-enabled/default
    fi
    
    # Проверка конфигурации
    log "Проверка конфигурации Nginx..."
    if ! nginx -t 2>&1 | tee /tmp/nginx_test.log; then
        error "Ошибка в конфигурации Nginx! См. /tmp/nginx_test.log
        
Откатите конфигурацию:
  sudo mv ${nginx_config}.backup.* $nginx_config
  sudo nginx -t
  sudo systemctl reload nginx"
    fi
    
    # Перезагрузка Nginx
    log "Перезагрузка Nginx..."
    if ! systemctl reload nginx; then
        warn "Не удалось перезагрузить Nginx. Пробуем restart..."
        if ! systemctl restart nginx; then
            error "Не удалось запустить Nginx. Проверьте: sudo systemctl status nginx"
        fi
    fi
    
    # Проверка что Nginx запущен
    if systemctl is-active --quiet nginx; then
        success "Nginx настроен и запущен"
    else
        error "Nginx не запущен. Проверьте: sudo systemctl status nginx"
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
        
        # Проверка DNS
        log "Проверка DNS для $DOMAIN_NAME..."
        local server_ip=$(curl -s -m 5 ifconfig.me 2>/dev/null || curl -s -m 5 icanhazip.com 2>/dev/null || echo "unknown")
        local domain_ip=$(dig +short "$DOMAIN_NAME" 2>/dev/null | tail -n1)
        
        if [ -z "$domain_ip" ]; then
            warn "Не удалось получить IP адрес для домена $DOMAIN_NAME"
            warn "Убедитесь что DNS настроен правильно!"
        elif [ "$server_ip" != "$domain_ip" ]; then
            warn "DNS домена $DOMAIN_NAME ($domain_ip) не совпадает с IP сервера ($server_ip)"
            warn "Let's Encrypt может не сработать!"
        else
            success "DNS проверка OK: $DOMAIN_NAME -> $server_ip"
        fi
        
        echo ""
        log "Требования для Let's Encrypt:"
        echo "  - Домен должен указывать на этот сервер"
        echo "  - Порт 80 должен быть открыт"
        echo "  - Nginx должен быть запущен"
        echo ""
        
        echo -ne "Продолжить получение сертификата? (y/n): "
        read -r -n 1 REPLY
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Проверка что порт 80 доступен
            if ! ss -tlnp | grep -q ':80'; then
                error "Порт 80 не прослушивается. Nginx не запущен?"
            fi
            
            log "Запрос сертификата для $DOMAIN_NAME..."
            
            # Попытка получить сертификат
            if certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --register-unsafely-without-email --redirect 2>&1 | tee /tmp/certbot.log; then
                success "HTTPS настроен для $DOMAIN_NAME"
                
                # Проверка автообновления
                if ! systemctl list-timers | grep -q certbot; then
                    log "Настройка автообновления сертификата..."
                    systemctl enable certbot.timer 2>/dev/null || true
                fi
            else
                cat /tmp/certbot.log
                warn "Не удалось получить сертификат. Возможные причины:"
                echo "  - DNS не указывает на этот сервер"
                echo "  - Порт 80 закрыт файрволом"
                echo "  - Домен уже имеет слишком много сертификатов"
                echo "  - Проблемы с Let's Encrypt сервером"
                echo ""
                log "Веб-интерфейс будет доступен по HTTP"
                log "Попробуйте позже: sudo certbot --nginx -d $DOMAIN_NAME"
            fi
        else
            log "HTTPS пропущен. Можно настроить позже:"
            echo "  sudo certbot --nginx -d $DOMAIN_NAME"
        fi
        
    elif [ "$HTTPS_ENABLED" == "selfsigned" ]; then
        # Самоподписанный сертификат
        log "Создание самоподписанного SSL сертификата..."
        
        # Проверка openssl
        if ! command -v openssl &> /dev/null; then
            error "OpenSSL не установлен. Установите: sudo apt-get install openssl"
        fi
        
        local ssl_dir="/etc/nginx/ssl"
        mkdir -p "$ssl_dir"
        
        # Резервная копия старых сертификатов
        if [ -f "$ssl_dir/selfsigned.crt" ]; then
            mv "$ssl_dir/selfsigned.crt" "$ssl_dir/selfsigned.crt.old.$(date +%s)"
            mv "$ssl_dir/selfsigned.key" "$ssl_dir/selfsigned.key.old.$(date +%s)"
        fi
        
        # Генерация сертификата
        log "Генерация RSA ключа и сертификата..."
        if openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$ssl_dir/selfsigned.key" \
            -out "$ssl_dir/selfsigned.crt" \
            -subj "/C=RU/ST=State/L=City/O=TelegrammBolt/CN=localhost" \
            2>&1 | tee /tmp/openssl.log; then
            
            chmod 600 "$ssl_dir/selfsigned.key"
            chmod 644 "$ssl_dir/selfsigned.crt"
            
            # Проверка созданных файлов
            if [ ! -f "$ssl_dir/selfsigned.key" ] || [ ! -f "$ssl_dir/selfsigned.crt" ]; then
                error "Сертификат не создан. Проверьте /tmp/openssl.log"
            fi
            
            # Вывод информации о сертификате
            log "Информация о сертификате:"
            openssl x509 -in "$ssl_dir/selfsigned.crt" -noout -subject -dates 2>/dev/null || true
            
            # Обновляем конфиг nginx
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
            warn "!!! Браузер покажет предупреждение - это нормально"
            log "Для доступа: https://$(curl -s ifconfig.me 2>/dev/null || echo 'ваш-IP')"
        else
            error "Не удалось создать сертификат"
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
    
    # Проверка наличия systemd
    if ! command -v systemctl &> /dev/null; then
        warn "systemd не найден. Служба не будет установлена."
        warn "Запускайте бота вручную: cd $BOT_DIR && .venv/bin/python bot/bot.py"
        return 0
    fi
    
    log "Создание systemd службы..."
    
    # Резервная копия существующей службы
    if [ -f "$SERVICE_FILE" ]; then
        cp "$SERVICE_FILE" "${SERVICE_FILE}.backup.$(date +%s)"
    fi
    
    # Проверка что Python executable существует
    if [ ! -f "$BOT_DIR/.venv/bin/python" ]; then
        error "Python не найден в .venv! Проверьте установку виртуального окружения."
    fi
    
    # Проверка что bot.py существует
    if [ ! -f "$BOT_DIR/bot/bot.py" ]; then
        error "bot/bot.py не найден! Проверьте структуру проекта."
    fi
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=TelegrammBolt Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BOT_DIR/.venv/bin/python $BOT_DIR/bot/bot.py
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Безопасность
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$BOT_DIR

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegrambot

[Install]
WantedBy=multi-user.target
EOF
    
    if [ ! -f "$SERVICE_FILE" ]; then
        error "Не удалось создать файл службы $SERVICE_FILE"
    fi
    
    # Проверка синтаксиса service файла
    if ! systemd-analyze verify "$SERVICE_FILE" 2>/tmp/service_verify.log; then
        warn "Предупреждения в service файле:"
        cat /tmp/service_verify.log || true
    fi
    
    log "Перезагрузка systemd..."
    systemctl daemon-reload
    
    log "Включение автозапуска..."
    if ! systemctl enable telegrambot.service 2>&1 | tee /tmp/systemctl_enable.log; then
        cat /tmp/systemctl_enable.log
        warn "Не удалось включить автозапуск. Служба может не запускаться при загрузке."
    fi
    
    success "Служба установлена и добавлена в автозагрузку"
    
    # Если включен веб-интерфейс, создаем службу для него
    if [ "$WEB_ENABLED" == "yes" ]; then
        log "Создание systemd службы для веб-интерфейса..."
        
        local WEB_SERVICE_FILE="/etc/systemd/system/telegrambot-web.service"
        
        # Резервная копия
        if [ -f "$WEB_SERVICE_FILE" ]; then
            cp "$WEB_SERVICE_FILE" "${WEB_SERVICE_FILE}.backup.$(date +%s)"
        fi
        
        cat > "$WEB_SERVICE_FILE" << EOF
[Unit]
Description=TelegrammBolt Web Interface
After=network.target network-online.target telegrambot.service
Wants=network-online.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$BOT_DIR/.venv/bin/gunicorn -w 4 -b 127.0.0.1:$WEB_PORT --timeout 120 --access-logfile $BOT_DIR/logs/web_access.log --error-logfile $BOT_DIR/logs/web_error.log web.web_app:app
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Безопасность
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$BOT_DIR

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegrambot-web

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        
        if systemctl enable telegrambot-web.service 2>&1 | tee /tmp/systemctl_enable_web.log; then
            success "Служба веб-интерфейса установлена"
        else
            warn "Не удалось включить автозапуск веб-интерфейса"
            cat /tmp/systemctl_enable_web.log || true
        fi
    fi
}

# ============================================
# Установка прав
# ============================================
set_permissions() {
    section "Установка прав доступа"
    
    log "Установка владельца файлов..."
    if ! chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR" 2>&1 | tee /tmp/chown.log; then
        cat /tmp/chown.log
        warn "Не удалось установить права для всех файлов"
    fi
    
    chmod 755 "$BOT_DIR"
    
    # Защита конфигов
    log "Защита конфиденциальных файлов..."
    if [ -f "$BOT_DIR/config/ven_bot.json" ]; then
        chmod 600 "$BOT_DIR/config/ven_bot.json"
    fi
    
    if [ -f "$BOT_DIR/config/smtp_config.json" ]; then
        chmod 600 "$BOT_DIR/config/smtp_config.json"
    fi
    
    # Права на директории
    chmod 755 "$BOT_DIR/data" 2>/dev/null || true
    chmod 755 "$BOT_DIR/photos" 2>/dev/null || true
    chmod 755 "$BOT_DIR/logs" 2>/dev/null || true
    
    # Проверка прав
    local owner=$(stat -c '%U' "$BOT_DIR/config/ven_bot.json" 2>/dev/null || echo "unknown")
    local perms=$(stat -c '%a' "$BOT_DIR/config/ven_bot.json" 2>/dev/null || echo "unknown")
    
    if [ "$owner" == "$BOT_USER" ] && [ "$perms" == "600" ]; then
        success "Права доступа установлены корректно"
    else
        warn "Проверьте права: owner=$owner (ожидается $BOT_USER), perms=$perms (ожидается 600)"
    fi
}

# ============================================
# Финальная информация
# ============================================
show_final_info() {
    section "Установка завершена!"
    
    echo ""
    success "TelegrammBolt успешно установлен!"
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo ""
    echo -e "${GREEN}[+] Директория:${NC} $BOT_DIR"
    echo -e "${GREEN}[+] Пользователь:${NC} $BOT_USER"
    echo -e "${GREEN}[+] Токен бота:${NC} ${BOT_TOKEN:0:20}..."
    echo -e "${GREEN}[+] Админы:${NC} $ADMIN_IDS"
    
    if [ "$WEB_ENABLED" == "yes" ]; then
        echo ""
        echo -e "${GREEN}[+] Веб-интерфейс:${NC} Включен"
        
        local server_ip=$(curl -s -m 5 ifconfig.me 2>/dev/null || curl -s -m 5 icanhazip.com 2>/dev/null || hostname -I | awk '{print $1}')
        
        if [ "$HTTPS_ENABLED" == "letsencrypt" ]; then
            echo -e "${GREEN}[+] URL:${NC} https://$DOMAIN_NAME"
            echo -e "${GREEN}[+] SSL:${NC} Let's Encrypt"
            echo -e "${GREEN}[+] Автообновление:${NC} certbot.timer"
        elif [ "$HTTPS_ENABLED" == "selfsigned" ]; then
            echo -e "${GREEN}[+] URL:${NC} https://$server_ip"
            echo -e "${YELLOW}[!] SSL:${NC} Самоподписанный сертификат"
            echo -e "${YELLOW}[!] ${NC} Браузер покажет предупреждение - это нормально"
            echo -e "${YELLOW}[!] ${NC} В Chrome введите: thisisunsafe"
        else
            echo -e "${GREEN}[+] URL:${NC} http://$server_ip:$WEB_PORT"
            echo -e "${YELLOW}[!] ${NC} HTTP (без шифрования)"
        fi
        
        echo ""
        echo -e "${CYAN}Логины для веб-интерфейса:${NC}"
        echo "  Логин: admin"
        echo "  Пароль: (установите при первом входе)"
    fi
    
    if [ "$SMTP_ENABLED" == "yes" ]; then
        echo ""
        echo -e "${GREEN}[+] Email:${NC} Настроен ($SMTP_USER)"
    fi
    
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo ""
    echo -e "${YELLOW}Управление ботом:${NC}"
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
        echo ""
        echo "  # Последние 100 строк логов:"
        echo "  sudo journalctl -u telegrambot -n 100"
        
        if [ "$WEB_ENABLED" == "yes" ]; then
            echo ""
            echo -e "${YELLOW}Управление веб-интерфейсом:${NC}"
            echo ""
            echo "  # Запустить веб:"
            echo "  sudo systemctl start telegrambot-web"
            echo ""
            echo "  # Остановить веб:"
            echo "  sudo systemctl stop telegrambot-web"
            echo ""
            echo "  # Перезапустить веб:"
            echo "  sudo systemctl restart telegrambot-web"
            echo ""
            echo "  # Статус веб:"
            echo "  sudo systemctl status telegrambot-web"
            echo ""
            echo "  # Логи веб:"
            echo "  sudo journalctl -u telegrambot-web -f"
            echo ""
            echo "  # Запустить всё сразу:"
            echo "  sudo systemctl start telegrambot telegrambot-web"
        fi
    else
        echo "  # Запустить бота (Docker):"
        echo "  cd $BOT_DIR && .venv/bin/python bot/bot.py"
    fi
    
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo ""
    echo -e "${YELLOW}Полезные команды:${NC}"
    echo ""
    echo "  # Проверка конфигурации:"
    echo "  cat $BOT_DIR/config/ven_bot.json"
    echo ""
    echo "  # Диагностика системы:"
    echo "  cd $BOT_DIR && .venv/bin/python utils.py check"
    echo ""
    echo "  # Список пользователей:"
    echo "  cd $BOT_DIR && .venv/bin/python utils.py users"
    echo ""
    echo "  # Обновление бота:"
    echo "  cd $BOT_DIR && git pull && .venv/bin/pip install -r requirements.txt"
    if [ "$DOCKER_ENV" != "true" ]; then
        echo "  sudo systemctl restart telegrambot"
    fi
    
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo ""
    echo -e "${YELLOW}Документация:${NC}"
    echo "  - README.md - Основная информация"
    echo "  - UTILS.md - Утилиты диагностики"
    echo "  - SECURITY.md - Безопасность"
    echo "  - GitHub: https://github.com/Nickto55/TelegrammBolt"
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo ""
    
    # Тест запуска
    if [ "$DOCKER_ENV" != "true" ]; then
        echo -ne "Запустить бота сейчас? (Y/n): "
        read -r -n 1 REPLY
        echo
        
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            log "Запуск бота..."
            
            if systemctl start telegrambot 2>&1 | tee /tmp/start_bot.log; then
                sleep 3
                
                if systemctl is-active --quiet telegrambot; then
                    success "Бот успешно запущен!"
                    echo ""
                    log "Проверка статуса:"
                    systemctl status telegrambot --no-pager --lines=10
                    echo ""
                    success "Бот работает! Проверьте Telegram."
                    
                    # Запуск веб-интерфейса
                    if [ "$WEB_ENABLED" == "yes" ]; then
                        echo ""
                        log "Запуск веб-интерфейса..."
                        
                        if systemctl start telegrambot-web 2>&1 | tee /tmp/start_web.log; then
                            sleep 2
                            
                            if systemctl is-active --quiet telegrambot-web; then
                                success "Веб-интерфейс запущен!"
                                echo ""
                                
                                local server_ip=$(curl -s -m 5 ifconfig.me 2>/dev/null || curl -s -m 5 icanhazip.com 2>/dev/null || hostname -I | awk '{print $1}')
                                
                                if [ "$HTTPS_ENABLED" == "letsencrypt" ]; then
                                    success "Веб-интерфейс доступен: https://$DOMAIN_NAME"
                                elif [ "$HTTPS_ENABLED" == "selfsigned" ]; then
                                    success "Веб-интерфейс доступен: https://$server_ip"
                                else
                                    success "Веб-интерфейс доступен: http://$server_ip:$WEB_PORT"
                                fi
                            else
                                warn "Веб-интерфейс не запустился. Проверьте:"
                                echo "  sudo journalctl -u telegrambot-web -n 50"
                            fi
                        else
                            cat /tmp/start_web.log
                            warn "Не удалось запустить веб-интерфейс"
                        fi
                    fi
                else
                    error "Бот не запустился. Проверьте логи:
  sudo journalctl -u telegrambot -n 50
  
Возможные причины:
  - Неправильный токен бота
  - Проблемы с зависимостями
  - Ошибка в конфигурации
  
Попробуйте запустить вручную для диагностики:
  cd $BOT_DIR
  sudo -u $BOT_USER .venv/bin/python bot/bot.py"
                fi
            else
                cat /tmp/start_bot.log
                warn "Не удалось запустить службу. Попробуйте вручную:"
                echo "  sudo systemctl start telegrambot"
                echo "  sudo journalctl -u telegrambot -f"
            fi
        fi
    else
        echo ""
        warn "Docker режим. Запустите бота вручную:"
        echo "  cd $BOT_DIR"
        echo "  .venv/bin/python bot/bot.py"
    fi
    
    echo ""
    success "Готово! Бот установлен и настроен."
    echo ""
    
    # Финальные предупреждения
    if [ "$HTTPS_ENABLED" == "no" ] && [ "$WEB_ENABLED" == "yes" ]; then
        warn "ВАЖНО: Веб-интерфейс работает без HTTPS!"
        warn "Данные передаются в открытом виде. Настройте SSL для безопасности."
    fi
    
    if [ "$SMTP_ENABLED" == "yes" ]; then
        log "Проверьте работу email: отправьте тестовый отчет через веб-интерфейс"
    fi
    
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
