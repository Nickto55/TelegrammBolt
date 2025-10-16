#!/bin/bash

# Скрипт автоматической реструктуризации проекта TelegrammBolt
# Запускать из корня проекта

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   TelegrammBolt Restructure Script        ║${NC}"
echo -e "${BLUE}║   Автоматическая реорганизация проекта    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Проверка, что мы в корне проекта
if [ ! -f "bot.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Ошибка: Запустите скрипт из корня проекта TelegrammBolt${NC}"
    exit 1
fi

# Запрос подтверждения
echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Этот скрипт изменит структуру проекта${NC}"
echo -e "${YELLOW}   Рекомендуется создать резервную копию перед продолжением${NC}"
echo ""
read -p "Продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Отменено${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}▶${NC} Начинаем реструктуризацию..."
echo ""

# Создание резервной копии
echo -e "${BLUE}▶${NC} Создание резервной копии..."
BACKUP_DIR="../TelegrammBolt_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r ./* "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Резервная копия создана: $BACKUP_DIR"
echo ""

# Фаза 1: Создание структуры директорий
echo -e "${BLUE}▶${NC} Создание структуры директорий..."

mkdir -p src/bot/{handlers,managers,workers,utils}
mkdir -p src/web/{routes,static/{css,js,img},templates}
mkdir -p src/shared
mkdir -p config
mkdir -p data/photos
mkdir -p scripts/{setup,maintenance,start,build}
mkdir -p services/{systemd,init.d}
mkdir -p docs/{installation,configuration,troubleshooting,guides,reference}
mkdir -p tests

echo -e "${GREEN}✓${NC} Структура создана"
echo ""

# Фаза 2: Создание __init__.py файлов
echo -e "${BLUE}▶${NC} Создание __init__.py файлов..."

touch src/__init__.py
touch src/bot/__init__.py
touch src/bot/handlers/__init__.py
touch src/bot/managers/__init__.py
touch src/bot/workers/__init__.py
touch src/bot/utils/__init__.py
touch src/web/__init__.py
touch src/web/routes/__init__.py
touch src/shared/__init__.py
touch tests/__init__.py

echo -e "${GREEN}✓${NC} __init__.py файлы созданы"
echo ""

# Фаза 3: Перемещение исходного кода
echo -e "${BLUE}▶${NC} Перемещение исходного кода..."

# Bot
[ -f "bot.py" ] && mv bot.py src/bot/main.py && echo "  ✓ bot.py → src/bot/main.py"
[ -f "commands.py" ] && mv commands.py src/bot/handlers/ && echo "  ✓ commands.py → src/bot/handlers/"
[ -f "commands_handlers.py" ] && mv commands_handlers.py src/bot/handlers/ && echo "  ✓ commands_handlers.py → src/bot/handlers/"

# Managers
[ -f "user_manager.py" ] && mv user_manager.py src/bot/managers/ && echo "  ✓ user_manager.py → src/bot/managers/"
[ -f "chat_manager.py" ] && mv chat_manager.py src/bot/managers/ && echo "  ✓ chat_manager.py → src/bot/managers/"
[ -f "dse_manager.py" ] && mv dse_manager.py src/bot/managers/ && echo "  ✓ dse_manager.py → src/bot/managers/"
[ -f "gui_manager.py" ] && mv gui_manager.py src/bot/managers/ && echo "  ✓ gui_manager.py → src/bot/managers/"

# Workers
[ -f "dse_watcher.py" ] && mv dse_watcher.py src/bot/workers/ && echo "  ✓ dse_watcher.py → src/bot/workers/"

# Utils
[ -f "config.py" ] && mv config.py src/bot/utils/ && echo "  ✓ config.py → src/bot/utils/"
[ -f "pdf_generator.py" ] && mv pdf_generator.py src/bot/utils/ && echo "  ✓ pdf_generator.py → src/bot/utils/"
[ -f "genereteTabl.py" ] && mv genereteTabl.py src/bot/utils/excel_generator.py && echo "  ✓ genereteTabl.py → src/bot/utils/excel_generator.py"

# Web
[ -f "web_app.py" ] && mv web_app.py src/web/app.py && echo "  ✓ web_app.py → src/web/app.py"
[ -d "templates" ] && mv templates/* src/web/templates/ 2>/dev/null && rmdir templates && echo "  ✓ templates → src/web/templates/"
[ -d "static" ] && mv static/* src/web/static/ 2>/dev/null && rmdir static && echo "  ✓ static → src/web/static/"

echo -e "${GREEN}✓${NC} Исходный код перемещен"
echo ""

# Фаза 4: Перемещение конфигурации
echo -e "${BLUE}▶${NC} Перемещение конфигурации..."

[ -f "ven_bot.json" ] && mv ven_bot.json config/ && echo "  ✓ ven_bot.json → config/"
[ -f "ven_bot.json.example" ] && mv ven_bot.json.example config/ && echo "  ✓ ven_bot.json.example → config/"
[ -f "smtp_config.json" ] && mv smtp_config.json config/ && echo "  ✓ smtp_config.json → config/"
[ -f "smtp_config.json.example" ] && mv smtp_config.json.example config/ && echo "  ✓ smtp_config.json.example → config/"
[ -f "nginx.conf" ] && mv nginx.conf config/ && echo "  ✓ nginx.conf → config/"

echo -e "${GREEN}✓${NC} Конфигурация перемещена"
echo ""

# Фаза 5: Перемещение данных
echo -e "${BLUE}▶${NC} Перемещение данных..."

[ -f "bot_data.json" ] && mv bot_data.json data/ && echo "  ✓ bot_data.json → data/"
[ -f "users_data.json" ] && mv users_data.json data/ && echo "  ✓ users_data.json → data/"
[ -f "RezultBot.xlsx" ] && mv RezultBot.xlsx data/ && echo "  ✓ RezultBot.xlsx → data/"
[ -f "test_report.pdf" ] && mv test_report.pdf data/ && echo "  ✓ test_report.pdf → data/"
[ -d "photos" ] && mv photos/* data/photos/ 2>/dev/null && rmdir photos && echo "  ✓ photos → data/photos/"

echo -e "${GREEN}✓${NC} Данные перемещены"
echo ""

# Фаза 6: Перемещение скриптов
echo -e "${BLUE}▶${NC} Перемещение скриптов..."

# Setup
[ -f "setup.sh" ] && mv setup.sh scripts/setup/ && echo "  ✓ setup.sh → scripts/setup/"
[ -f "setup_minimal.sh" ] && mv setup_minimal.sh scripts/setup/ && echo "  ✓ setup_minimal.sh → scripts/setup/"
[ -f "check_installation.sh" ] && mv check_installation.sh scripts/setup/ && echo "  ✓ check_installation.sh → scripts/setup/"

# Maintenance
[ -f "cleanup-bot.sh" ] && mv cleanup-bot.sh scripts/maintenance/ && echo "  ✓ cleanup-bot.sh → scripts/maintenance/"
[ -f "fix-bot-errors.sh" ] && mv fix-bot-errors.sh scripts/maintenance/ && echo "  ✓ fix-bot-errors.sh → scripts/maintenance/"
[ -f "emergency-fix.sh" ] && mv emergency-fix.sh scripts/maintenance/ && echo "  ✓ emergency-fix.sh → scripts/maintenance/"
[ -f "add-pdf-menu-function.sh" ] && mv add-pdf-menu-function.sh scripts/maintenance/ && echo "  ✓ add-pdf-menu-function.sh → scripts/maintenance/"
[ -f "show-web-url.sh" ] && mv show-web-url.sh scripts/maintenance/ && echo "  ✓ show-web-url.sh → scripts/maintenance/"

# Start
[ -f "start_bot.sh" ] && mv start_bot.sh scripts/start/ && echo "  ✓ start_bot.sh → scripts/start/"
[ -f "start_bot.bat" ] && mv start_bot.bat scripts/start/ && echo "  ✓ start_bot.bat → scripts/start/"

# Build
[ -f "installer.nsi" ] && mv installer.nsi scripts/build/ && echo "  ✓ installer.nsi → scripts/build/"

echo -e "${GREEN}✓${NC} Скрипты перемещены"
echo ""

# Фаза 7: Перемещение служб
echo -e "${BLUE}▶${NC} Перемещение служб..."

[ -f "telegrambot.service" ] && mv telegrambot.service services/systemd/ && echo "  ✓ telegrambot.service → services/systemd/"

echo -e "${GREEN}✓${NC} Службы перемещены"
echo ""

# Фаза 8: Перемещение документации
echo -e "${BLUE}▶${NC} Перемещение документации..."

# Installation
[ -f "README_Ubuntu.md" ] && mv README_Ubuntu.md docs/installation/ && echo "  ✓ README_Ubuntu.md → docs/installation/"
[ -f "QUICKSTART_Ubuntu.md" ] && mv QUICKSTART_Ubuntu.md docs/installation/ && echo "  ✓ QUICKSTART_Ubuntu.md → docs/installation/"
[ -f "QUICKSTART_Debian.md" ] && mv QUICKSTART_Debian.md docs/installation/ && echo "  ✓ QUICKSTART_Debian.md → docs/installation/"
[ -f "INSTALL_FROM_WEB_BRANCH.md" ] && mv INSTALL_FROM_WEB_BRANCH.md docs/installation/ && echo "  ✓ INSTALL_FROM_WEB_BRANCH.md → docs/installation/"
[ -f "NO_SYSTEMD.md" ] && mv NO_SYSTEMD.md docs/installation/ && echo "  ✓ NO_SYSTEMD.md → docs/installation/"

# Configuration
[ -f "SMTP_SETUP_INSTRUCTIONS.md" ] && mv SMTP_SETUP_INSTRUCTIONS.md docs/configuration/ && echo "  ✓ SMTP_SETUP_INSTRUCTIONS.md → docs/configuration/"
[ -f "WEB_SETUP.md" ] && mv WEB_SETUP.md docs/configuration/ && echo "  ✓ WEB_SETUP.md → docs/configuration/"

# Troubleshooting
[ -f "PYTHON_VERSION_FIX.md" ] && mv PYTHON_VERSION_FIX.md docs/troubleshooting/ && echo "  ✓ PYTHON_VERSION_FIX.md → docs/troubleshooting/"
[ -f "DOCKER_PYTHON_FIX.md" ] && mv DOCKER_PYTHON_FIX.md docs/troubleshooting/ && echo "  ✓ DOCKER_PYTHON_FIX.md → docs/troubleshooting/"
[ -f "FIX_CONFLICT_ERROR.md" ] && mv FIX_CONFLICT_ERROR.md docs/troubleshooting/ && echo "  ✓ FIX_CONFLICT_ERROR.md → docs/troubleshooting/"
[ -f "DOCKER_CONFLICT_FIX.md" ] && mv DOCKER_CONFLICT_FIX.md docs/troubleshooting/ && echo "  ✓ DOCKER_CONFLICT_FIX.md → docs/troubleshooting/"
[ -f "QUICK_FIX.md" ] && mv QUICK_FIX.md docs/troubleshooting/ && echo "  ✓ QUICK_FIX.md → docs/troubleshooting/"
[ -f "QUICK_ERROR_FIX.md" ] && mv QUICK_ERROR_FIX.md docs/troubleshooting/ && echo "  ✓ QUICK_ERROR_FIX.md → docs/troubleshooting/"
[ -f "FIXES_SUMMARY.md" ] && mv FIXES_SUMMARY.md docs/troubleshooting/ && echo "  ✓ FIXES_SUMMARY.md → docs/troubleshooting/"

# Guides
[ -f "WEB_QUICKSTART.md" ] && mv WEB_QUICKSTART.md docs/guides/ && echo "  ✓ WEB_QUICKSTART.md → docs/guides/"
[ -f "WEB_SUMMARY.md" ] && mv WEB_SUMMARY.md docs/guides/ && echo "  ✓ WEB_SUMMARY.md → docs/guides/"
[ -f "GET_WEB_URL.md" ] && mv GET_WEB_URL.md docs/guides/ && echo "  ✓ GET_WEB_URL.md → docs/guides/"
[ -f "DEPLOYMENT_GUIDE.md" ] && mv DEPLOYMENT_GUIDE.md docs/guides/ && echo "  ✓ DEPLOYMENT_GUIDE.md → docs/guides/"
[ -f "START_HERE.md" ] && mv START_HERE.md docs/guides/ && echo "  ✓ START_HERE.md → docs/guides/"
[ -f "README_WEB_BRANCH.md" ] && mv README_WEB_BRANCH.md docs/guides/ && echo "  ✓ README_WEB_BRANCH.md → docs/guides/"

# Reference
[ -f "CHEATSHEET.md" ] && mv CHEATSHEET.md docs/reference/ && echo "  ✓ CHEATSHEET.md → docs/reference/"
[ -f "PROJECT_STRUCTURE.md" ] && mv PROJECT_STRUCTURE.md docs/reference/ && echo "  ✓ PROJECT_STRUCTURE.md → docs/reference/"
[ -f "CHANGELOG.md" ] && mv CHANGELOG.md docs/reference/ && echo "  ✓ CHANGELOG.md → docs/reference/"

echo -e "${GREEN}✓${NC} Документация перемещена"
echo ""

# Фаза 9: Создание новых файлов
echo -e "${BLUE}▶${NC} Создание новых файлов..."

# Главный README.md
cat > README.md << 'EOF'
# 🤖 TelegrammBolt

Telegram бот для управления заявками ДСЕ с веб-интерфейсом

## 📋 Возможности

- ✅ Управление заявками ДСЕ через Telegram
- ✅ Веб-интерфейс для администрирования
- ✅ Генерация отчетов (Excel, PDF)
- ✅ Система уведомлений
- ✅ Многопользовательский чат
- ✅ Отслеживание изменений ДСЕ

## 🚀 Быстрый старт

```bash
# Установка
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/scripts/setup/setup.sh | bash

# Настройка
nano config/ven_bot.json

# Запуск
bash scripts/start/start_bot.sh
```

## 📚 Документация

- **Установка**: [docs/installation/](docs/installation/)
- **Настройка**: [docs/configuration/](docs/configuration/)
- **Решение проблем**: [docs/troubleshooting/](docs/troubleshooting/)
- **Руководства**: [docs/guides/](docs/guides/)
- **Справка**: [docs/reference/CHEATSHEET.md](docs/reference/CHEATSHEET.md)

## 📁 Структура проекта

```
TelegrammBolt/
├── src/          # Исходный код
├── config/       # Конфигурация
├── data/         # Данные
├── scripts/      # Скрипты
├── services/     # Системные службы
├── docs/         # Документация
└── tests/        # Тесты
```

Подробнее: [docs/reference/PROJECT_STRUCTURE.md](docs/reference/PROJECT_STRUCTURE.md)

## 🤝 Вклад

Pull requests приветствуются!

## 📄 Лицензия

MIT

## 🔗 Ссылки

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [python-telegram-bot](https://docs.python-telegram-bot.org/)

---

**Версия:** 2.0.0
EOF

echo "  ✓ README.md создан"

# .gitignore обновление
cat >> .gitignore << 'EOF'

# Data files
data/*.json
data/*.xlsx
data/*.pdf
data/photos/*
!data/photos/.gitkeep

# Config files
config/ven_bot.json
config/smtp_config.json
!config/*.example

# Virtual environment
.venv/
venv/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Build
dist/
build/
*.egg-info/
EOF

echo "  ✓ .gitignore обновлен"

# .gitkeep для пустых директорий
touch data/photos/.gitkeep
touch tests/.gitkeep

echo "  ✓ .gitkeep файлы созданы"

echo -e "${GREEN}✓${NC} Новые файлы созданы"
echo ""

# Итоговый отчет
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ Реструктуризация завершена!           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Статистика:${NC}"
echo "  - Резервная копия: $BACKUP_DIR"
echo "  - Создано директорий: $(find src config data scripts services docs tests -type d 2>/dev/null | wc -l)"
echo "  - Перемещено файлов: $(find src config data scripts services docs -type f 2>/dev/null | wc -l)"
echo ""
echo -e "${YELLOW}⚠️  Следующие шаги:${NC}"
echo "  1. Обновите импорты в Python файлах"
echo "  2. Обновите пути в скриптах"
echo "  3. Протестируйте бота и веб-интерфейс"
echo "  4. Закоммитьте изменения в Git"
echo ""
echo -e "${BLUE}📚 Документация:${NC}"
echo "  - План реструктуризации: RESTRUCTURE_PLAN.md"
echo "  - Новая структура: docs/reference/PROJECT_STRUCTURE.md"
echo "  - Главный README: README.md"
echo ""
echo -e "${GREEN}Готово! 🎉${NC}"
