#!/bin/bash

# Скрипт для освобождения порта 5000 и перезапуска бота

echo "=========================================="
echo "Освобождение порта 5000 и перезапуск бота"
echo "=========================================="
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Шаг 1: Проверка порта 5000
echo -e "${YELLOW}[1/5]${NC} Проверка порта 5000..."

if lsof -i :5000 > /dev/null 2>&1; then
    echo -e "  ${YELLOW}!${NC} Порт 5000 занят"
    
    # Показать какой процесс
    PROCESS=$(lsof -i :5000 | grep LISTEN | awk '{print $1, $2}' | head -1)
    echo "  Процесс: $PROCESS"
    
    # Получить PID
    PID=$(lsof -t -i :5000)
    
    if [ -n "$PID" ]; then
        echo -e "  ${YELLOW}[ACTION]${NC} Убиваем процесс PID: $PID"
        kill -9 $PID 2>/dev/null
        sleep 1
        
        if lsof -i :5000 > /dev/null 2>&1; then
            echo -e "  ${RED}✗${NC} Не удалось освободить порт"
        else
            echo -e "  ${GREEN}✓${NC} Порт 5000 освобождён"
        fi
    fi
else
    echo -e "  ${GREEN}✓${NC} Порт 5000 свободен"
fi

# Шаг 2: Остановка всех экземпляров бота
echo ""
echo -e "${YELLOW}[2/5]${NC} Остановка всех экземпляров бота..."

if pgrep -f "python.*bot.py" > /dev/null; then
    echo -e "  ${YELLOW}!${NC} Найдены запущенные боты"
    pkill -9 -f "python.*bot.py"
    sleep 2
    echo -e "  ${GREEN}✓${NC} Все экземпляры остановлены"
else
    echo -e "  ${GREEN}✓${NC} Боты не запущены"
fi

# Шаг 3: Проверка что всё остановлено
echo ""
echo -e "${YELLOW}[3/5]${NC} Финальная проверка..."

REMAINING=$(pgrep -f "python.*bot.py" | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Все процессы остановлены"
else
    echo -e "  ${RED}✗${NC} Остались процессы: $REMAINING"
    ps aux | grep "[p]ython.*bot.py"
fi

# Шаг 4: Очистка лог-файлов (опционально)
echo ""
echo -e "${YELLOW}[4/5]${NC} Очистка старых логов..."

if [ -f bot.log ]; then
    # Оставляем только последние 100 строк
    tail -100 bot.log > bot.log.tmp
    mv bot.log.tmp bot.log
    echo -e "  ${GREEN}✓${NC} Логи очищены"
else
    echo -e "  ${GREEN}✓${NC} Лог-файл не найден"
fi

# Шаг 5: Запуск бота
echo ""
echo -e "${YELLOW}[5/5]${NC} Запуск бота..."

cd /opt/telegrambot

# Проверка наличия venv
if [ -d ".venv" ]; then
    echo "  Активация виртуального окружения..."
    source .venv/bin/activate
fi

# Запуск бота
nohup python3 bot.py > bot.log 2>&1 &
BOT_PID=$!

sleep 3

# Проверка запуска
if ps -p $BOT_PID > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Бот запущен (PID: $BOT_PID)"
    
    # Проверка Flask через 5 секунд
    echo ""
    echo "  Ожидание запуска Flask (5 сек)..."
    sleep 5
    
    if lsof -i :5000 > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Flask запущен на порту 5000"
        
        # Тест доступности
        if curl -s -o /dev/null http://127.0.0.1:5000/login 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Flask отвечает на запросы"
        else
            echo -e "  ${YELLOW}!${NC} Flask не отвечает (возможно, ещё инициализируется)"
        fi
    else
        echo -e "  ${RED}✗${NC} Flask не запустился"
        echo "  Проверьте логи: tail -f bot.log"
    fi
else
    echo -e "  ${RED}✗${NC} Бот не запустился"
    echo "  Проверьте логи:"
    tail -20 bot.log
fi

echo ""
echo "=========================================="
echo "Готово!"
echo "=========================================="
echo ""
echo "Полезные команды:"
echo "  Логи бота:       tail -f bot.log"
echo "  Проверка порта:  lsof -i :5000"
echo "  Остановить бота: pkill -f bot.py"
echo "  Статус Flask:    curl http://127.0.0.1:5000/login"
echo ""

# Показать последние 10 строк лога
echo "Последние логи:"
echo "---"
tail -10 bot.log
echo ""
