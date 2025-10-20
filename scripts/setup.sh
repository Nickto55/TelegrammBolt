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

# Проверка версии Python
check_python_version() {
    log "Проверка версии Python..."
    
    if ! command -v python3 &> /dev/null; then
        error "Python 3 не найден. Установите Python 3."
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    log "Обнаружена версия Python: $PYTHON_VERSION"
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 9 ]]; then
        error "Требуется Python 3.9 или выше. Обнаружено: $PYTHON_VERSION"
    fi
    
    if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 13 ]]; then
        warn "⚠️  Обнаружен Python 3.13+. Для максимальной совместимости рекомендуется Python 3.11 или 3.12."
        warn "📚 При возникновении ошибок смотрите: TROUBLESHOOTING.md → Python 3.13"
        warn "🔧 Установка продолжится с использованием python-telegram-bot>=21.0"
        echo
        
        # Проверка интерактивного режима
        if [[ -t 0 ]]; then
            read -p "Продолжить с Python $PYTHON_VERSION? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                error "Установка отменена. Установите Python 3.11 или 3.12 и запустите скрипт снова."
            fi
        else
            log "Автоматический режим: продолжаем установку с Python $PYTHON_VERSION"
            sleep 2
        fi
    fi
    
    success "Версия Python совместима"
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
    log "Это может занять некоторое время..."
    
    # Установка с обработкой ошибок для Python 3.13
    if sudo -u telegrambot .venv/bin/pip install -r requirements.txt; then
        success "Python окружение настроено"
    else
        error "Ошибка установки зависимостей. Проверьте TROUBLESHOOTING.md"
    fi
    
    # Проверка установки telegram
    log "Проверка установки python-telegram-bot..."
    if sudo -u telegrambot .venv/bin/pip list | grep -q "python-telegram-bot"; then
        local tg_version=$(sudo -u telegrambot .venv/bin/pip list | grep python-telegram-bot | awk '{print $2}')
        success "python-telegram-bot установлен: версия $tg_version"
    else
        warn "python-telegram-bot не обнаружен. Возможна проблема совместимости."
    fi
}

# Установка прав на файлы
set_permissions() {
    local bot_dir="/opt/telegrambot"
    
    log "Установка прав доступа..."
    sudo chown -R telegrambot:telegrambot "$bot_dir"
    sudo chmod +x "$bot_dir/start_bot.sh"
    
    success "Права доступа установлены"
}

# Установка службы
setup_service() {
    local bot_dir="/opt/telegrambot"
    local service_file="/etc/systemd/system/telegrambot.service"
    
    # Проверка Docker окружения
    if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        warn "⚠️  Обнаружено Docker окружение"
        warn "Docker контейнеры обычно не используют systemd"
        warn "Пропускаем создание службы. Запускайте бота командой:"
        echo "   cd /opt/telegrambot && .venv/bin/python bot.py"
        return 0
    fi
    
    # Проверка переменной окружения для пропуска
    if [ ! -z "$SKIP_SERVICE" ]; then
        warn "SKIP_SERVICE установлен, пропускаем создание службы"
        return 0
    fi
    
    log "Установка службы..."
    
    # Проверяем наличие systemd
    if command -v systemctl &> /dev/null; then
        log "Обнаружен systemd, установка systemd службы..."
        
        # Копирование файла службы
        sudo cp "$bot_dir/telegrambot.service" "$service_file"
        
        # Перезагрузка systemd
        sudo systemctl daemon-reload
        
        # Включение службы
        sudo systemctl enable telegrambot.service
        
        success "Systemd служба установлена и включена"
    else
        warn "systemd не обнаружен, создание init.d скрипта..."
        
        # Создание init.d скрипта
        sudo bash -c 'cat > /etc/init.d/telegrambot << '\''INITEOF'\''
#!/bin/sh
### BEGIN INIT INFO
# Provides:          telegrambot
# Required-Start:    $remote_fs $syslog $network
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: TelegrammBolt Telegram Bot
### END INIT INFO

PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC="TelegrammBolt"
NAME=telegrambot
DAEMON=/opt/telegrambot/.venv/bin/python
DAEMON_ARGS="/opt/telegrambot/bot.py"
PIDFILE=/var/run/$NAME.pid
USER=telegrambot
WORKDIR=/opt/telegrambot

[ -x "$DAEMON" ] || exit 0

. /lib/lsb/init-functions

do_start() {
    start-stop-daemon --start --quiet --pidfile $PIDFILE --chuid $USER \
        --background --make-pidfile --chdir $WORKDIR \
        --exec $DAEMON -- $DAEMON_ARGS || return 2
}

do_stop() {
    start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 --pidfile $PIDFILE
    RETVAL="$?"
    rm -f $PIDFILE
    return "$RETVAL"
}

case "$1" in
  start)
    log_daemon_msg "Starting $DESC" "$NAME"
    do_start
    case "$?" in
        0|1) log_end_msg 0 ;;
        2) log_end_msg 1 ;;
    esac
    ;;
  stop)
    log_daemon_msg "Stopping $DESC" "$NAME"
    do_stop
    case "$?" in
        0|1) log_end_msg 0 ;;
        2) log_end_msg 1 ;;
    esac
    ;;
  status)
    status_of_proc "$DAEMON" "$NAME" && exit 0 || exit $?
    ;;
  restart|force-reload)
    log_daemon_msg "Restarting $DESC" "$NAME"
    do_stop
    case "$?" in
      0|1)
        do_start
        case "$?" in
            0) log_end_msg 0 ;;
            *) log_end_msg 1 ;;
        esac
        ;;
      *) log_end_msg 1 ;;
    esac
    ;;
  *)
    echo "Usage: $0 {start|stop|status|restart}" >&2
    exit 3
    ;;
