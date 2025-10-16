#!/bin/bash

# Скрипт для исправления ошибок бота
# Автоматически создает недостающие файлы и функции

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   TelegrammBolt - Исправление ошибок     ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""

BOT_DIR="/opt/telegrambot"
CURRENT_DIR=$(pwd)

# Определяем директорию бота
if [ -d "$BOT_DIR" ]; then
    WORK_DIR="$BOT_DIR"
elif [ -f "bot.py" ]; then
    WORK_DIR="$CURRENT_DIR"
else
    echo -e "${RED}✗ Не найдена директория бота!${NC}"
    exit 1
fi

echo -e "${BLUE}▶${NC} Рабочая директория: $WORK_DIR"
cd "$WORK_DIR"
echo ""

# Проверка 1: Файл show-web-url.sh
echo -e "${BLUE}▶${NC} Проверка show-web-url.sh..."
if [ ! -f "show-web-url.sh" ]; then
    echo -e "${YELLOW}⚠${NC} Файл show-web-url.sh отсутствует, создаю..."
    
    cat > show-web-url.sh << 'EOFSCRIPT'
#!/bin/bash
# Скрипт для отображения URL веб-интерфейса

set -e

# Цвета
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   TelegrammBolt Web Interface URL        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Получить порт
WEB_PORT=${WEB_PORT:-5000}

# Проверить Docker
IS_DOCKER=false
if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    IS_DOCKER=true
fi

# Получить IP адреса
get_public_ip() {
    curl -s --connect-timeout 2 ifconfig.me || curl -s --connect-timeout 2 icanhazip.com || echo ""
}

get_local_ip() {
    hostname -I 2>/dev/null | awk '{print $1}' || ip route get 1 2>/dev/null | awk '{print $7}' || echo "127.0.0.1"
}

PUBLIC_IP=$(get_public_ip)
LOCAL_IP=$(get_local_ip)

# Вывод информации
echo -e "${GREEN}🌐 URL веб-интерфейса:${NC}"
echo ""

if [ "$IS_DOCKER" = true ]; then
    echo -e "  ${YELLOW}📦 Docker Container:${NC}"
    echo -e "     http://localhost:${WEB_PORT}"
    echo ""
fi

if [ ! -z "$PUBLIC_IP" ]; then
    echo -e "  ${YELLOW}🌍 Public URL:${NC}"
    echo -e "     http://${PUBLIC_IP}:${WEB_PORT}"
    echo ""
fi

echo -e "  ${YELLOW}🏠 Local URL:${NC}"
echo -e "     http://${LOCAL_IP}:${WEB_PORT}"
echo ""

# Проверка доступности
echo -e "${BLUE}📊 Статус сервиса:${NC}"
if curl -s --connect-timeout 2 http://localhost:${WEB_PORT} > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Веб-интерфейс доступен${NC}"
else
    echo -e "  ${YELLOW}⚠ Веб-интерфейс не запущен${NC}"
    echo ""
    echo "Запустите веб-интерфейс:"
    echo "  python web_app.py"
    echo "  или"
    echo "  sudo service telegrambot-web start"
fi

echo ""
EOFSCRIPT
    
    chmod +x show-web-url.sh
    echo -e "${GREEN}✓ Файл show-web-url.sh создан${NC}"
else
    echo -e "${GREEN}✓ Файл show-web-url.sh существует${NC}"
fi
echo ""

# Проверка 2: Файл cleanup-bot.sh
echo -e "${BLUE}▶${NC} Проверка cleanup-bot.sh..."
if [ ! -f "cleanup-bot.sh" ]; then
    echo -e "${YELLOW}⚠${NC} Файл cleanup-bot.sh отсутствует, создаю..."
    
    # Скопируем содержимое из основного проекта
    cat > cleanup-bot.sh << 'EOFCLEANUP'
#!/bin/bash
# Скрипт для очистки конфликтов бота

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   TelegrammBolt Cleanup Script            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Остановить службу
echo -e "${BLUE}▶${NC} Остановка службы..."
sudo service telegrambot stop 2>/dev/null || true
echo -e "${GREEN}✓${NC} Служба остановлена"

