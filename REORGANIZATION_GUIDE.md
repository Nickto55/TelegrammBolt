# 🔄 Руководство по реорганизации проекта

## 📁 Новая структура проекта

```
TelegrammBolt/
├── src/                          # 📦 Исходный код приложения
│   ├── __init__.py
│   ├── bot/                      # 🤖 Telegram бот
│   │   ├── __init__.py
│   │   ├── bot.py               # Главный файл бота
│   │   ├── commands.py          # Команды и обработчики
│   │   └── config.py            # Конфигурация
│   │
│   ├── managers/                 # 👥 Менеджеры бизнес-логики
│   │   ├── __init__.py
│   │   ├── user_manager.py      # Управление пользователями
│   │   ├── chat_manager.py      # Управление чатами
│   │   ├── dse_manager.py       # Управление ДСЕ
│   │   ├── dse_watcher.py       # Мониторинг ДСЕ
│   │   └── email_manager.py     # Email рассылка
│   │
│   ├── utils/                    # 🛠️ Утилиты
│   │   ├── __init__.py
│   │   ├── pdf_generator.py     # Генерация PDF
│   │   ├── genereteTabl.py      # Генерация Excel
│   │   └── gui_manager.py       # GUI (если нужен)
│   │
│   └── web/                      # 🌐 Веб-приложение
│       ├── __init__.py
│       ├── web_app.py           # Flask приложение
│       ├── windows_service.py   # Windows сервис
│       ├── static/              # Статические файлы (CSS, JS)
│       │   ├── css/
│       │   │   └── style.css
│       │   └── js/
│       │       └── app.js
│       └── templates/           # HTML шаблоны
│           ├── base.html
│           ├── dashboard.html
│           └── login.html
│
├── config/                       # ⚙️ Конфигурационные файлы (примеры)
│   ├── ven_bot.json.example     # Пример конфига бота
│   ├── smtp_config.json.example # Пример конфига SMTP
│   ├── nginx.conf               # Конфиг Nginx
│   ├── nginx-ssl.conf           # Конфиг Nginx с SSL
│   ├── telegrambot.service      # Systemd service файл
│   └── installer.nsi            # NSIS installer
│
├── data/                         # 💾 Данные приложения (игнорируются git)
│   ├── .gitkeep
│   ├── ven_bot.json             # Активный конфиг бота
│   ├── smtp_config.json         # Активный конфиг SMTP
│   ├── bot_data.json            # Данные бота
│   ├── users_data.json          # Данные пользователей
│   ├── chat_data.json           # Данные чатов
│   ├── watched_dse.json         # Отслеживаемые ДСЕ
│   ├── *.xlsx                   # Excel отчеты
│   ├── *.pdf                    # PDF отчеты
│   └── photos/                  # Фотографии
│
├── docs/                         # 📚 Документация
│   ├── CHEATSHEET.md            # Шпаргалка
│   ├── INSTALLATION.md          # Руководство по установке
│   ├── TROUBLESHOOTING.md       # Решение проблем
│   ├── QUICK_FIX.md             # Быстрые исправления
│   ├── HTTPS_SETUP.md           # Настройка HTTPS
│   ├── HTTPS_QUICK_SETUP.txt    # Быстрая настройка HTTPS
│   └── DOCKER_TROUBLESHOOTING.md# Проблемы с Docker
│
├── scripts/                      # 📜 Скрипты установки и управления
│   ├── setup.sh                 # Основной установочный скрипт
│   ├── setup_minimal.sh         # Минимальная установка
│   ├── setup-https.sh           # Установка с HTTPS
│   ├── start_bot.sh             # Запуск бота (Linux)
│   ├── start_bot.bat            # Запуск бота (Windows)
│   ├── cleanup-bot.sh           # Очистка бота
│   ├── cleanup-docs.sh          # Очистка документации
│   ├── cleanup-docs.ps1         # Очистка документации (PS)
│   ├── check_installation.sh    # Проверка установки
│   ├── show-web-url.sh          # Показать URL веб-интерфейса
│   ├── restructure.sh           # Реструктуризация проекта
│   └── add-pdf-menu-function.sh # Добавить функцию PDF меню
│
├── .gitignore                    # Git ignore правила
├── requirements.txt              # Python зависимости
├── README.md                     # Главная документация
├── LICENSE                       # Лицензия
├── reorganize.ps1                # Скрипт реорганизации (этот файл)
└── REORGANIZATION_GUIDE.md       # Это руководство

```

---

## 🚀 Как выполнить реорганизацию

### Автоматически (PowerShell на Windows)

```powershell
cd C:\Users\truni\PycharmProjects\TelegrammBolt
.\reorganize.ps1
```

### Автоматически (Bash на Linux/Mac)

```bash
cd /path/to/TelegrammBolt

# Создать скрипт
cat > reorganize.sh << 'EOF'
#!/bin/bash
# Аналогичный скрипт для bash
EOF

chmod +x reorganize.sh
./reorganize.sh
```

