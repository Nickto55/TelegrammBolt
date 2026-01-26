#!/bin/bash

# TelegramBolt Management Panel
# Панель        управления для TelegramBolt с поддержкой веб-терминала

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Пути
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
BOT_SERVICE="telegrambot"
WEB_SERVICE="telegramweb"

# Порты по умолчанию
DEFAULT_WEB_PORT=5000
DEFAULT_TERMINAL_PORT=5001

# Функция очистки экрана и вывода заголовка
show_header() {
    clear
    echo -e "${WHITE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${WHITE}║${NC}        ${WHITE}TelegramBolt Management Panel${NC}               ${CYAN}║${NC}"
    echo -e "${WHITE}║${NC}        ${PURPLE}Панель управления с веб-терминалом${NC}          ${CYAN}║${NC}"
    echo -e "${WHITE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Функция получения статуса сервиса
get_service_status() {
    local service=$1
    if systemctl is-active --quiet $service 2>/dev/null; then
        echo -e "${GREEN}●${NC} Запущен"
    else
        echo -e "${RED}●${NC} Остановлен"
    fi
}

# Функция проверки процесса
check_process() {
    local process=$1
    if pgrep -f "$process" > /dev/null; then
        echo -e "${GREEN}●${NC} Активен"
    else
        echo -e "${RED}●${NC} Неактивен"
    fi
}

# Функция проверки веб-терминала
check_web_terminal() {
    # Проверяем наличие gunicorn с eventlet или socketio
    if pgrep -f "gunicorn.*eventlet.*web.web_app" > /dev/null; then
        echo -e "${GREEN}●${NC} Готов (Gunicorn)"
    elif pgrep -f "python.*web_app.py" > /dev/null; then
        echo -e "${YELLOW}●${NC} Работает (dev режим)"
    else
        echo -e "${RED}●${NC} Остановлен"
    fi
}

# Главное меню
show_menu() {
    show_header
    
    echo -e "${WHITE}┌─ Статус сервисов ────────────────────────────────────────┐${NC}"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  Telegram Bot:  $(get_service_status $BOT_SERVICE)"
    echo -e "${WHITE}│${NC}  Web Interface: $(get_service_status $WEB_SERVICE)"
    echo -e "${WHITE}│${NC}  Web Terminal:  $(check_web_terminal)"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}└───────────────────────────────────────────────────────────┘${NC}"
    echo ""
    
    echo -e "${WHITE}┌─ Управление ──────────────────────────────────────────────┐${NC}"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${WHITE}1.${NC} Запустить все сервисы"
    echo -e "${WHITE}│${NC}  ${WHITE}2.${NC} Остановить все сервисы"
    echo -e "${WHITE}│${NC}  ${WHITE}3.${NC} Перезапустить все сервисы"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${WHITE}4.${NC} Запустить только бота"
    echo -e "${WHITE}│${NC}  ${WHITE}5.${NC} Запустить только веб"
    echo -e "${WHITE}│${NC}  ${WHITE}6.${NC} Запустить веб с терминалом (Gunicorn)"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${WHITE}7.${NC} Просмотр логов бота"
    echo -e "${WHITE}│${NC}  ${WHITE}8.${NC} Просмотр логов веб"
    echo -e "${WHITE}│${NC}  ${WHITE}9.${NC} Проверка статуса"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${WHITE}10.${NC} Обновить проект (git pull)"
    echo -e "${WHITE}│${NC}  ${WHITE}11.${NC} Обновить зависимости"
    echo -e "${WHITE}│${NC}  ${WHITE}12.${NC} Тест веб-терминала"
    echo -e "${WHITE}│${NC}  ${WHITE}13.${NC} Настройка systemd сервиса"
    echo -e "${WHITE}│${NC}  ${WHITE}14.${NC} Проверка и установка библиотек"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${WHITE}15.${NC} Принудительный сброс пароля"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${WHITE}0.${NC} Выход"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}└───────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -n -e "${WHITE}Выберите действие: ${NC}"
}

# Функции управления
start_all() {
    echo -e "${GREEN}Запуск всех сервисов...${NC}"
    sudo systemctl start $BOT_SERVICE
    sudo systemctl start $WEB_SERVICE
    echo -e "${GREEN} Сервисы запущены${NC}"
    sleep 2
}