esac
:
INITEOF'
        
        sudo chmod +x /etc/init.d/telegrambot
        
        # Регистрация службы
        if command -v update-rc.d &> /dev/null; then
            sudo update-rc.d telegrambot defaults
        elif command -v chkconfig &> /dev/null; then
            sudo chkconfig --add telegrambot
        fi
        
        success "Init.d служба установлена"
    fi
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
    local is_docker=0
    
    # Проверка Docker окружения
    if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        is_docker=1
    fi
    
    echo
    echo "============================================================"
    success "🎉 Установка TelegrammBolt завершена успешно!"
    echo
    echo -e "${YELLOW}📋 Дальнейшие шаги:${NC}"
    echo
    echo "1. Настройте конфигурацию бота:"
    echo "   nano /opt/telegrambot/ven_bot.json"
    echo "   - Замените YOUR_BOT_TOKEN_HERE на токен вашего бота"
    echo "   - Замените YOUR_TELEGRAM_ID_HERE на ваш Telegram ID"
    echo
    echo "2. (Опционально) Настройте SMTP для отправки email:"
    echo "   nano /opt/telegrambot/smtp_config.json"
    echo
    
    if [ $is_docker -eq 1 ]; then
        echo -e "${BLUE}🐳 Docker окружение обнаружено${NC}"
        echo
        echo "3. Запустите бота:"
        echo "   cd /opt/telegrambot"
        echo "   .venv/bin/python bot.py"
        echo
        echo "   Или в фоне:"
        echo "   nohup .venv/bin/python bot.py > bot.log 2>&1 &"
        echo
        echo "4. Проверьте статус:"
        echo "   ps aux | grep bot.py"
        echo
        echo "5. Просмотр логов:"
        echo "   tail -f bot.log"
        echo
        echo -e "${YELLOW}🔧 Полезные команды:${NC}"
        echo "   - Остановка бота:     pkill -f bot.py"
        echo "   - Проверка процесса:  ps aux | grep bot.py"
    elif command -v systemctl &> /dev/null; then
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
    else
        echo "3. Запустите службу бота:"
        echo "   sudo service telegrambot start"
        echo "   или: sudo /etc/init.d/telegrambot start"
        echo
        echo "4. Проверьте статус службы:"
        echo "   sudo service telegrambot status"
        echo "   или: sudo /etc/init.d/telegrambot status"
        echo
        echo -e "${YELLOW}🔧 Полезные команды:${NC}"
        echo "   - Перезапуск бота:    sudo service telegrambot restart"
        echo "   - Остановка бота:     sudo service telegrambot stop"
    fi
    
    echo "   - Ручной запуск:      cd /opt/telegrambot && sudo -u telegrambot .venv/bin/python bot.py"
    echo
    echo -e "${YELLOW}📚 Получение токена и ID:${NC}"
    echo "   - Токен бота: https://t.me/BotFather (команда /newbot)"
    echo "   - Ваш Telegram ID: https://t.me/userinfobot (команда /start)"
    echo
    echo -e "${YELLOW}📖 Документация:${NC}"
    echo "   - README.md - Главная документация"
    echo "   - INSTALLATION.md - Полное руководство по установке"
    echo "   - TROUBLESHOOTING.md - Решение проблем (включая Python 3.13)"
    echo "   - CHEATSHEET.md - Шпаргалка команд"
    echo
    echo "============================================================"
}

# Основная функция
main() {
    echo "🚀 TelegrammBolt - Установка на Ubuntu/Debian"
    echo "============================================================"
    echo
    
    check_system
    check_python_version
    update_system
    create_bot_user
    clone_repository
    setup_python_env
    set_permissions
    setup_service
    setup_config
    show_final_instructions
}

# Запуск основной функции
main "$@"