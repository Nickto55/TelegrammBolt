#!/bin/bash

# Скрипт для остановки всех экземпляров TelegrammBolt и очистки конфликтов
# Использование: bash cleanup-bot.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   TelegrammBolt Cleanup Script            ║${NC}"
echo -e "${BLUE}║   Устранение конфликтов                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Функция для вывода с цветом
print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Шаг 1: Показать текущие процессы
print_step "Поиск запущенных процессов бота..."
PROCESSES=$(ps aux | grep -E "bot\.py|python.*telegrambot" | grep -v grep | grep -v cleanup)
if [ -z "$PROCESSES" ]; then
    print_success "Активных процессов не найдено"
else
    echo "$PROCESSES"
    print_warning "Найдены активные процессы!"
fi
echo ""

# Шаг 2: Остановить службу
print_step "Остановка службы telegrambot..."
if command -v systemctl &> /dev/null; then
    # systemd
    if systemctl is-active --quiet telegrambot 2>/dev/null; then
        sudo systemctl stop telegrambot || true
        print_success "Служба systemd остановлена"
    else
        print_warning "Служба systemd не запущена"
    fi
elif [ -f /etc/init.d/telegrambot ]; then
    # init.d
    sudo service telegrambot stop 2>/dev/null || true
    print_success "Служба init.d остановлена"
else
    print_warning "Служба не найдена (systemd/init.d)"
fi
echo ""

# Шаг 3: Убить все процессы Python с bot.py
print_step "Завершение всех процессов bot.py..."
BOT_PIDS=$(pgrep -f "python.*bot.py" || true)
if [ -z "$BOT_PIDS" ]; then
    print_success "Процессы bot.py не найдены"
else
    echo "PIDs: $BOT_PIDS"
    sudo pkill -TERM -f "python.*bot.py" 2>/dev/null || true
    sleep 2
    # Проверить, остались ли процессы
    REMAINING=$(pgrep -f "python.*bot.py" || true)
    if [ ! -z "$REMAINING" ]; then
        print_warning "Процессы не остановились, принудительное завершение..."
        sudo pkill -9 -f "python.*bot.py" 2>/dev/null || true
    fi
    print_success "Процессы bot.py завершены"
fi
echo ""

# Шаг 4: Убить процессы web_app.py (если есть)
print_step "Завершение процессов web_app.py..."
WEB_PIDS=$(pgrep -f "python.*web_app.py" || true)
if [ -z "$WEB_PIDS" ]; then
    print_success "Процессы web_app.py не найдены"
else
    echo "PIDs: $WEB_PIDS"
    sudo pkill -TERM -f "python.*web_app.py" 2>/dev/null || true
    sleep 2
    # Проверить, остались ли процессы
    REMAINING=$(pgrep -f "python.*web_app.py" || true)
    if [ ! -z "$REMAINING" ]; then
        print_warning "Процессы не остановились, принудительное завершение..."
        sudo pkill -9 -f "python.*web_app.py" 2>/dev/null || true
    fi
    print_success "Процессы web_app.py завершены"
fi
echo ""

# Шаг 5: Удалить lock файлы
print_step "Удаление lock файлов..."
if [ -d /opt/telegrambot ]; then
    sudo rm -f /opt/telegrambot/*.lock 2>/dev/null || true
    sudo rm -f /opt/telegrambot/*.pid 2>/dev/null || true
    print_success "Lock файлы удалены"
else
    print_warning "Директория /opt/telegrambot не найдена"
fi
echo ""

# Шаг 6: Подождать
print_step "Ожидание завершения процессов..."
sleep 3
print_success "Ожидание завершено"
echo ""

# Шаг 7: Финальная проверка
print_step "Финальная проверка процессов..."
FINAL_CHECK=$(ps aux | grep -E "bot\.py|web_app\.py" | grep -v grep | grep -v cleanup || true)
if [ -z "$FINAL_CHECK" ]; then
    print_success "Все процессы успешно завершены!"
else
    print_error "Все еще остались процессы:"
    echo "$FINAL_CHECK"
    echo ""
    print_warning "Попробуйте выполнить вручную:"
    echo "  sudo pkill -9 -f 'python.*bot.py'"
    exit 1
fi
echo ""

# Шаг 8: Проверить webhook
print_step "Проверка webhook (если настроен)..."
if [ -f /opt/telegrambot/ven_bot.json ]; then
    TOKEN=$(grep -o '"bot_token": *"[^"]*"' /opt/telegrambot/ven_bot.json | cut -d'"' -f4 || true)
    if [ ! -z "$TOKEN" ]; then
        WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" 2>/dev/null || echo '{"ok":false}')
        WEBHOOK_URL=$(echo "$WEBHOOK_INFO" | grep -o '"url":"[^"]*"' | cut -d'"' -f4 || true)
        if [ ! -z "$WEBHOOK_URL" ]; then
            print_warning "Webhook настроен: $WEBHOOK_URL"
            echo "Для использования polling нужно удалить webhook:"
            echo "  curl \"https://api.telegram.org/bot${TOKEN}/deleteWebhook\""
        else
            print_success "Webhook не настроен (используется polling)"
        fi
    else
        print_warning "Не удалось прочитать токен из ven_bot.json"
    fi
else
    print_warning "Файл ven_bot.json не найден"
fi
echo ""

# Итоговый отчет
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ Очистка завершена успешно!            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Теперь вы можете запустить бота:${NC}"
echo ""
echo "  ${YELLOW}Вариант 1: Через службу (рекомендуется)${NC}"
echo "    sudo service telegrambot start"
echo "    sudo service telegrambot status"
echo ""
echo "  ${YELLOW}Вариант 2: Вручную (для отладки)${NC}"
echo "    cd /opt/telegrambot"
echo "    sudo -u telegrambot .venv/bin/python bot.py"
echo ""
echo "  ${YELLOW}Вариант 3: С веб-интерфейсом${NC}"
echo "    sudo service telegrambot start"
echo "    sudo service telegrambot-web start"
echo ""
echo -e "${BLUE}Полезные команды:${NC}"
echo "  Логи службы:    tail -f /opt/telegrambot/telegrambot.log"
echo "  Статус службы:  sudo service telegrambot status"
echo "  Процессы:       ps aux | grep bot.py"
echo "  Этот скрипт:    bash cleanup-bot.sh"
echo ""