stop_all() {
    echo -e "${YELLOW}Остановка всех сервисов...${NC}"
    sudo systemctl stop $BOT_SERVICE
    sudo systemctl stop $WEB_SERVICE
    echo -e "${GREEN} Сервисы остановлены${NC}"
    sleep 2
}

restart_all() {
    echo -e "${YELLOW}Перезапуск всех сервисов...${NC}"
    sudo systemctl restart $BOT_SERVICE
    sudo systemctl restart $WEB_SERVICE
    echo -e "${GREEN} Сервисы перезапущены${NC}"
    sleep 2
}

start_bot() {
    echo -e "${GREEN}Запуск Telegram бота...${NC}"
    sudo systemctl start $BOT_SERVICE
    sudo systemctl status $BOT_SERVICE --no-pager -l
    read -p "Нажмите Enter для продолжения..."
}

start_web() {
    echo -e "${GREEN}Запуск веб-интерфейса...${NC}"
    sudo systemctl start $WEB_SERVICE
    sudo systemctl status $WEB_SERVICE --no-pager -l
    read -p "Нажмите Enter для продолжения..."
}

start_web_terminal() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Запуск веб-интерфейса с терминалом (Gunicorn)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Выбор порта
    echo -e "${YELLOW}Выберите порт для запуска:${NC}"
    echo -e "  ${WHITE}1.${NC} Порт 5000 (по умолчанию)"
    echo -e "  ${WHITE}2.${NC} Порт 8080"
    echo -e "  ${WHITE}3.${NC} Порт 3000"
    echo -e "  ${WHITE}4.${NC} Свой порт"
    echo ""
    read -p "Ваш выбор (1-4, Enter=5000): " port_choice
    
    WEB_PORT=$DEFAULT_WEB_PORT
    
    case $port_choice in
        2) WEB_PORT=8080 ;;
        3) WEB_PORT=3000 ;;
        4)
            read -p "Введите номер порта: " custom_port
            if [[ $custom_port =~ ^[0-9]+$ ]] && [ $custom_port -ge 1024 ] && [ $custom_port -le 65535 ]; then
                WEB_PORT=$custom_port
            else
                echo -e "${RED}Неверный порт. Использую 5000${NC}"
                sleep 1
            fi
            ;;
        *) WEB_PORT=5000 ;;
    esac
    
    echo ""
    echo -e "${GREEN}Выбран порт: ${WHITE}$WEB_PORT${NC}"
    echo ""
    
    # Проверка виртуального окружения
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Виртуальное окружение не найдено. Создаём...${NC}"
        python3 -m venv $VENV_DIR
        echo -e "${GREEN} Виртуальное окружение создано${NC}"
    fi
    
    # Активация виртуального окружения
    source $VENV_DIR/bin/activate
    
    # Проверка и установка зависимостей
    echo -e "${CYAN}Проверка зависимостей для веб-терминала...${NC}"
    
    MISSING_DEPS=()
    
    if ! pip show flask-socketio &>/dev/null; then
        MISSING_DEPS+=("flask-socketio")
    fi
    
    if ! pip show python-socketio &>/dev/null; then
        MISSING_DEPS+=("python-socketio")
    fi
    
    if ! pip show eventlet &>/dev/null; then
        MISSING_DEPS+=("eventlet")
    fi
    
    if ! pip show ptyprocess &>/dev/null; then
        MISSING_DEPS+=("ptyprocess")
    fi
    
    if ! pip show gunicorn &>/dev/null; then
        MISSING_DEPS+=("gunicorn")
    fi
    
    if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
        echo -e "${YELLOW}Недостающие пакеты: ${MISSING_DEPS[*]}${NC}"
        echo -e "${YELLOW}Установка зависимостей...${NC}"
        pip install -q --upgrade pip
        pip install -q flask-socketio python-socketio eventlet ptyprocess gunicorn
        echo -e "${GREEN} Все зависимости установлены${NC}"
    else
        echo -e "${GREEN} Все зависимости уже установлены${NC}"
    fi
    
    echo ""
    
    # Остановка старых процессов (включая systemd сервис)
    echo -e "${YELLOW}Остановка старых процессов на порту $WEB_PORT...${NC}"
    sudo systemctl stop telegramweb 2>/dev/null
    sudo lsof -ti:$WEB_PORT | xargs -r kill -9 2>/dev/null
    sleep 1
    echo -e "${GREEN} Порт $WEB_PORT освобожден${NC}"
    echo ""
    
    # Запуск Gunicorn с eventlet
    echo -e "${GREEN}Запуск сервера с поддержкой WebSocket...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Получаем IP адрес сервера
    SERVER_IP=$(hostname -I | awk '{print $1}')
    HOSTNAME=$(hostname)
    
    echo -e "${WHITE}Сервер запущен на порту: ${GREEN}$WEB_PORT${NC}"
    echo ""
    echo -e "${YELLOW}Откройте в браузере один из адресов:${NC}"
    echo -e "  ${GREEN}http://${SERVER_IP}:${WEB_PORT}${NC}"
    if [ ! -z "$HOSTNAME" ]; then
        echo -e "  ${GREEN}http://${HOSTNAME}:${WEB_PORT}${NC}"
    fi
    echo -e "  ${GREEN}http://localhost:${WEB_PORT}${NC} ${YELLOW}(если на этом же компьютере)${NC}"
    echo ""
    echo -e "${CYAN}Веб-терминал:${NC}"
    echo -e "  ${GREEN}http://${SERVER_IP}:${WEB_PORT}/terminal${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Для остановки нажмите Ctrl+C${NC}"
    echo ""
    
    cd $PROJECT_DIR
    gunicorn --worker-class eventlet -w 1 \
        --bind 0.0.0.0:$WEB_PORT \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        web.web_app:app
}

