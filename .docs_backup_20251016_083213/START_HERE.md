# ⚡ ЧТО ДЕЛАТЬ ПРЯМО СЕЙЧАС

## Вы находитесь в Docker контейнере в директории `/web`

### 🎯 ОДНА КОМАНДА - ИСПРАВИТ ВСЁ

```bash
bash emergency-fix.sh
```

Если файл не существует, создайте его:

```bash
cat > emergency-fix.sh << 'EOFSCRIPT'
#!/bin/bash
echo "🚨 Экстренное исправление..."
pkill -f "bot.py" 2>/dev/null
echo "✓ Процессы остановлены"

# Добавить функцию
if ! grep -q "def show_pdf_export_menu" pdf_generator.py; then
    LINE=$(grep -n '^if __name__ == "__main__":' pdf_generator.py | cut -d: -f1)
    if [ -z "$LINE" ]; then
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
fi

[ ! -f "users_data.json" ] && echo '{}' > users_data.json
[ ! -f "bot_data.json" ] && echo '{"records": []}' > bot_data.json
[ ! -d "photos" ] && mkdir -p photos

echo "✅ Готово! Запустите: sudo bash ./start_bot.sh"
EOFSCRIPT

chmod +x emergency-fix.sh
bash emergency-fix.sh
```

---

## 🔴 ИЛИ ТРИ ПРОСТЫЕ КОМАНДЫ

### 1. Остановить бота:
```bash
pkill -f "bot.py"
```

### 2. Добавить функцию в pdf_generator.py:
```bash
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
```

### 3. Запустить бота:
```bash
sudo bash ./start_bot.sh
```

---

## ✅ Проверка

После запуска бота отправьте `/start` в Telegram.

Бот должен ответить без ошибок!

---

## 📚 Что было исправлено

1. ✅ Добавлена функция `show_pdf_export_menu` в `pdf_generator.py`
2. ✅ Созданы файлы `users_data.json`, `bot_data.json` (если отсутствовали)
3. ✅ Создана директория `photos` (если отсутствовала)

---

## 🌐 Веб-интерфейс (опционально)

Если хотите запустить веб-интерфейс:

```bash
# Проверьте, есть ли web_app.py
ls -la web_app.py

# Если есть, запустите
python web_app.py &

# Проверьте
curl http://localhost:5000
```

---

## 🆘 Если не помогло

Покажите вывод:

```bash
# 1. Проверить функцию
grep -n "def show_pdf_export_menu" pdf_generator.py

# 2. Попробовать запустить
sudo bash ./start_bot.sh

# 3. Скопируйте ошибку и отправьте в чат
```

---

**НАЧНИТЕ С ПЕРВОЙ КОМАНДЫ:** `bash emergency-fix.sh` 🚀
