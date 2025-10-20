#!/bin/bash#!/bin/bash#!/bin/bash#!/bin/bash

#

# УСТАНОВЩИК TelegrammBolt для Linux/Ubuntu#

# Автоматическая установка и настройка бота + веб-интерфейса

## 🚀 УСТАНОВЩИК TelegrammBolt для Linux/Ubuntu#################################################################################



set -e  # Остановка при ошибке# Автоматическая установка и настройка бота + веб-интерфейса



# ============================================## 🚀 УСТАНОВЩИК TelegrammBolt для Linux/Ubuntu# TelegrammBolt - Полный установочный скрипт с интерактивной настройкой

# Цвета для вывода

# ============================================

RED='\033[0;31m'

GREEN='\033[0;32m'set -e  # Остановка при ошибке# Автоматическая установка и настройка бота + веб-интерфейса# Версия: 2.0

YELLOW='\033[1;33m'

BLUE='\033[0;34m'

NC='\033[0m'

# ============================================## Автор: Nickto55

# ============================================

# Функции для красивого вывода# Цвета для вывода

# ============================================

print_header() {# ============================================# Дата: 17 октября 2025

    echo ""

    echo -e "${BLUE}======================================================================${NC}"RED='\033[0;31m'

    echo -e "${BLUE}  $1${NC}"

    echo -e "${BLUE}======================================================================${NC}"GREEN='\033[0;32m'set -e  # Остановка при ошибке################################################################################

    echo ""

}YELLOW='\033[1;33m'



print_success() {BLUE='\033[0;34m'

    echo -e "${GREEN}[OK]${NC} $1"

}NC='\033[0m'



print_error() {# Цвета для выводаset -e  # Остановка при любой ошибке

    echo -e "${RED}[ERROR]${NC} $1"

}# ============================================



print_warning() {# Функции для красивого выводаRED='\033[0;31m'

    echo -e "${YELLOW}[WARN]${NC} $1"

}# ============================================



print_info() {print_header() {GREEN='\033[0;32m'# ============================================

    echo -e "${BLUE}[INFO]${NC} $1"

}    echo ""



# ============================================    echo -e "${BLUE}======================================================================${NC}"YELLOW='\033[1;33m'# Цвета для вывода

# Проверка запуска из корня проекта

# ============================================    echo -e "${BLUE}  $1${NC}"

if [ ! -d "bot" ] || [ ! -d "web" ]; then

    print_error "Ошибка: Запустите скрипт из корня проекта!"    echo -e "${BLUE}======================================================================${NC}"BLUE='\033[0;34m'# ============================================

    print_info "Должны существовать папки: bot/ и web/"

    exit 1    echo ""

fi

}NC='\033[0m' # No ColorRED='\033[0;31m'

print_header "TelegrammBolt - Установщик для Linux"



# ============================================

# 1. Проверка Pythonprint_success() {GREEN='\033[0;32m'

# ============================================

print_header "Проверка Python"    echo -e "${GREEN}✓${NC} $1"



if ! command -v python3 &> /dev/null; then}# Функции для красивого выводаYELLOW='\033[1;33m'

    print_error "Python 3 не найден!"

    print_info "Установите: sudo apt install python3 python3-pip python3-venv"

    exit 1

fiprint_error() {print_header() {BLUE='\033[0;34m'



PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)    echo -e "${RED}✗${NC} $1"

print_success "Python $PYTHON_VERSION установлен"

}    echo ""CYAN='\033[0;36m'

# ============================================

# 2. Создание виртуального окружения

# ============================================

print_header "Создание виртуального окружения"print_warning() {    echo -e "${BLUE}======================================================================${NC}"PURPLE='\033[0;35m'



if [ ! -d ".venv" ]; then    echo -e "${YELLOW}⚠${NC} $1"

    print_info "Создаю .venv..."

    python3 -m venv .venv}    echo -e "${BLUE}$1${NC}"NC='\033[0m' # No Color

    print_success "Виртуальное окружение создано"

else

    print_info ".venv уже существует"

fiprint_info() {    echo -e "${BLUE}======================================================================${NC}"



# Активация venv    echo -e "${BLUE}ℹ${NC} $1"

source .venv/bin/activate

print_success "Виртуальное окружение активировано"}    echo ""# ============================================



# ============================================

# 3. Обновление pip

# ============================================# ============================================}# Функции для вывода

print_header "Обновление pip"

