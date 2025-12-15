#!/bin/bash

# TelegramBolt Management Panel
# Панель управления для TelegramBolt с поддержкой веб-терминала

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

# Функция очистки экрана и вывода заголовка
show_header() {
    clear
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}        ${WHITE}TelegramBolt Management Panel${NC}              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}        ${PURPLE}Панель управления с веб-терминалом${NC}         ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
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

# Главное меню
show_menu() {
    show_header
    
    echo -e "${BLUE}┌─ Статус сервисов ────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  Telegram Bot:  $(get_service_status $BOT_SERVICE)"
    echo -e "${BLUE}│${NC}  Web Interface: $(get_service_status $WEB_SERVICE)"
    echo -e "${BLUE}│${NC}  Web Terminal:  $(check_process 'socketio')"
    echo -e "${BLUE}│${NC}"
    echo -e "${BLUE}└───────────────────────────────────────────────────────────┘${NC}"
    echo ""
    
    echo -e "${YELLOW}┌─ Управление ──────────────────────────────────────────────┐${NC}"
    echo -e "${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${WHITE}1.${NC} Запустить все сервисы"
    echo -e "${YELLOW}│${NC}  ${WHITE}2.${NC} Остановить все сервисы"
    echo -e "${YELLOW}│${NC}  ${WHITE}3.${NC} Перезапустить все сервисы"
    echo -e "${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${WHITE}4.${NC} Запустить только бота"
    echo -e "${YELLOW}│${NC}  ${WHITE}5.${NC} Запустить только веб"
    echo -e "${YELLOW}│${NC}  ${WHITE}6.${NC} Запустить веб с терминалом (Gunicorn)"
    echo -e "${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${WHITE}7.${NC} Просмотр логов бота"
    echo -e "${YELLOW}│${NC}  ${WHITE}8.${NC} Просмотр логов веб"
    echo -e "${YELLOW}│${NC}  ${WHITE}9.${NC} Проверка статуса"
    echo -e "${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${WHITE}10.${NC} Обновить проект (git pull)"
    echo -e "${YELLOW}│${NC}  ${WHITE}11.${NC} Обновить зависимости"
    echo -e "${YELLOW}│${NC}  ${WHITE}12.${NC} Тест веб-терминала"
    echo -e "${YELLOW}│${NC}  ${WHITE}13.${NC} Настройка systemd сервиса"
    echo -e "${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${WHITE}0.${NC} Выход"
    echo -e "${YELLOW}│${NC}"
    echo -e "${YELLOW}└───────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -n -e "${WHITE}Выберите действие: ${NC}"
}

# Функции управления
start_all() {
    echo -e "${GREEN}Запуск всех сервисов...${NC}"
    sudo systemctl start $BOT_SERVICE
    sudo systemctl start $WEB_SERVICE
    echo -e "${GREEN}✓ Сервисы запущены${NC}"
    sleep 2
}

stop_all() {
    echo -e "${YELLOW}Остановка всех сервисов...${NC}"
    sudo systemctl stop $BOT_SERVICE
    sudo systemctl stop $WEB_SERVICE
    echo -e "${GREEN}✓ Сервисы остановлены${NC}"
    sleep 2
}

