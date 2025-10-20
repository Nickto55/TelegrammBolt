# 📊 Монитор бота - Быстрый старт

## ✅ Что создано

### Основные файлы
1. **monitor.py** - Интерактивная TUI консоль с curses
2. **monitor_integration.py** - Модуль интеграции с ботом
3. **start_monitor.sh** - Скрипт запуска для Linux
4. **MONITOR_README.md** - Полная документация
5. **monitor_cheatsheet.sh** - Шпаргалка по использованию

### Файлы обмена данными
- **monitor_stats.json** - Бот пишет статистику
- **monitor_commands.json** - Монитор пишет команды
- **bot_monitor.log** - Логи для мониторинга

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install psutil
```

### 2. Сделать скрипты исполняемыми
```bash
chmod +x start_monitor.sh
chmod +x monitor_cheatsheet.sh
```

### 3. Запустить монитор
```bash
./start_monitor.sh
```

### 4. Посмотреть шпаргалку
```bash
./monitor_cheatsheet.sh
```

## 📋 Как это работает

```
┌────────────────┐
│    bot.py      │ ← Основной бот
│   (Telegram)   │
└────────┬───────┘
         │
         ├─ Каждые 5 сек пишет статистику в monitor_stats.json
         ├─ Каждые 2 сек читает команды из monitor_commands.json
         ├─ Пишет логи в bot_monitor.log
         │
         ▼
┌────────────────┐
│ monitor_stats  │ ← Файл со статистикой
│    .json       │   (status, uptime, users, memory, etc.)
└────────────────┘
         ▲
         │
         │ читает
         │
┌────────┴───────┐
│  monitor.py    │ ← TUI интерфейс
│   (curses)     │
└────────┬───────┘
         │
         │ пишет команды
         │
         ▼
┌────────────────┐
│monitor_commands│ ← Команды управления
│    .json       │   (reload, clear_cache, etc.)
└────────────────┘
```

## 🎯 Основные возможности

### Вкладка 1: Статистика 📊
- Статус бота (running/stopped)
- Uptime (время работы)
- Пользователи (всего/активных)
- ДСЕ записей
- Запросы (всего и в минуту)
- Использование памяти

### Вкладка 2: Логи 📋
- Последние 100 строк логов
- Автообновление каждые 2 секунды
- Прокрутка: `↑`/`↓`, `PgUp`/`PgDn`

### Вкладка 3: Пользователи 👥
- Список всех пользователей
- ID, имя, роль, последняя активность
- Статистика по ролям

### Вкладка 4: Управление ⚙️
- `R` - Reload stats (обновить статистику)
- `C` - Clear cache (очистить кэш)
- `L` - Clear logs (очистить старые логи)
- `W` - Reset watcher (сброс отслеживания ДСЕ)
- `S` - Stop tasks (остановить фоновые задачи)

## ⌨️ Навигация

```
Tab / →         - Следующая вкладка
Shift+Tab / ←   - Предыдущая вкладка
↑ / ↓          - Прокрутка вверх/вниз
PgUp / PgDn     - Быстрая прокрутка
Home            - В начало
End             - В конец
Q / Ctrl+C      - Выход
```

## 🔧 Интеграция с ботом

Интеграция уже подключена в `bot.py`:
```python
from monitor_integration import start_monitor_integration
await start_monitor_integration(application)
```

Бот автоматически:
- ✅ Записывает статистику каждые 5 секунд
- ✅ Читает команды от монитора каждые 2 секунды
- ✅ Пишет логи в bot_monitor.log
- ✅ Обрабатывает команды управления

## 🛠️ Запуск в фоне

### Через tmux
```bash
tmux new -s monitor
./start_monitor.sh
# Detach: Ctrl+B, D
# Attach: tmux attach -t monitor
```

### Через screen
```bash
screen -S monitor
./start_monitor.sh
# Detach: Ctrl+A, D
# Attach: screen -r monitor
```

### Через SSH
```bash
ssh -t user@server "cd /opt/telegrambot && ./start_monitor.sh"
```

## 📊 Примеры команд

### Просмотр статистики вручную
```bash
cat monitor_stats.json | jq '.'
```

### Отправка команды вручную
```bash
echo '{"commands":[{"cmd":"reload_stats","timestamp":"'$(date +%Y-%m-%d\ %H:%M:%S)'"}]}' > monitor_commands.json
```

### Просмотр логов
```bash
tail -f bot_monitor.log
```

## ⚠️ Важно

1. **Монитор не влияет на бота** - они работают независимо
2. **Бот работает без монитора** - монитор опциональный
3. **Команды асинхронные** - результат может быть не мгновенным
4. **Минимум ресурсов** - монитор потребляет <10MB RAM

## 🐛 Решение проблем

### Монитор не запускается
```bash
# Права на выполнение
chmod +x start_monitor.sh

# Проверка Python
python3 --version  # Нужен 3.7+

# Установка psutil
pip3 install psutil
```

### Нет данных
```bash
# Проверить бота
systemctl status telegrambot

# Проверить файлы
ls -la monitor_*.json

# Логи бота
journalctl -u telegrambot -f
```

### Ошибка curses
```bash
# Ubuntu/Debian
sudo apt install libncurses5-dev

# Проверка терминала
echo $TERM
export TERM=xterm-256color
```

## 📚 Дополнительно

- **Полная документация**: `cat MONITOR_README.md`
- **Шпаргалка**: `./monitor_cheatsheet.sh`
- **Логи бота**: `journalctl -u telegrambot -f`
- **Статус бота**: `systemctl status telegrambot`

---

**Версия**: 1.0  
**Платформа**: Linux  
**Python**: 3.7+  
**Зависимости**: psutil, curses (стандартная библиотека)
