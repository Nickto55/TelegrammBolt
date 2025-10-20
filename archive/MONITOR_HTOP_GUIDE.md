# TelegrammBolt Monitor - htop-style Interface

## Overview

Монитор теперь имеет интерфейс в стиле **htop** с цветным оформлением, прогресс-барами и улучшенной навигацией.

## Color Scheme

### Цветовая палитра:
- **Cyan** (голубой) - Заголовки, информация
- **Green** (зеленый) - Успех, активные элементы, running status
- **Yellow** (желтый) - Предупреждения, ожидание
- **Red** (красный) - Ошибки, критические состояния
- **Magenta** (пурпурный) - Специальные элементы
- **Blue** (синий) - Футер, неактивные вкладки

### Статусы:
- `RUNNING` - зеленый (бот активен)
- `STOPPED` - красный (бот остановлен)
- `[OK]` - зеленый (команда выполнена)
- `[ERR]` - красный (ошибка)
- `[WRN]` - желтый (предупреждение)
- `[...]` - желтый (в процессе)

## Interface Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ TelegrammBolt Monitor                          2025-10-17 15:30:00  │ <- Cyan header
├─────────────────────────────────────────────────────────────────────┤
│ [1] Stats  [2] Logs  [3] Users  [4] Control                        │ <- Tabs
│═════════════════════════════════════════════════════════════════════│
│                                                                     │
│  Content Area (varies by tab)                                      │
│  - Progress bars with color indication                              │
│  - Color-coded logs                                                 │
│  - Formatted tables                                                 │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ F1 Help  F5 Refresh  Tab Next  Q Quit                              │ <- Blue footer
└─────────────────────────────────────────────────────────────────────┘
```

## Tab 1: Statistics

### Features:
- **BOT STATUS** section with colored status indicator
- **Uptime** in HH:MM:SS format
- **RESOURCES** section with progress bars:
  - Memory usage (green/yellow/red based on usage)
  - Requests per minute rate
- **STATISTICS** section with key metrics in 2 columns

### Progress Bars:
```
Memory [125.6MB]: ████████████░░░░░░░░  65.3%
Req/min [12.5]  : ████░░░░░░░░░░░░░░░░  12.5%
```

Colors:
- Green: 0-50%
- Yellow: 50-80%
- Red: 80-100%

## Tab 2: Logs

### Features:
- Color-coded log levels:
  - `[ERR]` - Red - Errors
  - `[WRN]` - Yellow - Warnings
  - `[OK ]` - Green - Success messages
  - `[INF]` - Cyan - Information
  - `[---]` - Default - Other
- Scroll position indicator (e.g., `[65%]`)
- Auto-refresh every 2 seconds

### Example:
```
RECENT LOGS (45 entries)                    [UP/DOWN to scroll]
----------------------------------------------------------------
[INF] 2025-10-17 15:00:00 - Bot started
[OK ] 2025-10-17 15:01:00 - Services initialized
[WRN] 2025-10-17 15:02:00 - High server load
[ERR] 2025-10-17 15:03:00 - Database connection failed
```

## Tab 3: Users

### Features:
- Table format with columns:
  - User ID
  - Username (ASCII-safe)
  - Role
- Scroll through users list
- Up to 20 users displayed

## Tab 4: Control Panel

### Features:
- **Available commands** section with:
  - Colored key bindings
  - Command names in green
  - Detailed descriptions
- **Command history** section with:
  - Status indicators (OK/ERR/...)
  - Command names
  - Timestamps

### Example:
```
CONTROL PANEL
----------------------------------------------------------------
Available commands:

 [R]  Restart watcher    - Restart DSE monitoring service
 [C]  Clear cache        - Clear all cached data
 [S]  Save stats         - Force save current statistics

COMMAND HISTORY
----------------------------------------------------------------
[OK]  restart_watcher     2025-10-17 15:30:00
[...] clear_cache         2025-10-17 15:31:00
```

## Navigation

### Keyboard Shortcuts:
```
Tab / →       - Next tab
Shift+Tab / ← - Previous tab
↑ / ↓        - Scroll up/down in logs or users
PgUp / PgDn   - Page scroll (if implemented)
Home          - Jump to start
End           - Jump to end
F1            - Help (shows this guide)
F5            - Force refresh
Q / Ctrl+C    - Quit
```

### Tab-specific keys:
**Control tab ([4]):**
- `R` - Restart watcher
- `C` - Clear cache
- `S` - Save statistics
- `L` - Clear logs
- `E` - Export data
- `T` - Test notifications

## Terminal Requirements

### Minimum size:
- Width: 80 characters
- Height: 20 lines

### Recommended:
- Width: 100+ characters
- Height: 30+ lines

### If terminal is too small:
```
Terminal too small! Min: 80x20
```

## Performance

- **Update interval**: 2 seconds
- **CPU usage**: <1%
- **Memory**: ~5-10 MB
- **Non-blocking**: Bot continues running independently

## Tips & Tricks

### 1. Full-screen mode
Use terminal in full-screen for best experience:
```bash
# Linux
Alt+F11 (toggle fullscreen in most terminals)

# Or maximize window
```

### 2. Color test
If colors don't work:
```bash
# Check terminal support
echo $TERM

# Should be xterm-256color or similar
export TERM=xterm-256color
```

### 3. Persistent monitoring
Run in tmux/screen:
```bash
tmux new -s monitor
python3 monitor.py

# Detach: Ctrl+B, D
# Attach: tmux attach -t monitor
```

### 4. Remote monitoring
SSH with terminal forwarding:
```bash
ssh -t user@server "cd /opt/telegrambot && python3 monitor.py"
```

## Troubleshooting

### Colors not showing
```bash
# Enable 256 color support
export TERM=xterm-256color

# Or
export TERM=screen-256color
```

### Progress bars broken
- Resize terminal to minimum 80 columns
- Check that terminal supports Unicode

### Slow updates
- Normal - updates every 2 seconds
- Bot updates stats every 5 seconds
- Network lag may affect remote SSH

## Comparison with htop

| Feature | htop | TelegrammBolt Monitor |
|---------|------|----------------------|
| Process list | ✅ | ❌ (shows bot stats) |
| CPU/Memory | ✅ | ✅ (memory only) |
| Color coding | ✅ | ✅ |
| Progress bars | ✅ | ✅ |
| Sorting | ✅ | ❌ |
| Tree view | ✅ | ❌ |
| Kill process | ✅ | ❌ |
| Custom metrics | ❌ | ✅ (bot-specific) |
| Log viewing | ❌ | ✅ |
| Control panel | ❌ | ✅ |

## ASCII Art

If terminal supports, you can add ASCII art to startup:
```
  _____ ____        _     __  __             _ _             
 |_   _| __ )      |  \/  | ___  _ __ (_) |_ ___  _ __ 
   | | |  _ \ _____| |\/| |/ _ \| '_ \| | __/ _ \| '__|
   | | | |_) |_____| |  | | (_) | | | | | || (_) | |   
   |_| |____/      |_|  |_|\___/|_| |_|_|\__\___/|_|   
```

---

**Version**: 2.0 (htop-style)  
**Platform**: Linux only  
**Python**: 3.7+  
**Dependencies**: psutil, curses (standard library)