pip install --upgrade pip --quiet# Проверка запуска из корня проекта

print_success "pip обновлён"

# ============================================# ============================================

# ============================================

# 4. Установка зависимостейif [ ! -d "bot" ] || [ ! -d "web" ]; then

# ============================================

print_header "Установка зависимостей"    print_error "Ошибка: Запустите скрипт из корня проекта!"print_success() {log() {



if [ -f "requirements.txt" ]; then    print_info "Должны существовать папки: bot/ и web/"

    print_info "Устанавливаю пакеты из requirements.txt..."

    pip install -r requirements.txt --quiet    exit 1    echo -e "${GREEN}✓${NC} $1"    echo -e "${BLUE}[INFO]${NC} $1"

    print_success "Все зависимости установлены"

elsefi

    print_error "requirements.txt не найден!"

    exit 1}}

fi

print_header "TelegrammBolt - Установщик для Linux"

# ============================================

# 5. Создание директорий

# ============================================

print_header "Создание директорий"# ============================================



mkdir -p data photos/temp config logs# 1. Проверка Pythonprint_error() {warn() {

print_success "Директории созданы: data/, photos/, config/, logs/"

# ============================================

# ============================================

# 6. Создание конфигурационных файловprint_header "Проверка Python"    echo -e "${RED}✗${NC} $1"    echo -e "${YELLOW}[WARN]${NC} $1"

# ============================================

print_header "Настройка конфигурации"



# config/ven_bot.jsonif ! command -v python3 &> /dev/null; then}}

if [ ! -f "config/ven_bot.json" ]; then

    print_info "Создаю config/ven_bot.json..."    print_error "Python 3 не найден!"

    

    echo ""    print_info "Установите: sudo apt install python3 python3-pip python3-venv"

    read -p "Введите BOT_TOKEN от @BotFather: " BOT_TOKEN

    read -p "Введите ваш Telegram ID (admin): " ADMIN_ID    exit 1

    

    if [ -z "$BOT_TOKEN" ]; thenfiprint_warning() {error() {

        BOT_TOKEN="YOUR_BOT_TOKEN_HERE"

        print_warning "Токен не введён, создаю с заглушкой"

    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)    echo -e "${YELLOW}⚠${NC} $1"    echo -e "${RED}[ERROR]${NC} $1"

    if [ -z "$ADMIN_ID" ]; then

        ADMIN_ID="123456789"print_success "Python $PYTHON_VERSION установлен"

        print_warning "ID не введён, используем заглушку"

    fi}    exit 1

    

    cat > config/ven_bot.json <<EOF# ============================================

{

  "BOT_TOKEN": "$BOT_TOKEN",# 2. Создание виртуального окружения}

  "BOT_USERNAME": "@your_bot",

  "ADMIN_IDS": [$ADMIN_ID]# ============================================

}

EOFprint_header "Создание виртуального окружения"print_info() {

    print_success "Создан: config/ven_bot.json"

else

    print_info "config/ven_bot.json уже существует"

fiif [ ! -d ".venv" ]; then    echo -e "${BLUE}ℹ${NC} $1"success() {



# ============================================    print_info "Создаю .venv..."

# 7. Создание файлов данных

# ============================================    python3 -m venv .venv}    echo -e "${GREEN}[✓]${NC} $1"

print_header "Создание файлов данных"

    print_success "Виртуальное окружение создано"

for file in bot_data.json users_data.json chat_data.json watched_dse.json; do

    if [ ! -f "data/$file" ]; thenelse}

        echo "{}" > "data/$file"

        print_success "Создан: data/$file"    print_info ".venv уже существует"

    else

        print_info "data/$file уже существует"fi# Проверка что скрипт запущен из корня проекта

    fi

done



# ============================================# Активация venvif [ ! -d "bot" ] || [ ! -d "web" ]; thensection() {

# 8. Создание скриптов запуска

# ============================================source .venv/bin/activate

print_header "Создание скриптов запуска"

print_success "Виртуальное окружение активировано"    print_error "Ошибка: Запустите скрипт из корня проекта!"    echo ""

# start_bot.sh

cat > start_bot.sh <<'EOF'

#!/bin/bash

# Запуск Telegram бота TelegrammBolt# ============================================    print_info "Должны существовать папки: bot/ и web/"    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"



SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"# 3. Обновление pip

cd "$SCRIPT_DIR"

# ============================================    exit 1    echo -e "${CYAN}  $1${NC}"

# Активация виртуального окружения

if [ -d ".venv" ]; thenprint_header "Обновление pip"

    source .venv/bin/activate

elif [ -d "venv" ]; thenpip install --upgrade pip --quietfi    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"

    source venv/bin/activate

fiprint_success "pip обновлён"



# Запуск бота    echo ""

echo "Запуск Telegram бота..."

cd bot# ============================================

python3 bot.py

EOF# 4. Установка зависимостейprint_header "TelegrammBolt - Установщик для Linux"}



chmod +x start_bot.sh# ============================================

print_success "Создан: start_bot.sh"

print_header "Установка зависимостей"

# start_web.sh

cat > start_web.sh <<'EOF'

#!/bin/bash

# Запуск веб-интерфейса TelegrammBoltif [ -f "requirements.txt" ]; then# 1. Проверка Pythonprompt() {



SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"    print_info "Устанавливаю пакеты из requirements.txt..."

cd "$SCRIPT_DIR"

    pip install -r requirements.txt --quietprint_header "Проверка Python"    echo -e "${PURPLE}[?]${NC} $1"

# Активация виртуального окружения

if [ -d ".venv" ]; then    print_success "Все зависимости установлены"

    source .venv/bin/activate

elif [ -d "venv" ]; thenelse}

    source venv/bin/activate

