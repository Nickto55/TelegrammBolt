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

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка
```bash
# Скопируйте example файлы и настройте
cp config/ven_bot.json.example config/ven_bot.json
# Отредактируйте config/ven_bot.json - добавьте токен бота
```

### 3. Запуск

**Telegram бот:**
```bash
cd bot
python bot.py
```

**Веб-интерфейс:**
```bash
cd web
python web_app.py
```

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
