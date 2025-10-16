#!/bin/bash
# ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ - Запустить в Docker контейнере в директории /web

echo "🚨 Экстренное исправление TelegrammBolt..."

# 1. Остановить бота (если запущен)
pkill -f "bot.py" 2>/dev/null
echo "✓ Процессы остановлены"

# 2. Добавить функцию show_pdf_export_menu
if ! grep -q "def show_pdf_export_menu" pdf_generator.py; then
    echo "📝 Добавление функции show_pdf_export_menu..."
    
    # Найти строку с if __name__
    LINE=$(grep -n '^if __name__ == "__main__":' pdf_generator.py | cut -d: -f1)
    
    if [ -z "$LINE" ]; then
        # Добавить в конец
        cat >> pdf_generator.py << 'EOF'


async def show_pdf_export_menu(update, context):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📄 Экспорт всех записей", callback_data='pdf_export_all')],
        [InlineKeyboardButton("📋 Выбрать записи", callback_data='pdf_export_select')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='reports')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📊 *Экспорт в PDF*\n\nВыберите опцию экспорта:", reply_markup=reply_markup, parse_mode='Markdown')
EOF
    else
        # Вставить перед if __name__
        BEFORE=$((LINE - 1))
        head -n $BEFORE pdf_generator.py > pdf_generator.py.tmp
        cat >> pdf_generator.py.tmp << 'EOF'


async def show_pdf_export_menu(update, context):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📄 Экспорт всех записей", callback_data='pdf_export_all')],
        [InlineKeyboardButton("📋 Выбрать записи", callback_data='pdf_export_select')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='reports')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📊 *Экспорт в PDF*\n\nВыберите опцию экспорта:", reply_markup=reply_markup, parse_mode='Markdown')


EOF
        tail -n +$LINE pdf_generator.py >> pdf_generator.py.tmp
        mv pdf_generator.py.tmp pdf_generator.py
    fi
    echo "✓ Функция добавлена"
else
    echo "✓ Функция уже существует"
fi

# 3. Создать show-web-url.sh
if [ ! -f "show-web-url.sh" ]; then
    echo "📝 Создание show-web-url.sh..."
    cat > show-web-url.sh << 'EOF'
#!/bin/bash
WEB_PORT=${WEB_PORT:-5000}
LOCAL_IP=$(hostname -I | awk '{print $1}')
PUBLIC_IP=$(curl -s --connect-timeout 2 ifconfig.me || echo "")
echo ""
echo "🌐 URL веб-интерфейса:"
[ ! -z "$PUBLIC_IP" ] && echo "  Public: http://${PUBLIC_IP}:${WEB_PORT}"
echo "  Local:  http://${LOCAL_IP}:${WEB_PORT}"
echo ""
EOF
    chmod +x show-web-url.sh
    echo "✓ show-web-url.sh создан"
else
    echo "✓ show-web-url.sh существует"
fi

# 4. Создать cleanup-bot.sh
if [ ! -f "cleanup-bot.sh" ]; then
    echo "📝 Создание cleanup-bot.sh..."
    cat > cleanup-bot.sh << 'EOF'
#!/bin/bash
echo "🧹 Очистка процессов..."
sudo service telegrambot stop 2>/dev/null || true
pkill -9 -f "python.*bot.py" 2>/dev/null || true
rm -f *.lock *.pid 2>/dev/null || true
sleep 2
echo "✓ Очистка завершена"
echo "Запустите: sudo bash ./start_bot.sh"
EOF
    chmod +x cleanup-bot.sh
    echo "✓ cleanup-bot.sh создан"
else
    echo "✓ cleanup-bot.sh существует"
fi

# 5. Создать недостающие файлы данных
[ ! -f "users_data.json" ] && echo '{}' > users_data.json && echo "✓ users_data.json создан"
[ ! -f "bot_data.json" ] && echo '{"records": []}' > bot_data.json && echo "✓ bot_data.json создан"
[ ! -d "photos" ] && mkdir -p photos && echo "✓ директория photos создана"

echo ""
echo "✅ Исправление завершено!"
echo ""
echo "Запустите бота:"
echo "  sudo bash ./start_bot.sh"
echo ""
