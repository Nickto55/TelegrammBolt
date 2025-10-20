# 📊 Монитор бота TelegrammBolt

Интерактивная консоль для мониторинга и управления ботом в режиме реального времени.

## 🚀 Запуск

### Linux/Ubuntu
```bash
# Сделать скрипт исполняемым (первый раз)
chmod +x start_monitor.sh

# Запустить монитор
./start_monitor.sh
```

Или напрямую через Python:
```bash
python3 monitor.py
```

## 📋 Возможности

### 📊 Вкладка "Статистика"
- **Статус бота**: работает/остановлен
- **Uptime**: время работы бота
- **Пользователи**: всего/активных
- **ДСЕ записей**: общее количество
- **Запросы**: всего и в минуту
- **Память**: использование RAM
- **Последнее обновление**: время последнего обновления статистики

### 📋 Вкладка "Логи"
- Просмотр логов бота в реальном времени
- Прокрутка: `↑` / `↓` или `PgUp` / `PgDn`
- Автообновление каждые 2 секунды
- Последние 100 строк логов

### 👥 Вкладка "Пользователи"
- Список всех пользователей бота
- Информация: ID, имя, роль, последняя активность
- Статистика по ролям
- Прокрутка списка: `↑` / `↓`

### ⚙️ Вкладка "Управление"
- **R** - Перезагрузить статистику
- **C** - Очистить кэш
- **L** - Очистить старые логи
- **W** - Сбросить watcher
- **S** - Остановить фоновые задачи

## ⌨️ Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| `Tab` / `→` | Следующая вкладка |
| `Shift+Tab` / `←` | Предыдущая вкладка |
| `↑` / `↓` | Прокрутка вверх/вниз |
| `PgUp` / `PgDn` | Быстрая прокрутка |
| `Home` | В начало |
| `End` | В конец |
| `Q` / `Ctrl+C` | Выход |

На вкладке "Управление":
- `R` - Reload stats
- `C` - Clear cache
- `L` - Clear logs
- `W` - Reset watcher
- `S` - Stop tasks

## 🔧 Как это работает

### Архитектура
```
┌─────────────┐         ┌──────────────────┐
│   Bot.py    │ ◄─────► │ monitor_stats.json│
│             │         └──────────────────┘
│  (пишет     │         ┌──────────────────┐
│   статус)   │ ◄─────► │monitor_commands  │
└─────────────┘         │     .json        │
                        └──────────────────┘
                               ▲
                               │
                        ┌──────┴───────┐
                        │  monitor.py  │
                        │  (читает и   │
                        │   отправляет │
                        │   команды)   │
                        └──────────────┘
```

### Файлы обмена данными

**monitor_stats.json** - Бот записывает сюда статистику:
```json
{
  "status": "running",
  "uptime": 3600,
  "users_total": 25,
  "users_active": 5,
  "dse_total": 150,
  "requests_total": 1234,
  "requests_per_minute": 12.5,
  "memory_mb": 125.6,
  "last_update": "2025-10-17 15:30:45"
}
```

**monitor_commands.json** - Монитор пишет команды для бота:
```json
{
  "commands": [
    {"cmd": "reload_stats", "timestamp": "2025-10-17 15:30:00"},
    {"cmd": "clear_cache", "timestamp": "2025-10-17 15:31:00"}
  ]
}
```

**bot_monitor.log** - Логи бота для отображения в мониторе

## 🛠️ Установка зависимостей

Монитор использует стандартные библиотеки Python + `psutil` для мониторинга системы:

```bash
# Установка через pip
pip install psutil

# Или через requirements.txt
pip install -r requirements.txt
```

## ⚠️ Важные замечания

1. **Независимость**: Монитор работает независимо от бота. Если бот остановлен, монитор всё равно работает.

2. **Обновление данных**: Бот обновляет статистику каждые 5 секунд. Монитор читает данные каждые 2 секунды.

3. **Команды**: Команды от монитора обрабатываются ботом асинхронно. Результат может быть не мгновенным.

4. **Логи**: По умолчанию показываются последние 100 строк. Для полных логов используйте:
   ```bash
   tail -f bot_monitor.log
   ```

5. **Производительность**: Монитор потребляет минимум ресурсов и не влияет на работу бота.

## 🐛 Решение проблем

### Монитор не запускается
```bash
# Проверьте права доступа
chmod +x start_monitor.sh

# Проверьте Python версию (нужен 3.7+)
python3 --version

# Установите psutil
pip3 install psutil
```

### Нет данных в мониторе
- Убедитесь, что бот запущен: `systemctl status telegrambot`
- Проверьте наличие файла: `ls -la monitor_stats.json`
- Проверьте логи бота: `journalctl -u telegrambot -f`

### Команды не работают
- Проверьте права на запись: `ls -la monitor_commands.json`
- Убедитесь, что бот читает команды (в логах должны быть записи об обработке команд)

## 📚 Интеграция с systemd

Можно запустить монитор как systemd службу:

```bash
sudo nano /etc/systemd/system/telegrambot-monitor.service
```

```ini
[Unit]
Description=TelegrammBolt Monitor
After=telegrambot.service

[Service]
Type=simple
User=telegrambot
WorkingDirectory=/opt/telegrambot
Environment="TERM=xterm-256color"
ExecStart=/opt/telegrambot/.venv/bin/python /opt/telegrambot/monitor.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegrambot-monitor
sudo systemctl start telegrambot-monitor
```

## 📊 Примеры использования

### Мониторинг в фоне с логированием
```bash
./start_monitor.sh > monitor_output.log 2>&1 &
```

### Запуск через tmux/screen
```bash
# Через tmux
tmux new -s bot-monitor
./start_monitor.sh

# Через screen
screen -S bot-monitor
./start_monitor.sh
```

### SSH туннель для удалённого мониторинга
```bash
ssh -t user@server "cd /opt/telegrambot && ./start_monitor.sh"
```

---

**Разработчик**: TelegrammBolt Team  
**Версия**: 1.0  
**Лицензия**: MIT
