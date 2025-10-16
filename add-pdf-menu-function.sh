#!/bin/bash
# Быстрое исправление ImportError для show_pdf_export_menu

echo "🔧 Добавление функции show_pdf_export_menu в pdf_generator.py..."

# Проверяем существование файла
if [ ! -f "pdf_generator.py" ]; then
    echo "❌ Файл pdf_generator.py не найден!"
    exit 1
fi

# Проверяем, есть ли уже функция
if grep -q "def show_pdf_export_menu" pdf_generator.py; then
    echo "✓ Функция show_pdf_export_menu уже существует"
    exit 0
fi

# Находим строку if __name__ == "__main__":
LINE_NUM=$(grep -n '^if __name__ == "__main__":' pdf_generator.py | cut -d: -f1)

if [ -z "$LINE_NUM" ]; then
    echo "❌ Не найдена строка 'if __name__ == \"__main__\":'"
    echo "Добавляю функцию в конец файла..."
    cat >> pdf_generator.py << 'EOFUNC'


async def show_pdf_export_menu(update, context):
    """
    Показать меню экспорта PDF
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📄 Экспорт всех записей", callback_data='pdf_export_all')],
        [InlineKeyboardButton("📋 Выбрать записи", callback_data='pdf_export_select')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='reports')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📊 *Экспорт в PDF*\n\n"
        "Выберите опцию экспорта:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
EOFUNC
else
    # Вставляем перед if __name__
    BEFORE_LINE=$((LINE_NUM - 1))
    
    # Создаем временный файл
    head -n $BEFORE_LINE pdf_generator.py > pdf_generator.py.tmp
    
    cat >> pdf_generator.py.tmp << 'EOFUNC'

async def show_pdf_export_menu(update, context):
    """
    Показать меню экспорта PDF
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📄 Экспорт всех записей", callback_data='pdf_export_all')],
        [InlineKeyboardButton("📋 Выбрать записи", callback_data='pdf_export_select')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='reports')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📊 *Экспорт в PDF*\n\n"
        "Выберите опцию экспорта:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


EOFUNC
    
    tail -n +$LINE_NUM pdf_generator.py >> pdf_generator.py.tmp
    
    # Заменяем оригинальный файл
    mv pdf_generator.py.tmp pdf_generator.py
fi

echo "✅ Функция show_pdf_export_menu добавлена!"
echo ""
echo "Теперь можно перезапустить бота:"
echo "  sudo bash ./start_bot.sh"