view_bot_logs() {
    echo -e "${CYAN}Логи Telegram бота (Ctrl+C для выхода):${NC}"
    sudo journalctl -u $BOT_SERVICE -f --no-pager
}

view_web_logs() {
    echo -e "${CYAN}Логи веб-интерфейса (Ctrl+C для выхода):${NC}"
    sudo journalctl -u $WEB_SERVICE -f --no-pager
}

check_status() {
    show_header
    echo -e "${BLUE}┌─ Детальный статус ────────────────────────────────────────┐${NC}"
    echo ""
    echo -e "${WHITE}Telegram Bot:${NC}"
    sudo systemctl status $BOT_SERVICE --no-pager -l | head -20
    echo ""
    echo -e "${WHITE}Web Interface:${NC}"
    sudo systemctl status $WEB_SERVICE --no-pager -l | head -20
    echo ""
    echo -e "${WHITE}Процессы:${NC}"
    ps aux | grep -E "python.*bot\.py|python.*web_app\.py|gunicorn.*web\.web_app" | grep -v grep
    echo ""
    echo -e "${WHITE}Порты (используемые):${NC}"
    for PORT in 5000 5001 8080 3000; do
        local PORT_STATUS=$(sudo lsof -i :$PORT 2>/dev/null)
        if [ -n "$PORT_STATUS" ]; then
            echo -e "${GREEN} Порт $PORT:${NC}"
            echo "$PORT_STATUS" | grep -E "gunicorn|python|flask" | awk '{print "  "$1" (PID: "$2")"}'
        fi
    done
    
    # Проверка на свободные порты
    local HAS_RUNNING=false
    for PORT in 5000 5001 8080 3000; do
        if sudo lsof -i :$PORT 2>/dev/null > /dev/null; then
            HAS_RUNNING=true
            break
        fi
    done
    
    if [ "$HAS_RUNNING" = false ]; then
        echo -e "${YELLOW}⚠ Все стандартные порты (5000, 5001, 8080, 3000) свободны${NC}"
    fi
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

update_project() {
    show_header
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Обновление проекта${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Проверка git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}✗ Git не установлен${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    # Проверка наличия git репозитория
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        echo -e "${YELLOW}⚠ Это не git репозиторий${NC}"
        echo -e "${YELLOW}  Обновление через git недоступно${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    # Сохраняем хеш manage.sh до обновления для автоперезапуска
    SCRIPT_PATH="$(readlink -f "$0")"
    OLD_HASH=$(md5sum "$SCRIPT_PATH" 2>/dev/null | awk '{print $1}')
    
    echo -e "${YELLOW}Текущая ветка:${NC} $(git branch --show-current)"
    echo -e "${YELLOW}Последний коммит:${NC} $(git log -1 --oneline)"
    echo ""
    
    # Проверка изменений
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠ Обнаружены локальные изменения:${NC}"
        git status --short
        echo ""
        read -p "Продолжить обновление? Локальные изменения могут быть потеряны (y/n): " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Отменено${NC}"
            read -p "Нажмите Enter для продолжения..."
            return
        fi
    fi
    
    echo -e "${CYAN}Остановка сервисов...${NC}"
    sudo systemctl stop $BOT_SERVICE $WEB_SERVICE 2>/dev/null
    
    echo -e "${CYAN}Обновление кода из репозитория...${NC}"
    git fetch origin
    
    # Показать что будет обновлено
    if [ -n "$(git log HEAD..origin/$(git branch --show-current) --oneline)" ]; then
        echo -e "${GREEN}Доступные обновления:${NC}"
        git log HEAD..origin/$(git branch --show-current) --oneline --decorate --color
        echo ""
    else
        echo -e "${GREEN} Проект уже актуален${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    read -p "Применить обновления? (y/n): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        git pull origin $(git branch --show-current)
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN} Код обновлен${NC}"
            echo ""
            
            # Проверяем, обновился ли manage.sh и перезапускаем его
            NEW_HASH=$(md5sum "$SCRIPT_PATH" 2>/dev/null | awk '{print $1}')
            if [ "$OLD_HASH" != "$NEW_HASH" ]; then
                echo -e "${YELLOW}⚠ manage.sh был обновлён, перезапуск скрипта...${NC}"
                sleep 2
                exec "$SCRIPT_PATH" "$@"
            fi
            
            # Обновление зависимостей
            echo -e "${CYAN}Обновление зависимостей...${NC}"
            if [ -d "$VENV_DIR" ]; then
                source $VENV_DIR/bin/activate
            fi
            pip install -q --upgrade pip
            pip install -q -r requirements.txt --upgrade
            echo -e "${GREEN} Зависимости обновлены${NC}"
            echo ""
            
            # Перезапуск сервисов
            echo -e "${CYAN}Перезапуск сервисов...${NC}"
            sudo systemctl daemon-reload
            sudo systemctl start $BOT_SERVICE $WEB_SERVICE 2>/dev/null
            echo -e "${GREEN} Сервисы перезапущены${NC}"
            echo ""
            
            echo -e "${GREEN} Обновление завершено!${NC}"
        else
            echo -e "${RED}✗ Ошибка при обновлении${NC}"
            echo -e "${YELLOW}Попробуйте вручную: git pull${NC}"
        fi
    else
        echo -e "${YELLOW}Отменено${NC}"
    fi
    
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

update_dependencies() {
    echo -e "${CYAN}Обновление зависимостей...${NC}"
    
    if [ -d "$VENV_DIR" ]; then
        source $VENV_DIR/bin/activate
    fi
    
    pip install --upgrade pip
    pip install -r requirements.txt --upgrade
    
    echo -e "${GREEN} Зависимости обновлены${NC}"
    read -p "Нажмите Enter для продолжения..."
}

test_terminal() {
    show_header
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Тест веб-терминала${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Проверка зависимостей
    echo -e "${YELLOW}Проверка зависимостей:${NC}"
    
    if [ -d "$VENV_DIR" ]; then
        source $VENV_DIR/bin/activate
    fi
    
    packages=("flask-socketio" "python-socketio" "eventlet" "ptyprocess")
    all_ok=true
    
    for pkg in "${packages[@]}"; do
        if pip show ${pkg} &>/dev/null; then
            echo -e "  ${GREEN}${NC} ${pkg}"
        else
            echo -e "  ${RED}✗${NC} ${pkg} - не установлен"
            all_ok=false
        fi
    done
    
    echo ""
    
    # Проверка файлов
    echo -e "${YELLOW}Проверка файлов:${NC}"
    
    files=(
        "web/terminal_manager.py"
        "web/templates/terminal.html"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            echo -e "  ${GREEN}${NC} $file"
        else
            echo -e "  ${RED}✗${NC} $file - не найден"
            all_ok=false
        fi
    done
    
    echo ""
}

reset_user_password() {
    show_header
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Принудительный сброс пароля пользователя${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Активация виртуального окружения
    if [ -d "$VENV_DIR" ]; then
        source $VENV_DIR/bin/activate
    fi
    
    # Запрашиваем email или  ID веб-пользователя
    echo -e "${YELLOW}Введите email или ID веб-пользователя:${NC}"
    read -p "Email/ID: " user_identifier
    
    if [ -z "$user_identifier" ]; then
        echo -e "${RED}Ошибка: Не указан email или ID пользователя${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    # Генерируем новый случайный пароль
    NEW_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12)
    
    if [ -z "$NEW_PASSWORD" ]; then
        # Если openssl недоступен, используем альтернативный способ
        NEW_PASSWORD=$(cat /dev/urandom | tr -dc 'A-Za-z0-9' | fold -w 12 | head -n 1)
    fi
    
    if [ -z "$NEW_PASSWORD" ]; then
        echo -e "${RED}Ошибка: Не удалось сгенерировать новый пароль${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    # Хэшируем новый пароль
    HASHED_PASSWORD=$(python3 -c "
import hashlib
print(hashlib.sha256('$NEW_PASSWORD'.encode()).hexdigest())
")
    
    # Вызываем Python скрипт для обновления пароля
    RESULT=$(python3 -c "
import sys
sys.path.append('$PROJECT_DIR')
from bot.account_linking import find_web_user_by_email, admin_change_password
import os

try:
    # Проверяем, является ли идентификатор числом (web_user_id) или email
    if '$user_identifier'.startswith('web_'):
        # Это web_user_id
        web_user_id = '$user_identifier'
        # Просто попробуем найти пользователя с этим ID
        import json
        linking_file = os.path.join('$PROJECT_DIR', 'data', 'account_linking.json')
        if os.path.exists(linking_file):
            with open(linking_file, 'r', encoding='utf-8') as f:
                linking_data = json.load(f)
            if web_user_id in linking_data.get('web_users', {}):
                user_found = True
            else:
                user_found = False
        else:
            user_found = False
    else:
        # Это email, ищем по email
        web_user_id, user_data = find_web_user_by_email('$user_identifier')
        if web_user_id:
            user_found = True
        else:
            user_found = False
    
    if user_found:
        # Выполняем сброс пароля
        result = admin_change_password(web_user_id, '$HASHED_PASSWORD')
        if result['success']:
            print('SUCCESS:' + web_user_id)
        else:
            print('ERROR:' + result['error'])
    else:
        print('ERROR:Пользователь не найден')
except Exception as e:
    print('ERROR:' + str(e))
")

    if [[ $RESULT == SUCCESS:* ]]; then
        WEB_USER_ID=$(echo $RESULT | cut -d':' -f2)
        echo -e "${GREEN}✓ Пароль успешно сброшен${NC}"
        echo ""
        echo -e "${WHITE}Новые данные для входа:${NC}"
        echo -e "  ${YELLOW}ID веб-пользователя:${NC} $WEB_USER_ID"
        echo -e "  ${YELLOW}Новый пароль:${NC} $NEW_PASSWORD"
        echo ""
        echo -e "${RED}ВАЖНО:${NC} Сохраните этот пароль в надежном месте!"
    else
        ERROR_MSG=$(echo $RESULT | cut -d':' -f2-)
        echo -e "${RED}✗ Ошибка: $ERROR_MSG${NC}"
    fi
    
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

setup_systemd() {
    
    # Проверка интеграции
    echo -e "${YELLOW}Проверка интеграции в web_app.py:${NC}"
    
    if grep -q "from flask_socketio import SocketIO" $PROJECT_DIR/web/web_app.py; then
        echo -e "  ${GREEN}${NC} Flask-SocketIO импортирован"
    else
        echo -e "  ${RED}✗${NC} Flask-SocketIO не импортирован"
        all_ok=false
    fi
    
    if grep -q "socketio.run(app" $PROJECT_DIR/web/web_app.py; then
        echo -e "  ${GREEN}${NC} Приложение использует socketio.run()"
    else
        echo -e "  ${YELLOW}⚠${NC} Приложение может использовать Gunicorn (это нормально)"
    fi
    
    # Проверка роутов
    if grep -q "@app.route('/terminal')" $PROJECT_DIR/web/web_app.py || grep -q "@app.route(\"/terminal\")" $PROJECT_DIR/web/web_app.py; then
        echo -e "  ${GREEN}${NC} Роут /terminal настроен"
    else
        echo -e "  ${RED}✗${NC} Роут /terminal не найден"
        all_ok=false
    fi
    
    echo ""
    
    if $all_ok; then
        echo -e "${GREEN} Все проверки пройдены!${NC}"
        echo -e "${CYAN}Можете запустить веб с терминалом (опция 6)${NC}"
    else
        echo -e "${RED}✗ Обнаружены проблемы${NC}"
        echo -e "${YELLOW}Выполните: pip install -r requirements.txt${NC}"
    fi
    
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

setup_systemd() {
    show_header
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Настройка systemd сервиса для веб-терминала${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    SERVICE_FILE="/etc/systemd/system/telegrambolt-web.service"
    CURRENT_USER=$(whoami)
    
    echo -e "${YELLOW}Будет создан файл: ${WHITE}$SERVICE_FILE${NC}"
    echo -e "${YELLOW}Пользователь: ${WHITE}$CURRENT_USER${NC}"
    echo -e "${YELLOW}Рабочая директория: ${WHITE}$PROJECT_DIR${NC}"
    echo ""
    
    # Выбор порта для systemd сервиса
    echo -e "${CYAN}Выберите порт для веб-интерфейса:${NC}"
    echo -e "  ${WHITE}1.${NC} 5000 (по умолчанию)"
    echo -e "  ${WHITE}2.${NC} 8080"
    echo -e "  ${WHITE}3.${NC} 3000"
    echo -e "  ${WHITE}4.${NC} Другой порт"
    echo ""
    echo -n -e "${WHITE}Выберите порт (1-4): ${NC}"
    read port_choice
    
    case $port_choice in
        1) SYSTEMD_PORT=5000 ;;
        2) SYSTEMD_PORT=8080 ;;
        3) SYSTEMD_PORT=3000 ;;
        4) 
            echo -n -e "${WHITE}Введите номер порта: ${NC}"
            read SYSTEMD_PORT
            ;;
        *) 
            echo -e "${YELLOW}Неверный выбор, используется порт 5000${NC}"
            SYSTEMD_PORT=5000
            ;;
    esac
    
    echo ""
    echo -e "${GREEN} Выбран порт: ${WHITE}$SYSTEMD_PORT${NC}"
    echo ""
    
    read -p "Продолжить? (y/n): " confirm
    
    if [[ $confirm == "y" || $confirm == "Y" ]]; then
        sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=TelegramBolt Web Application with Terminal
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"

ExecStart=$VENV_DIR/bin/gunicorn \\
    --worker-class eventlet \\
    -w 1 \\
    --bind 0.0.0.0:$SYSTEMD_PORT \\
    --access-logfile /var/log/telegrambolt-web.log \\
    --error-logfile /var/log/telegrambolt-web.log \\
    --log-level info \\
    web.web_app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        
        echo ""
        echo -e "${GREEN} Сервис создан с портом $SYSTEMD_PORT${NC}"
        echo ""
        echo -e "${YELLOW}Команды управления:${NC}"
        echo -e "  ${WHITE}sudo systemctl enable telegrambolt-web${NC}  - добавить в автозагрузку"
        echo -e "  ${WHITE}sudo systemctl start telegrambolt-web${NC}   - запустить"
        echo -e "  ${WHITE}sudo systemctl status telegrambolt-web${NC}  - проверить статус"
        echo -e "  ${WHITE}sudo journalctl -u telegrambolt-web -f${NC}  - просмотр логов"
        echo ""
        echo -e "${CYAN}Доступ к веб-интерфейсу: ${WHITE}http://YOUR_IP:$SYSTEMD_PORT${NC}"
        echo ""
    else
        echo -e "${YELLOW}Отменено${NC}"
    fi
    
    read -p "Нажмите Enter для продолжения..."
}

# Функция проверки и установки всех библиотек
check_install_libraries() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Проверка и установка библиотек${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Проверка виртуального окружения
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}⚠ Виртуальное окружение не найдено${NC}"
        echo -e "${GREEN}Создаём виртуальное окружение...${NC}"
        python3 -m venv $VENV_DIR
        if [ $? -eq 0 ]; then
            echo -e "${GREEN} Виртуальное окружение создано${NC}"
        else
            echo -e "${RED}✗ Ошибка создания виртуального окружения${NC}"
            read -p "Нажмите Enter для продолжения..."
            return
        fi
    else
        echo -e "${GREEN} Виртуальное окружение найдено${NC}"
    fi
    
    echo ""
    
    # Активация виртуального окружения
    source $VENV_DIR/bin/activate
    
    # Проверка наличия requirements.txt
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        echo -e "${RED}✗ Файл requirements.txt не найден${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    echo -e "${CYAN}Обновление pip...${NC}"
    pip install --upgrade pip
    echo ""
    
    echo -e "${CYAN}Проверка установленных пакетов...${NC}"
    echo ""
    
    # Читаем requirements.txt и проверяем каждый пакет
    MISSING_PACKAGES=()
    INSTALLED_PACKAGES=()
    
    while IFS= read -r line || [ -n "$line" ]; do
        # Пропускаем пустые строки и комментарии
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        
        # Извлекаем имя пакета (до знака =, <, > или [)
        package_name=$(echo "$line" | sed 's/[>=<\[].*//g' | tr -d '[:space:]')
        
        if [ -n "$package_name" ]; then
            # Проверяем установлен ли пакет
            if pip show "$package_name" &>/dev/null; then
                INSTALLED_PACKAGES+=("$package_name")
                echo -e "${GREEN}${NC} $package_name"
            else
                MISSING_PACKAGES+=("$line")
                echo -e "${RED}✗${NC} $package_name (не установлен)"
            fi
        fi
    done < "$PROJECT_DIR/requirements.txt"
    
    echo ""
    echo -e "${CYAN}─────────────────────────────────────────────────────────${NC}"
    echo -e "${WHITE}Установлено: ${GREEN}${#INSTALLED_PACKAGES[@]}${NC}"
    echo -e "${WHITE}Отсутствует: ${RED}${#MISSING_PACKAGES[@]}${NC}"
    echo -e "${CYAN}─────────────────────────────────────────────────────────${NC}"
    echo ""
    
    # Если есть отсутствующие пакеты, предлагаем установить
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        echo -e "${YELLOW}Отсутствующие пакеты:${NC}"
        for pkg in "${MISSING_PACKAGES[@]}"; do
            echo -e "  ${RED}●${NC} $pkg"
        done
        echo ""
        
        read -p "Установить отсутствующие пакеты? (y/n): " install_choice
        
        if [[ $install_choice == "y" || $install_choice == "Y" ]]; then
            echo ""
            echo -e "${GREEN}Установка пакетов из requirements.txt...${NC}"
            pip install -r "$PROJECT_DIR/requirements.txt"
            
            if [ $? -eq 0 ]; then
                echo ""
                echo -e "${GREEN} Все пакеты успешно установлены${NC}"
            else
                echo ""
                echo -e "${RED}✗ Произошли ошибки при установке${NC}"
            fi
        else
            echo -e "${YELLOW}Установка отменена${NC}"
        fi
    else
        echo -e "${GREEN} Все необходимые библиотеки установлены${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Версия Python:${NC} $(python --version)"
    echo -e "${CYAN}Версия pip:${NC} $(pip --version | cut -d' ' -f2)"
    echo ""
    
    deactivate
    
    read -p "Нажмите Enter для продолжения..."
}

# Основной цикл
while true; do
    show_menu
    read choice
    
    case $choice in
        1) start_all ;;
        2) stop_all ;;
        3) restart_all ;;
        4) start_bot ;;
        5) start_web ;;
        6) start_web_terminal ;;
        7) view_bot_logs ;;
        8) view_web_logs ;;
        9) check_status ;;
        10) update_project ;;
        11) update_dependencies ;;
        12) test_terminal ;;
        13) setup_systemd ;;
        14) check_install_libraries ;;
        15) reset_user_password ;;
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