fi    print_error "requirements.txt не найден!"



# Запуск веб-приложения    exit 1if ! command -v python3 &> /dev/null; then

echo "Запуск веб-интерфейса..."

cd webfi

python3 web_app.py

EOF    print_error "Python 3 не найден!"# ============================================



chmod +x start_web.sh# ============================================

print_success "Создан: start_web.sh"

# 5. Создание директорий    print_info "Установите: sudo apt install python3 python3-pip python3-venv"# Глобальные переменные

# ============================================

# 9. Тестирование# ============================================

# ============================================

print_header "Тестирование установки"print_header "Создание директорий"    exit 1# ============================================



python3 -c "import telegram, flask, openpyxl, reportlab, nest_asyncio" 2>/dev/null

if [ $? -eq 0 ]; then

    print_success "Все модули импортируются"mkdir -p data photos/temp config logsfiBOT_DIR="/opt/telegrambot"

else

    print_warning "Некоторые модули не установлены"print_success "Директории созданы: data/, photos/, config/, logs/"

fi

BOT_USER="telegrambot"

# ============================================

# 10. Финальные инструкции# ============================================

# ============================================

print_header "Установка завершена!"# 6. Создание конфигурационных файловPYTHON_VERSION=$(python3 --version | cut -d' ' -f2)SERVICE_FILE="/etc/systemd/system/telegrambot.service"



echo ""# ============================================

echo -e "${GREEN}Что дальше:${NC}"

echo ""print_header "Настройка конфигурации"print_success "Python $PYTHON_VERSION установлен"PYTHON_VERSION=""

echo "1. Настройте конфигурацию:"

echo "   nano config/ven_bot.json"

echo "   Добавьте ваш BOT_TOKEN от @BotFather"

echo ""# config/ven_bot.jsonBOT_TOKEN=""

echo "2. Запустите бота:"

echo "   ./start_bot.sh"if [ ! -f "config/ven_bot.json" ]; then

echo "   или"

echo "   source .venv/bin/activate && cd bot && python3 bot.py"    print_info "Создаю config/ven_bot.json..."# 2. Создание виртуального окруженияADMIN_IDS=""

echo ""

echo "3. Запустите веб-интерфейс:"    

echo "   ./start_web.sh"

echo "   или"    echo ""print_header "Создание виртуального окружения"SMTP_ENABLED="no"

echo "   source .venv/bin/activate && cd web && python3 web_app.py"

echo ""    read -p "$(echo -e ${YELLOW}Введите BOT_TOKEN от @BotFather: ${NC})" BOT_TOKEN

echo "4. Откройте в браузере:"

echo "   http://localhost:5000"    read -p "$(echo -e ${YELLOW}Введите ваш Telegram ID \(admin\): ${NC})" ADMIN_IDSMTP_SERVER=""

echo ""

echo -e "${BLUE}Документация:${NC}"    

echo "   README.md - Общее описание"

echo "   UTILS.md - Утилиты диагностики"    if [ -z "$BOT_TOKEN" ]; thenif [ ! -d ".venv" ]; thenSMTP_PORT=""

