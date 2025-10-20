# Решение проблемы: Черный экран в monitor.py

## Проблема
```bash
python monitor.py
# Показывает только черный экран
```

---

## Причины черного экрана

### 1. **Нет файлов данных** ⭐ САМАЯ ЧАСТАЯ
Монитор не может отобразить данные, потому что нет файла `monitor_stats.json`.

**Решение:**
```bash
# Создать тестовые данные
python test_monitor_data.py

# Запустить монитор
python monitor.py
```

### 2. **Терминал слишком маленький**
Минимальный размер: **80 столбцов × 20 строк**

**Проверка:**
```bash
# Узнать размер терминала
tput cols  # Должно быть >= 80
tput lines # Должно быть >= 20
```

**Решение:**
- Разверните терминал на весь экран
- Или: `resize -s 30 100` (30 строк, 100 столбцов)

### 3. **Бот не запущен**
Если бот не работает, монитор показывает пустые данные (может выглядеть как черный экран).

**Проверка:**
```bash
ps aux | grep bot.py
```

**Решение:**
```bash
python bot.py &
```

### 4. **Ошибка curses**
На некоторых терминалах curses может не работать.

**Проверка:**
```bash
python -c "import curses; print('OK')"
```

**Решение:**
- Используйте стандартный терминал (не Midnight Commander, не screen без настройки)
- Установите: `export TERM=xterm-256color`

---

## ✅ Правильный запуск (пошагово)

### На сервере Ubuntu/Debian:

```bash
# 1. Перейти в папку проекта
cd /opt/telegrambot

# 2. Активировать venv (если есть)
source .venv/bin/activate

# 3. Создать тестовые данные (если бот не запущен)
python test_monitor_data.py

# 4. Запустить монитор
bash start_monitor.sh
```

### Или просто:

```bash
cd /opt/telegrambot
bash start_monitor.sh
```

Скрипт автоматически:
- Активирует venv
- Установит psutil (если нужно)
- Создаст тестовые данные (если нужно)
- Запустит монитор

---

## 🔍 Диагностика

### Проверка 1: Есть ли файлы данных?

```bash
ls -lh monitor_stats.json monitor_commands.json bot_monitor.log
```

Если файлов нет - создайте:
```bash
python test_monitor_data.py
```

### Проверка 2: Размер терминала

```bash
echo "Columns: $(tput cols), Lines: $(tput lines)"
```

Должно быть:
```
Columns: 80 (или больше), Lines: 20 (или больше)
```

### Проверка 3: Curses работает?

```bash
python << 'PYTHON'
import curses
def test(stdscr):
    stdscr.addstr(0, 0, "Curses works!")
    stdscr.refresh()
    stdscr.getch()
curses.wrapper(test)
PYTHON
```

Если видите "Curses works!" - всё ОК.

### Проверка 4: Содержимое данных

```bash
cat monitor_stats.json
```

Должен быть валидный JSON:
```json
{
  "status": "running",
  "uptime": 3600,
  ...
}
```

---

## 🛠️ Исправление

### Если нет данных:

```bash
# Создать тестовые файлы
python test_monitor_data.py

# Проверить что созданы
ls -lh monitor*.json bot_monitor.log

# Запустить монитор
python monitor.py
```

### Если терминал маленький:

```bash
# Вариант 1: Развернуть окно терминала
# (Alt+F11 или кнопка "Развернуть")

# Вариант 2: Изменить размер командой
resize -s 30 100

# Запустить монитор
python monitor.py
```

### Если TERM не настроен:

```bash
# Установить правильный TERM
export TERM=xterm-256color

# Добавить в ~/.bashrc для постоянства
echo 'export TERM=xterm-256color' >> ~/.bashrc

# Запустить монитор
python monitor.py
```

---

## 📊 Что должно быть видно

После запуска должен появиться интерфейс:

```
┌──────────────────────────────────────────────────────────┐
│ TelegrammBolt Monitor              2025-10-17 15:30:00   │
├──────────────────────────────────────────────────────────┤
│ [1] Stats  [2] Logs  [3] Users  [4] Control             │
│══════════════════════════════════════════════════════════│
│                                                          │
│  BOT STATUS                                              │
│  Status: RUNNING                                         │
│  Uptime: 01:23:45                                        │
│                                                          │
│  RESOURCES                                               │
│  Memory [125.6MB]: ████████████░░░░░░░░  65%             │
│  Req/min [12.5]:   ████░░░░░░░░░░░░░░░░  13%             │
│                                                          │
│  STATISTICS                                              │
│  Total Users:        25    DSE Records:       150        │
│  Active Users:        5    Total Requests:   1234        │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ F1 Help  F5 Refresh  Tab Next  Q Quit                   │
└──────────────────────────────────────────────────────────┘
```

---

## ❌ Не показывает интерфейс?

### Запустите с отладкой:

```bash
python monitor.py 2>&1 | tee monitor_debug.log
```

Проверьте лог:
```bash
cat monitor_debug.log
```

Должно быть:
```
==========================================
TelegrammBolt Monitor - Starting...
==========================================

Terminal requirements: minimum 80x20
Controls: Tab/Arrows - navigate, Q - quit

Starting in 2 seconds...
```

Если ошибки - пришлите мне вывод.

---

## 💡 Обновление от 17 октября 2025

Теперь **monitor.py автоматически**:
- ✅ Создаёт тестовые данные если их нет
- ✅ Показывает понятные сообщения об ошибках
- ✅ Проверяет размер терминала
- ✅ Выводит инструкции перед запуском

Просто запустите:
```bash
python monitor.py
```

Всё должно заработать автоматически!

---

## 🚀 Быстрые команды

```bash
# Полная последовательность
cd /opt/telegrambot
source .venv/bin/activate
python test_monitor_data.py
python monitor.py

# Или через скрипт
bash start_monitor.sh

# С увеличенным терминалом
resize -s 30 100 && python monitor.py

# С отладкой
python monitor.py 2>&1 | tee debug.log
```

---

## 📋 Чеклист

- [ ] На Linux/Unix (не Windows)
- [ ] Терминал >= 80x20
- [ ] Файл monitor_stats.json существует
- [ ] TERM=xterm-256color установлен
- [ ] Curses работает (тест выше)
- [ ] Запускаю в обычном терминале (не mc/screen)

Если все ✅ - монитор заработает!

---

**Главное:** Запускайте `bash start_monitor.sh` на **Linux сервере**, а не на Windows! 🚀
