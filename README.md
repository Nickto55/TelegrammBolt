# TelegrammBolt - Telegram Bot + Web Interface

Система управления заявками ДСЕ с Telegram ботом и веб-интерфейсом.

## 📁 Структура проекта

```
TelegrammBolt/
├── bot/                    # Telegram бот
├── web/                    # Веб-интерфейс (Flask)
├── config/                 # Конфигурация
├── data/                   # Файлы данных
├── photos/                 # Загруженные фотографии
├── scripts/                # Утилиты и скрипты
└── docs/                   # Документация
```

## � Утилиты

После установки доступен мощный набор инструментов диагностики:

```bash
# Интерактивный режим
python utils.py

# Проверка системы
python utils.py check

# Найти заявку по ID
python utils.py find Hshd

# Диагностика данных
python utils.py diagnose

# Показать пользователей
python utils.py users
```

Подробнее в [UTILS.md](UTILS.md)

## Быстрый старт

### Автоматическая установка (рекомендуется)

```bash
python install.py
```

Установщик автоматически:
- ✅ Проверит Python и зависимости
- ✅ Создаст необходимые директории
- ✅ Настроит конфигурацию (попросит BOT_TOKEN)
- ✅ Создаст файлы данных
- ✅ Создаст скрипты запуска

### Ручная установка

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Настройте конфигурацию:**
```bash
# Создайте config/ven_bot.json
{
  "BOT_TOKEN": "your_token_from_botfather",
  "BOT_USERNAME": "@your_bot",
  "ADMIN_IDS": [123456789]
}
```

3. **Запуск:**

**Telegram бот:**
```bash
# Linux/Mac
./start_bot.sh

# Windows
start_bot.bat

# Или вручную
cd bot && python bot.py
```

**Веб-интерфейс:**
```bash
# Linux/Mac
./start_web.sh

# Windows  
start_web.bat

# Или вручную
cd web && python web_app.py
```

Веб-интерфейс: http://localhost:5000

## 📚 Документация

- [Установка](docs/INSTALLATION.md) - Подробная инструкция по установке
- [Решение проблем](docs/TROUBLESHOOTING.md) - Частые вопросы и решения
- [Быстрые исправления](docs/QUICK_FIX.md) - Быстрые решения типичных проблем

## 🛠️ Утилиты

В папке `scripts/` находятся полезные инструменты:

- `server_check.py` - Проверка состояния системы
- `check_dse_id.py` - Поиск заявки по ID
- `diagnose_dse.py` - Диагностика данных
- `emergency_check.py` - Экстренная проверка

## 🔧 Разработка

### Структура бота (bot/)
- `bot.py` - Главный файл
- `commands.py` - Команды бота
- `dse_manager.py` - Управление заявками
- `user_manager.py` - Управление пользователями

### Структура веба (web/)
- `web_app.py` - Flask приложение
- `static/` - CSS, JS, изображения
- `templates/` - HTML шаблоны

## 📞 Поддержка

При возникновении проблем:
1. Запустите диагностику: `python scripts/emergency_check.py`
2. Проверьте логи в консоли
3. См. [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 📝 Лицензия

MIT License