echo ""

echo -e "${GREEN}Готово! Удачной работы!${NC}"        BOT_TOKEN="YOUR_BOT_TOKEN_HERE"

echo ""

        print_warning "Токен не введён, создаю с заглушкой"    print_info "Создаю .venv..."SMTP_USER=""

    fi

        python3 -m venv .venvSMTP_PASSWORD=""

    if [ -z "$ADMIN_ID" ]; then

        ADMIN_ID="123456789"    print_success "Виртуальное окружение создано"WEB_ENABLED="yes"

        print_warning "ID не введён, используем заглушку"

    fielseWEB_PORT="5000"

    

    cat > config/ven_bot.json <<EOF    print_info ".venv уже существует"HTTPS_ENABLED="no"

{

  "BOT_TOKEN": "$BOT_TOKEN",fiDOMAIN_NAME=""

  "BOT_USERNAME": "@your_bot",

  "ADMIN_IDS": [$ADMIN_ID]

}

EOF# Активация venv# ============================================

    print_success "Создан: config/ven_bot.json"

elsesource .venv/bin/activate# Баннер

    print_info "config/ven_bot.json уже существует"

fiprint_success "Виртуальное окружение активировано"# ============================================



# ============================================show_banner() {

# 7. Создание файлов данных

# ============================================# 3. Обновление pip    clear

print_header "Создание файлов данных"

print_header "Обновление pip"    echo -e "${CYAN}"

for file in bot_data.json users_data.json chat_data.json watched_dse.json; do

    if [ ! -f "data/$file" ]; thenpip install --upgrade pip --quiet    cat << "EOF"

        echo "{}" > "data/$file"

        print_success "Создан: data/$file"print_success "pip обновлён"╔═══════════════════════════════════════════════════════════════╗

    else

        print_info "data/$file уже существует"║                                                               ║

    fi

done# 4. Установка зависимостей║   ████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗  ║



# ============================================print_header "Установка зависимостей"║   ╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗ ║

# 8. Создание скриптов запуска

# ============================================║      ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║ ║

print_header "Создание скриптов запуска"

if [ -f "requirements.txt" ]; then║      ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║ ║

# start_bot.sh

cat > start_bot.sh <<'EOF'    print_info "Устанавливаю пакеты из requirements.txt..."║      ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║ ║

#!/bin/bash

# Запуск Telegram бота TelegrammBolt    pip install -r requirements.txt --quiet║      ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ║



SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"    print_success "Все зависимости установлены"║                                                               ║

cd "$SCRIPT_DIR"

else║             TELEGRAMMBOLT - Автоматический установщик         ║

# Активация виртуального окружения

if [ -d ".venv" ]; then    print_error "requirements.txt не найден!"║                         Версия 2.0                            ║

    source .venv/bin/activate

elif [ -d "venv" ]; then    exit 1║                                                               ║

    source venv/bin/activate

fifi╚═══════════════════════════════════════════════════════════════╝



# Запуск ботаEOF

echo "🤖 Запуск Telegram бота..."

cd bot# 5. Создание директорий    echo -e "${NC}"

python3 bot.py

EOFprint_header "Создание директорий"    echo ""



chmod +x start_bot.sh}

print_success "Создан: start_bot.sh"

mkdir -p data photos/temp config logs

# start_web.sh

cat > start_web.sh <<'EOF'print_success "Директории созданы: data/, photos/, config/, logs/"# ============================================

#!/bin/bash

# Запуск веб-интерфейса TelegrammBolt# Проверка прав root



SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"# 6. Создание конфигурационных файлов# ============================================

cd "$SCRIPT_DIR"