restart_all() {
    echo -e "${YELLOW}Перезапуск всех сервисов...${NC}"
    sudo systemctl restart $BOT_SERVICE
    sudo systemctl restart $WEB_SERVICE
    echo -e "${GREEN}✓ Сервисы перезапущены${NC}"
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
    
    # Проверка виртуального окружения
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}✗ Виртуальное окружение не найдено${NC}"
        echo -e "${YELLOW}  Создаём виртуальное окружение...${NC}"
        python3 -m venv $VENV_DIR
    fi
    
    # Активация виртуального окружения
    source $VENV_DIR/bin/activate
    
    # Проверка зависимостей
    echo -e "${YELLOW}Проверка зависимостей...${NC}"
    if ! pip show flask-socketio &>/dev/null || ! pip show eventlet &>/dev/null; then
        echo -e "${YELLOW}Установка недостающих зависимостей...${NC}"
        pip install -q flask-socketio python-socketio eventlet ptyprocess gunicorn
    fi
    
    # Остановка старых процессов
    echo -e "${YELLOW}Остановка старых процессов на порту 5000...${NC}"
    sudo lsof -ti:5000 | xargs -r kill -9 2>/dev/null
    
    # Запуск Gunicorn с eventlet
    echo -e "${GREEN}Запуск сервера...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}Веб-интерфейс: ${GREEN}http://0.0.0.0:5000${NC}"
    echo -e "${WHITE}Веб-терминал:  ${GREEN}http://0.0.0.0:5000/terminal${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Для остановки нажмите Ctrl+C${NC}"
    echo ""
    
    cd $PROJECT_DIR
    gunicorn --worker-class eventlet -w 1 \
        --bind 0.0.0.0:5000 \
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
    echo -e "${WHITE}Порты:${NC}"
    sudo lsof -i :5000 2>/dev/null || echo "Порт 5000 свободен"
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
        echo -e "${GREEN}✓ Проект уже актуален${NC}"
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    read -p "Применить обновления? (y/n): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        git pull origin $(git branch --show-current)
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Код обновлен${NC}"
            echo ""
            
            # Обновление зависимостей
            echo -e "${CYAN}Обновление зависимостей...${NC}"
            if [ -d "$VENV_DIR" ]; then
                source $VENV_DIR/bin/activate
            fi
            pip install -q --upgrade pip
            pip install -q -r requirements.txt --upgrade
            echo -e "${GREEN}✓ Зависимости обновлены${NC}"
            echo ""
            
            # Перезапуск сервисов
            echo -e "${CYAN}Перезапуск сервисов...${NC}"
            sudo systemctl daemon-reload
            sudo systemctl start $BOT_SERVICE $WEB_SERVICE 2>/dev/null
            echo -e "${GREEN}✓ Сервисы перезапущены${NC}"
            echo ""
            
            echo -e "${GREEN}✓ Обновление завершено!${NC}"
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
    
    echo -e "${GREEN}✓ Зависимости обновлены${NC}"
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
            echo -e "  ${GREEN}✓${NC} ${pkg}"
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
            echo -e "  ${GREEN}✓${NC} $file"
        else
            echo -e "  ${RED}✗${NC} $file - не найден"
            all_ok=false
        fi
    done
    
    echo ""
    
    # Проверка интеграции
    echo -e "${YELLOW}Проверка интеграции в web_app.py:${NC}"
    
    if grep -q "from flask_socketio import SocketIO" $PROJECT_DIR/web/web_app.py; then
        echo -e "  ${GREEN}✓${NC} Flask-SocketIO импортирован"
    else
        echo -e "  ${RED}✗${NC} Flask-SocketIO не импортирован"
        all_ok=false
    fi
    
    if grep -q "socketio.run(app" $PROJECT_DIR/web/web_app.py; then
        echo -e "  ${GREEN}✓${NC} Приложение использует socketio.run()"
    else
        echo -e "  ${RED}✗${NC} Приложение не использует socketio.run()"
        all_ok=false
    fi
    
    echo ""
    
    if $all_ok; then
        echo -e "${GREEN}✓ Все проверки пройдены!${NC}"
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
    --bind 0.0.0.0:5000 \\
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
        echo -e "${GREEN}✓ Сервис создан${NC}"
        echo ""
        echo -e "${YELLOW}Команды управления:${NC}"
        echo -e "  ${WHITE}sudo systemctl enable telegrambolt-web${NC}  - добавить в автозагрузку"
        echo -e "  ${WHITE}sudo systemctl start telegrambolt-web${NC}   - запустить"
        echo -e "  ${WHITE}sudo systemctl status telegrambolt-web${NC}  - проверить статус"
        echo -e "  ${WHITE}sudo journalctl -u telegrambolt-web -f${NC}  - просмотр логов"
        echo ""
    else
        echo -e "${YELLOW}Отменено${NC}"
    fi
    
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