### Вручную

Если автоматический скрипт не работает, выполните вручную:

```powershell
# 1. Создать директории
mkdir src, src\bot, src\managers, src\utils, src\web
mkdir config, data, docs, scripts

# 2. Переместить файлы бота
Move-Item bot.py src\bot\
Move-Item commands.py src\bot\
Move-Item config.py src\bot\

# 3. Переместить managers
Move-Item user_manager.py src\managers\
Move-Item chat_manager.py src\managers\
Move-Item dse_manager.py src\managers\
Move-Item dse_watcher.py src\managers\
Move-Item email_manager.py src\managers\

# 4. Переместить utils
Move-Item pdf_generator.py src\utils\
Move-Item genereteTabl.py src\utils\
Move-Item gui_manager.py src\utils\

# 5. Переместить web
Move-Item web_app.py src\web\
Move-Item windows_service.py src\web\
Move-Item static src\web\
Move-Item templates src\web\

# 6. Переместить документацию
Move-Item *.md docs\
Move-Item HTTPS_QUICK_SETUP.txt docs\

# 7. Переместить скрипты
Move-Item *.sh scripts\
Move-Item *.bat scripts\
Move-Item *.ps1 scripts\

# 8. Переместить конфиги
Move-Item *.example config\
Move-Item *.conf config\
Move-Item *.service config\
Move-Item *.nsi config\

# 9. Переместить данные
Move-Item *.json data\
Move-Item *.xlsx data\
Move-Item *.pdf data\
Move-Item photos data\

# 10. Удалить устаревшие файлы
Remove-Item commands_handlers.py
Remove-Item update_imports.py
Remove-Item .docs_backup_* -Recurse
```

---

## 🔧 После реорганизации

### 1. Обновление импортов

**Старый стиль:**
```python
from user_manager import get_user_role
from dse_manager import get_all_dse_records
from config import load_data
```

**Новый стиль:**
```python
from src.managers.user_manager import get_user_role
from src.managers.dse_manager import get_all_dse_records
from src.bot.config import load_data
```

### 2. Создание файлов-заглушек в корне (опционально)

Для обратной совместимости можно создать заглушки:

**bot.py** (в корне):
```python
#!/usr/bin/env python3
"""Точка входа - запуск бота"""
from src.bot.bot import main

if __name__ == "__main__":
    main()
```

### 3. Обновление путей в конфигах

**Обновить `config/telegrambot.service`:**
```ini
[Service]
WorkingDirectory=/opt/TelegrammBolt
ExecStart=/opt/TelegrammBolt/.venv/bin/python src/bot/bot.py
```

**Обновить скрипты запуска:**
```bash
# scripts/start_bot.sh
python3 src/bot/bot.py
```

### 4. Создать .gitkeep файлы

```bash
touch data/.gitkeep
touch data/photos/.gitkeep
```

### 5. Обновить README.md

Обновить примеры кода и пути в документации.

---

## ✅ Проверка после реорганизации

```powershell
# 1. Проверить структуру
tree /F

# 2. Проверить импорты
python -m py_compile src/bot/bot.py

# 3. Проверить запуск
python src/bot/bot.py

# 4. Проверить веб
python src/web/web_app.py
```

---

## 🔄 Откат изменений

Если что-то пошло не так:

```bash
git reset --hard HEAD
git clean -fd
```

Или восстановить из backup:
```bash
cp -r .backup/* .
```

---

## 📝 Что удалено

### Устаревшие файлы:
- ❌ `commands_handlers.py` - дубликат функциональности
- ❌ `update_imports.py` - одноразовый скрипт
- ❌ `.docs_backup_*` - старые бэкапы

### Что НЕ удалено (оставлено для совместимости):
- ✅ `.idea/` - настройки IDE (в .gitignore)
- ✅ `.venv/` - виртуальное окружение (в .gitignore)
- ✅ `__pycache__/` - Python кэш (в .gitignore)

---

## 🎯 Преимущества новой структуры

1. **🗂️ Организованность** - Каждый тип файлов в своей папке
2. **🔍 Легкость навигации** - Быстро найти нужный модуль
3. **📦 Модульность** - Четкое разделение ответственности
4. **🧪 Тестируемость** - Проще писать тесты
5. **📚 Документированность** - Вся документация в одном месте
6. **🚀 Масштабируемость** - Легко добавлять новые модули
7. **🔒 Безопасность** - Данные отделены от кода
8. **🐳 Docker-ready** - Удобная структура для контейнеризации

---

## 🆘 Помощь

Если возникли проблемы:
1. Проверьте `docs/TROUBLESHOOTING.md`
2. Создайте issue на GitHub
3. Проверьте права доступа к файлам
4. Убедитесь что все зависимости установлены

---

**Автор:** Nickto55  
**Дата:** 17 октября 2025 г.  
**Версия:** 2.0