print_header "Настройка конфигурации"check_root() {

# Активация виртуального окружения

if [ -d ".venv" ]; then    if [[ $EUID -ne 0 ]]; then

    source .venv/bin/activate

elif [ -d "venv" ]; then# config/ven_bot.json        error "Этот скрипт должен запускаться с правами root (используйте sudo)"

    source venv/bin/activate

fiif [ ! -f "config/ven_bot.json" ]; then    fi



# Запуск веб-приложения    print_info "Создаю config/ven_bot.json..."}

echo "🌐 Запуск веб-интерфейса..."

cd web    

python3 web_app.py

EOF    echo ""# ============================================



chmod +x start_web.sh    read -p "$(echo -e ${YELLOW}Введите BOT_TOKEN от @BotFather: ${NC})" BOT_TOKEN# Проверка системы

print_success "Создан: start_web.sh"

    read -p "$(echo -e ${YELLOW}Введите ваш Telegram ID \(admin\): ${NC})" ADMIN_ID# ============================================

# ============================================

# 9. Тестирование    check_system() {

# ============================================

print_header "Тестирование установки"    if [ -z "$BOT_TOKEN" ]; then    section "Проверка системы"



python3 -c "import telegram, flask, openpyxl, reportlab, nest_asyncio" 2>/dev/null        BOT_TOKEN="YOUR_BOT_TOKEN_HERE"    

if [ $? -eq 0 ]; then

    print_success "Все модули импортируются"        print_warning "Токен не введён, создаю с заглушкой"    log "Проверка операционной системы..."

else

    print_warning "Некоторые модули не установлены"    fi    

fi

        if ! command -v lsb_release &> /dev/null; then

# ============================================

# 10. Финальные инструкции    if [ -z "$ADMIN_ID" ]; then        warn "lsb_release не найден. Установка..."

# ============================================

print_header "✅ Установка завершена!"        ADMIN_ID="123456789"        apt-get update -qq



echo ""        print_warning "ID не введён, используем заглушку"        apt-get install -y lsb-release

echo -e "${GREEN}Что дальше:${NC}"

echo ""    fi    fi

echo "1️⃣  Настройте конфигурацию:"

echo -e "   ${YELLOW}nano config/ven_bot.json${NC}"        

echo "   Добавьте ваш BOT_TOKEN от @BotFather"

echo ""    cat > config/ven_bot.json <<EOF    DISTRIB=$(lsb_release -si)

echo "2️⃣  Запустите бота:"

echo -e "   ${YELLOW}./start_bot.sh${NC}"{    VERSION=$(lsb_release -sr)

echo "   или"

echo -e "   ${YELLOW}source .venv/bin/activate && cd bot && python3 bot.py${NC}"  "BOT_TOKEN": "$BOT_TOKEN",    

echo ""

echo "3️⃣  Запустите веб-интерфейс:"  "BOT_USERNAME": "@your_bot",    success "Обнаружена система: $DISTRIB $VERSION"

echo -e "   ${YELLOW}./start_web.sh${NC}"

echo "   или"  "ADMIN_IDS": [$ADMIN_ID]    

echo -e "   ${YELLOW}source .venv/bin/activate && cd web && python3 web_app.py${NC}"

echo ""}    if [[ "$DISTRIB" != "Ubuntu" && "$DISTRIB" != "Debian" ]]; then

echo "4️⃣  Откройте в браузере:"

echo -e "   ${BLUE}http://localhost:5000${NC}"EOF        error "Поддерживаются только Ubuntu и Debian. Обнаружено: $DISTRIB"

echo ""

echo -e "${BLUE}📚 Документация:${NC}"    print_success "Создан: config/ven_bot.json"    fi

echo "   README.md - Общее описание"

echo "   UTILS.md - Утилиты диагностики"else    

echo ""

echo -e "${GREEN}✨ Готово! Удачной работы! ✨${NC}"    print_info "config/ven_bot.json уже существует"    # Проверка Docker

echo ""

fi    if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then

        warn "Обнаружено Docker окружение"

# 7. Создание файлов данных        DOCKER_ENV=true

print_header "Создание файлов данных"    else

        DOCKER_ENV=false

for file in bot_data.json users_data.json chat_data.json watched_dse.json; do    fi

    if [ ! -f "data/$file" ]; then}

        echo "{}" > "data/$file"

        print_success "Создан: data/$file"# ============================================

    else# Проверка Python

        print_info "data/$file уже существует"# ============================================

    ficheck_python() {

done    section "Проверка Python"

    

# 8. Создание скриптов запуска    if ! command -v python3 &> /dev/null; then

print_header "Создание скриптов запуска"        error "Python 3 не найден. Установите Python 3.9+"

    fi

# start_bot.sh    

cat > start_bot.sh <<'EOF'    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')

#!/bin/bash    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)

# Запуск Telegram бота TelegrammBolt    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"    success "Python версия: $PYTHON_VERSION"

cd "$SCRIPT_DIR"    

    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 9 ]]; then

# Активация виртуального окружения        error "Требуется Python 3.9+. Обнаружено: $PYTHON_VERSION"

