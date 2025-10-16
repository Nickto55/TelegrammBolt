# 🔧 Быстрое исправление ошибок

## Проблемы, которые вы видите:

### 1. ❌ ImportError: cannot import name 'show_pdf_export_menu'
```python
ImportError: cannot import name 'show_pdf_export_menu' from 'pdf_generator'
```

### 2. ❌ show-web-url.sh не найден
```bash
bash: show-web-url.sh: No such file or directory
```

### 3. ❌ Веб-интерфейс недоступен
```bash
curl: (7) Failed to connect to localhost port 5000
```

---

## ✅ БЫСТРОЕ РЕШЕНИЕ (3 шага)

### Шаг 1: Скачать обновленный pdf_generator.py

```bash
# В Docker контейнере (в директории /web)
curl -o pdf_generator.py https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/pdf_generator.py
```

ИЛИ добавьте функцию вручную в `pdf_generator.py` перед строкой `if __name__ == "__main__":`:

```python
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
```

### Шаг 2: Создать show-web-url.sh

```bash
# В директории /web
cat > show-web-url.sh << 'EOF'
#!/bin/bash
# Скрипт для отображения URL веб-интерфейса

WEB_PORT=${WEB_PORT:-5000}

echo ""
echo "🌐 URL веб-интерфейса:"
echo ""

# Получить IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
PUBLIC_IP=$(curl -s --connect-timeout 2 ifconfig.me || echo "")

if [ ! -z "$PUBLIC_IP" ]; then
    echo "  🌍 Public:  http://${PUBLIC_IP}:${WEB_PORT}"
fi
echo "  🏠 Local:   http://${LOCAL_IP}:${WEB_PORT}"
echo ""

# Проверка доступности
if curl -s --connect-timeout 2 http://localhost:${WEB_PORT} > /dev/null 2>&1; then
    echo "✓ Веб-интерфейс доступен"
else
    echo "⚠ Веб-интерфейс не запущен"
    echo ""
    echo "Запустите: python web_app.py"
fi
echo ""
EOF

chmod +x show-web-url.sh
```

### Шаг 3: Перезапустить бота

```bash
# Остановить (если запущен)
pkill -9 -f "python.*bot.py"

# Запустить заново
sudo bash ./start_bot.sh
```

---

## 🚀 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ

Используйте скрипт `fix-bot-errors.sh`:

```bash
# Скачать скрипт
curl -o fix-bot-errors.sh https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/fix-bot-errors.sh

# Сделать исполняемым
chmod +x fix-bot-errors.sh

# Запустить
bash fix-bot-errors.sh
```

Скрипт автоматически:
- Проверит и создаст `show-web-url.sh`
- Проверит и создаст `cleanup-bot.sh`
- Добавит функцию `show_pdf_export_menu` в `pdf_generator.py`
- Создаст недостающие файлы данных (`users_data.json`, `bot_data.json`)
- Создаст директорию `photos`

---

## 📝 Ручное исправление pdf_generator.py

### Способ 1: Через nano

```bash
nano pdf_generator.py
```

Найдите строку `if __name__ == "__main__":` (в конце файла) и ПЕРЕД ней добавьте:

```python
async def show_pdf_export_menu(update, context):
    """Показать меню экспорта PDF"""
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
        "📊 *Экспорт в PDF*\n\nВыберите опцию экспорта:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


```

Сохраните: `Ctrl+O`, Enter, `Ctrl+X`

### Способ 2: Через sed

```bash
# Добавить функцию автоматически
sed -i "/^if __name__ == \"__main__\":/i\\
async def show_pdf_export_menu(update, context):\\n\\
    \"\"\"Показать меню экспорта PDF\"\"\"\\n\\
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup\\n\\
    \\n\\
    query = update.callback_query\\n\\
    await query.answer()\\n\\
    \\n\\
    keyboard = [\\n\\
        [InlineKeyboardButton(\"📄 Экспорт всех записей\", callback_data='pdf_export_all')],\\n\\
        [InlineKeyboardButton(\"📋 Выбрать записи\", callback_data='pdf_export_select')],\\n\\
        [InlineKeyboardButton(\"⬅️ Назад\", callback_data='reports')]\\n\\
    ]\\n\\
    \\n\\
    reply_markup = InlineKeyboardMarkup(keyboard)\\n\\
    await query.edit_message_text(\\n\\
        \"📊 *Экспорт в PDF*\\\\n\\\\nВыберите опцию экспорта:\",\\n\\
        reply_markup=reply_markup,\\n\\
        parse_mode='Markdown'\\n\\
    )\\n\\
\\n\\
" pdf_generator.py
```

---

## 🌐 Запуск веб-интерфейса

Веб-интерфейс по умолчанию НЕ запускается автоматически.

### Способ 1: Вручную

```bash
# В отдельном терминале или фоне
python web_app.py &

# Или с указанием порта
WEB_PORT=5000 python web_app.py &
```

### Способ 2: Через службу (если настроена)

```bash
sudo service telegrambot-web start
```

### Способ 3: Через systemd (если настроен)

```bash
sudo systemctl start telegrambot-web
```

### Проверка веб-интерфейса

```bash
# Проверить порт 5000
curl http://localhost:5000

# Или
netstat -tulpn | grep 5000

# Или
ps aux | grep web_app
```

---

## 🐛 Проверка после исправления

```bash
# 1. Проверить что функция есть
grep -n "def show_pdf_export_menu" pdf_generator.py

# 2. Проверить что скрипт создан
ls -la show-web-url.sh

# 3. Тест скрипта
bash show-web-url.sh

# 4. Запустить бота
sudo bash ./start_bot.sh
```

---

## 📚 Дополнительная информация

- **Если бот не запускается:** [FIX_CONFLICT_ERROR.md](FIX_CONFLICT_ERROR.md)
- **Если нет веб-интерфейса:** Скачайте из ветки `web`
  ```bash
  curl -o web_app.py https://raw.githubusercontent.com/Nickto55/TelegrammBolt/web/web_app.py
  ```
- **Полная документация:** [README_Ubuntu.md](README_Ubuntu.md)

---

## ⚡ Команды в одну строку

### Исправить pdf_generator.py и создать скрипты:

```bash
# Создать show-web-url.sh
cat > show-web-url.sh << 'EOF'
#!/bin/bash
WEB_PORT=${WEB_PORT:-5000}
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "🌐 URL: http://${LOCAL_IP}:${WEB_PORT}"
EOF
chmod +x show-web-url.sh

# Добавить функцию в pdf_generator.py (если её нет)
grep -q "def show_pdf_export_menu" pdf_generator.py || echo '
async def show_pdf_export_menu(update, context):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📄 Экспорт всех записей", callback_data="pdf_export_all")],
        [InlineKeyboardButton("📋 Выбрать записи", callback_data="pdf_export_select")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="reports")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📊 *Экспорт в PDF*\n\nВыберите опцию экспорта:", reply_markup=reply_markup, parse_mode="Markdown")
' >> pdf_generator.py

# Перезапустить бота
pkill -f "bot.py" && sudo bash ./start_bot.sh
```

---

**Готово!** Теперь бот должен работать без ошибок. 🎉