# Убить процессы
echo -e "${BLUE}▶${NC} Завершение процессов..."
sudo pkill -9 -f "python.*bot.py" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓${NC} Процессы завершены"

# Удалить lock файлы
echo -e "${BLUE}▶${NC} Удаление lock файлов..."
rm -f /opt/telegrambot/*.lock 2>/dev/null || true
rm -f /opt/telegrambot/*.pid 2>/dev/null || true
echo -e "${GREEN}✓${NC} Lock файлы удалены"

echo ""
echo -e "${GREEN}✓ Очистка завершена!${NC}"
echo ""
echo "Запустите бота:"
echo "  sudo service telegrambot start"
EOFCLEANUP
    
    chmod +x cleanup-bot.sh
    echo -e "${GREEN}✓ Файл cleanup-bot.sh создан${NC}"
else
    echo -e "${GREEN}✓ Файл cleanup-bot.sh существует${NC}"
fi
echo ""

# Проверка 3: Функция show_pdf_export_menu в pdf_generator.py
echo -e "${BLUE}▶${NC} Проверка pdf_generator.py..."
if ! grep -q "def show_pdf_export_menu" pdf_generator.py; then
    echo -e "${YELLOW}⚠${NC} Функция show_pdf_export_menu отсутствует, добавляю..."
    
    # Добавляем функцию перед if __name__ == "__main__"
    sed -i '/^if __name__ == "__main__":/i\
async def show_pdf_export_menu(update, context):\
    """\
    Показать меню экспорта PDF\
    """\
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup\
    \
    query = update.callback_query\
    await query.answer()\
    \
    keyboard = [\
        [InlineKeyboardButton("📄 Экспорт всех записей", callback_data='"'"'pdf_export_all'"'"')],\
        [InlineKeyboardButton("📋 Выбрать записи", callback_data='"'"'pdf_export_select'"'"')],\
        [InlineKeyboardButton("⬅️ Назад", callback_data='"'"'reports'"'"')]\
    ]\
    \
    reply_markup = InlineKeyboardMarkup(keyboard)\
    await query.edit_message_text(\
        "📊 *Экспорт в PDF*\\n\\n"\
        "Выберите опцию экспорта:",\
        reply_markup=reply_markup,\
        parse_mode='"'"'Markdown'"'"'\
    )\
\
\
' pdf_generator.py
    
    echo -e "${GREEN}✓ Функция show_pdf_export_menu добавлена${NC}"
else
    echo -e "${GREEN}✓ Функция show_pdf_export_menu существует${NC}"
fi
echo ""

# Проверка 4: users_data.json
echo -e "${BLUE}▶${NC} Проверка users_data.json..."
if [ ! -f "users_data.json" ]; then
    echo -e "${YELLOW}⚠${NC} Файл users_data.json отсутствует, создаю..."
    echo '{}' > users_data.json
    chmod 644 users_data.json
    echo -e "${GREEN}✓ Файл users_data.json создан${NC}"
else
    echo -e "${GREEN}✓ Файл users_data.json существует${NC}"
fi
echo ""

# Проверка 5: bot_data.json
echo -e "${BLUE}▶${NC} Проверка bot_data.json..."
if [ ! -f "bot_data.json" ]; then
    echo -e "${YELLOW}⚠${NC} Файл bot_data.json отсутствует, создаю..."
    echo '{"records": []}' > bot_data.json
    chmod 644 bot_data.json
    echo -e "${GREEN}✓ Файл bot_data.json создан${NC}"
else
    echo -e "${GREEN}✓ Файл bot_data.json существует${NC}"
fi
echo ""

# Проверка 6: Директория photos
echo -e "${BLUE}▶${NC} Проверка директории photos..."
if [ ! -d "photos" ]; then
    echo -e "${YELLOW}⚠${NC} Директория photos отсутствует, создаю..."
    mkdir -p photos
    chmod 755 photos
    echo -e "${GREEN}✓ Директория photos создана${NC}"
else
    echo -e "${GREEN}✓ Директория photos существует${NC}"
fi
echo ""

# Итоговый отчет
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ Все проверки завершены!               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Теперь можно запустить бота:${NC}"
echo "  sudo bash ./start_bot.sh"
echo "  или"
echo "  sudo service telegrambot start"
echo ""