if [ -d ".venv" ]; then    fi

    source .venv/bin/activate    

elif [ -d "venv" ]; then    if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 13 ]]; then

    source venv/bin/activate        warn "Обнаружен Python 3.13+. Возможны проблемы совместимости."

fi        warn "Рекомендуется Python 3.11 или 3.12"

        sleep 2

# Запуск бота    fi

echo "🤖 Запуск Telegram бота..."}

cd bot

python3 bot.py# ============================================

EOF# Обновление системы

# ============================================

chmod +x start_bot.shupdate_system() {

print_success "Создан: start_bot.sh"    section "Обновление системы"

    

# start_web.sh    log "Обновление списка пакетов..."

cat > start_web.sh <<'EOF'    apt-get update -qq

#!/bin/bash    

# Запуск веб-интерфейса TelegrammBolt    log "Установка системных зависимостей..."

    apt-get install -y -qq \

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"        python3 \

cd "$SCRIPT_DIR"        python3-pip \

        python3-venv \

# Активация виртуального окружения        git \

if [ -d ".venv" ]; then        curl \

    source .venv/bin/activate        wget \

elif [ -d "venv" ]; then        unzip \

    source venv/bin/activate        build-essential \

fi        nginx \

        certbot \

# Запуск веб-приложения        python3-certbot-nginx \

echo "🌐 Запуск веб-интерфейса..."        jq

cd web    

python3 web_app.py    success "Системные зависимости установлены"

EOF}



chmod +x start_web.sh# ============================================

print_success "Создан: start_web.sh"# Интерактивная настройка - Bot Token

# ============================================

# 9. Тестированиеconfigure_bot_token() {

print_header "Тестирование установки"    section "Настройка Telegram Бота"

    

python3 -c "import telegram, flask, openpyxl, reportlab, nest_asyncio" 2>/dev/null    echo ""

if [ $? -eq 0 ]; then    log "Для работы бота нужен токен от @BotFather"

    print_success "Все модули импортируются"    log "Как получить токен:"

else    echo "  1. Откройте Telegram"

    print_warning "Некоторые модули не установлены"    echo "  2. Найдите @BotFather"

fi    echo "  3. Отправьте команду: /newbot"

    echo "  4. Следуйте инструкциям"

# 10. Финальные инструкции    echo "  5. Скопируйте токен (формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)"

print_header "✅ Установка завершена!"    echo ""

    

echo ""    while true; do

echo -e "${GREEN}Что дальше:${NC}"        echo ""

echo ""        echo -ne "${PURPLE}[?]${NC} Введите токен бота: "

echo "1️⃣  Настройте конфигурацию:"        read -r BOT_TOKEN

echo -e "   ${YELLOW}nano config/ven_bot.json${NC}"        

echo "   Добавьте ваш BOT_TOKEN от @BotFather"        # Убираем возможные пробелы в начале и конце

echo ""        BOT_TOKEN=$(echo "$BOT_TOKEN" | xargs)

echo "2️⃣  Запустите бота:"        

echo -e "   ${YELLOW}./start_bot.sh${NC}"        if [[ -z "$BOT_TOKEN" ]]; then

echo "   или"            error "Токен не может быть пустым!"

echo -e "   ${YELLOW}source .venv/bin/activate && cd bot && python3 bot.py${NC}"            continue

echo ""        fi

echo "3️⃣  Запустите веб-интерфейс:"        

echo -e "   ${YELLOW}./start_web.sh${NC}"        # Базовая проверка формата токена

echo "   или"        if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then

echo -e "   ${YELLOW}source .venv/bin/activate && cd web && python3 web_app.py${NC}"            warn "Токен имеет неправильный формат!"

echo ""            warn "Ожидаемый формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

echo "4️⃣  Откройте в браузере:"            echo -ne "Продолжить с этим токеном? (y/n): "

echo -e "   ${BLUE}http://localhost:5000${NC}"            read -r -n 1 REPLY

echo ""            echo

echo -e "${BLUE}📚 Документация:${NC}"            if [[ $REPLY =~ ^[Yy]$ ]]; then

echo "   README.md - Общее описание"                break

echo "   UTILS.md - Утилиты диагностики"            fi

echo "   SECURITY.md - Безопасность"        else

echo ""            success "Токен принят"

echo -e "${GREEN}✨ Готово! Удачной работы! ✨${NC}"            break

echo ""        fi

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
