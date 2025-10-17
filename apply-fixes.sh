#!/bin/bash

# 🚀 Быстрое применение исправлений
# Дата: $(date)

echo "=================================================="
echo "🔧 ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ ДЛЯ TELEGRAM БОТА"
echo "=================================================="
echo ""

# Проверка директории
if [ ! -d "/opt/telegrambot" ]; then
    echo "❌ Ошибка: Директория /opt/telegrambot не найдена"
    exit 1
fi

cd /opt/telegrambot

echo "📍 Текущая директория: $(pwd)"
echo ""

# Остановка бота
echo "⏸️  Остановка бота..."
pkill -f "python.*bot.py" 2>/dev/null
pkill -f "python.*web_app.py" 2>/dev/null
sleep 2

# Проверка портов
echo "🔍 Проверка портов..."
PORT_5000=$(lsof -ti:5000 2>/dev/null)
if [ ! -z "$PORT_5000" ]; then
    echo "⚠️  Порт 5000 занят (PID: $PORT_5000), освобождаем..."
    kill -9 $PORT_5000 2>/dev/null
    sleep 1
fi

# Резервное копирование
echo "💾 Создание резервной копии..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp commands.py "$BACKUP_DIR/"
cp pdf_generator.py "$BACKUP_DIR/"
echo "   Резервная копия: $BACKUP_DIR"
echo ""

# Проверка Python окружения
echo "🐍 Проверка Python окружения..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   ✅ Virtual environment активирован"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "   ✅ Virtual environment активирован"
else
    echo "   ⚠️  Virtual environment не найден, используем системный Python"
fi

# Проверка зависимостей
echo "📦 Проверка зависимостей..."
python -c "import telegram, flask, reportlab" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ⚠️  Устанавливаем отсутствующие зависимости..."
    pip install python-telegram-bot flask reportlab pillow psutil -q
fi

# Проверка файлов конфигурации
echo "⚙️  Проверка конфигурации..."
if [ ! -f "ven_bot.json" ]; then
    echo "   ❌ Ошибка: ven_bot.json не найден"
    exit 1
fi

BOT_USERNAME=$(python -c "import json; print(json.load(open('ven_bot.json')).get('BOT_USERNAME', ''))" 2>/dev/null)
if [ -z "$BOT_USERNAME" ]; then
    echo "   ⚠️  Предупреждение: BOT_USERNAME пустой в ven_bot.json"
    echo "   📝 Установите его в конфигурации для работы веб-авторизации"
fi

# Запуск бота
echo ""
echo "🚀 Запуск бота..."
nohup python bot.py > bot.log 2>&1 &
BOT_PID=$!

# Ожидание запуска
echo "⏳ Ожидание инициализации (5 секунд)..."
sleep 5

# Проверка статуса
if ps -p $BOT_PID > /dev/null; then
    echo ""
    echo "=================================================="
    echo "✅ БОТ УСПЕШНО ЗАПУЩЕН!"
    echo "=================================================="
    echo ""
    echo "📊 Информация:"
    echo "   - PID: $BOT_PID"
    echo "   - Логи: tail -f bot.log"
    echo "   - Web: http://localhost:5000 (если включен)"
    echo ""
    echo "🧪 Тестирование исправлений:"
    echo ""
    echo "   1️⃣  Изменение роли пользователя:"
    echo "      - Панель администратора → Изменить роль"
    echo "      - Выбрать пользователя → Выбрать роль"
    echo "      - ✅ Должно показать: 'Роль изменена на: [Роль]'"
    echo ""
    echo "   2️⃣  Выборочный экспорт PDF:"
    echo "      - Главное меню → Экспорт в PDF"
    echo "      - Выбрать записи → Выбрать ДСЕ"
    echo "      - Экспорт выбранных"
    echo "      - ✅ Должны прийти PDF файлы"
    echo ""
    echo "📝 Команды управления:"
    echo "   - Остановить: pkill -f 'python.*bot.py'"
    echo "   - Перезапустить: bash apply-fixes.sh"
    echo "   - Логи: tail -f bot.log"
    echo "   - Монитор: python monitor.py"
    echo ""
    echo "=================================================="
else
    echo ""
    echo "❌ ОШИБКА ЗАПУСКА БОТА"
    echo "=================================================="
    echo ""
    echo "🔍 Проверьте логи:"
    echo "   tail -50 bot.log"
    echo ""
    echo "📝 Последние 20 строк лога:"
    tail -20 bot.log
    echo ""
    echo "🛠️  Возможные причины:"
    echo "   - Неверный токен в ven_bot.json"
    echo "   - Порт 5000 занят другим процессом"
    echo "   - Отсутствуют зависимости Python"
    echo "   - Синтаксическая ошибка в коде"
    echo ""
    exit 1
fi

echo "✨ Готово!"
