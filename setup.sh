#!/bin/bash
# TelegrammBolt - Установочный скрипт для Ubuntu/Debian
# Этот скрипт автоматически устанавливает и настраивает Telegram бота

set -e  # Остановка при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Проверка системы
check_system() {
    log "Проверка операционной системы..."
    
    if ! command -v lsb_release &> /dev/null; then
        warn "lsb_release не найден. Попытка установить..."
        sudo apt-get update
        sudo apt-get install -y lsb-release
    fi
    
    DISTRIB=$(lsb_release -si)
    VERSION=$(lsb_release -sr)
    
    log "Обнаружена система: $DISTRIB $VERSION"
    
    if [[ "$DISTRIB" != "Ubuntu" && "$DISTRIB" != "Debian" ]]; then
        error "Поддерживаются только Ubuntu и Debian. Обнаружено: $DISTRIB"
    fi
}

# Обновление пакетов системы
update_system() {
    log "Обновление списка пакетов..."
    sudo apt-get update
    
    log "Установка необходимых системных пакетов..."
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        unzip \
        software-properties-common \
        build-essential
}

# Создание пользователя для бота
create_bot_user() {
    if ! id "telegrambot" &>/dev/null; then
        log "Создание пользователя telegrambot..."
        sudo useradd --system --shell /bin/bash --home /opt/telegrambot --create-home telegrambot
        success "Пользователь telegrambot создан"
    else
        log "Пользователь telegrambot уже существует"
    fi
}

# Клонирование репозитория
clone_repository() {
    local repo_url="https://github.com/Nickto55/TelegrammBolt.git"
    local target_dir="/opt/telegrambot"
    
    log "Клонирование репозитория..."
    
    if [ -d "$target_dir/.git" ]; then
        log "Обновление существующего репозитория..."
        cd "$target_dir"
        sudo -u telegrambot git pull
    else
        log "Клонирование репозитория из GitHub..."
        sudo rm -rf "$target_dir"
        sudo git clone "$repo_url" "$target_dir"
        sudo chown -R telegrambot:telegrambot "$target_dir"
    fi
    
    success "Репозиторий успешно клонирован в $target_dir"
}

# Создание виртуального окружения и установка зависимостей
setup_python_env() {
    local bot_dir="/opt/telegrambot"
    
    log "Настройка Python окружения..."
    cd "$bot_dir"
    
    # Создание виртуального окружения
    if [ ! -d ".venv" ]; then
        log "Создание виртуального окружения..."
        sudo -u telegrambot python3 -m venv .venv
    fi
    
    # Установка зависимостей напрямую через pip из виртуального окружения
    log "Обновление pip..."
    sudo -u telegrambot .venv/bin/pip install --upgrade pip
    
    log "Установка Python зависимостей..."
    sudo -u telegrambot .venv/bin/pip install -r requirements.txt
    
    success "Python окружение настроено"
}

# Установка прав на файлы
set_permissions() {
    local bot_dir="/opt/telegrambot"
    
    log "Установка прав доступа..."
    sudo chown -R telegrambot:telegrambot "$bot_dir"
    sudo chmod +x "$bot_dir/start_bot.sh"
    
    success "Права доступа установлены"
}

# Установка systemd службы
setup_systemd_service() {
    local bot_dir="/opt/telegrambot"
    local service_file="/etc/systemd/system/telegrambot.service"
    
    log "Установка systemd службы..."
    
    # Копирование файла службы
    sudo cp "$bot_dir/telegrambot.service" "$service_file"
    
    # Перезагрузка systemd
    sudo systemctl daemon-reload
    
    # Включение службы
    sudo systemctl enable telegrambot.service
    
    success "Systemd служба установлена и включена"
}

# Создание конфигурационных файлов
setup_config() {
    local bot_dir="/opt/telegrambot"
    
    log "Настройка конфигурации..."
    cd "$bot_dir"
    
    # Создание шаблонов конфигурации, если они не существуют
    if [ ! -f "ven_bot.json" ]; then
        log "Создание шаблона ven_bot.json..."
        sudo -u telegrambot bash -c 'cat > ven_bot.json << EOF
{
  "BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
  "ADMIN_IDS": ["YOUR_TELEGRAM_ID_HERE"]
}
EOF'
    fi
    
    if [ ! -f "smtp_config.json" ]; then
        log "Создание шаблона smtp_config.json..."
        sudo -u telegrambot bash -c 'cat > smtp_config.json << EOF
{
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": 587,
  "SMTP_USER": "your_email@gmail.com",
  "SMTP_PASSWORD": "your_app_password",
  "FROM_NAME": "Бот учета ДСЕ"
}
EOF'
    fi
    
    success "Конфигурационные файлы созданы"
}

# Показать инструкции по настройке
show_final_instructions() {
    echo
    echo "============================================================"
    success "🎉 Установка TelegrammBolt завершена успешно!"
    echo
    echo -e "${YELLOW}📋 Дальнейшие шаги:${NC}"
    echo
    echo "1. Настройте конфигурацию бота:"
    echo "   sudo nano /opt/telegrambot/ven_bot.json"
    echo "   - Замените YOUR_BOT_TOKEN_HERE на токен вашего бота"
    echo "   - Замените YOUR_TELEGRAM_ID_HERE на ваш Telegram ID"
    echo
    echo "2. (Опционально) Настройте SMTP для отправки email:"
    echo "   sudo nano /opt/telegrambot/smtp_config.json"
    echo
    echo "3. Запустите службу бота:"
    echo "   sudo systemctl start telegrambot"
    echo
    echo "4. Проверьте статус службы:"
    echo "   sudo systemctl status telegrambot"
    echo
    echo "5. Просмотр логов:"
    echo "   sudo journalctl -u telegrambot -f"
    echo
    echo -e "${YELLOW}🔧 Полезные команды:${NC}"
    echo "   - Перезапуск бота:    sudo systemctl restart telegrambot"
    echo "   - Остановка бота:     sudo systemctl stop telegrambot"
    echo "   - Отключение автозапуска: sudo systemctl disable telegrambot"
    echo "   - Ручной запуск:      cd /opt/telegrambot && sudo -u telegrambot .venv/bin/python bot.py"
    echo
    echo -e "${YELLOW}📚 Получение токена и ID:${NC}"
    echo "   - Токен бота: https://t.me/BotFather (команда /newbot)"
    echo "   - Ваш Telegram ID: https://t.me/userinfobot (команда /start)"
    echo
    echo "============================================================"
}

# Основная функция
main() {
    echo "🚀 TelegrammBolt - Установка на Ubuntu/Debian"
    echo "============================================================"
    echo
    
    check_system
    update_system
    create_bot_user
    clone_repository
    setup_python_env
    set_permissions
    setup_systemd_service
    setup_config
    show_final_instructions
}

# Запуск основной функции
main "$@"