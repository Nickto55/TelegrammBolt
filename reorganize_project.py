#!/usr/bin/env python3
"""
🧹 АВТОМАТИЧЕСКАЯ РЕОРГАНИЗАЦИЯ ПРОЕКТА
Наводим порядок: разделяем бот и веб, удаляем мусор
"""
import os
import shutil
import json
from datetime import datetime

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(msg):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

# Создать бэкап
def create_backup():
    print_step("📦 Создание резервной копии")
    
    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(backup_name):
        print_warning(f"Бэкап {backup_name} уже существует, пропускаем...")
        return backup_name
    
    try:
        # Создаем архив важных файлов
        important_files = [
            'bot_data.json', 'users_data.json', 'chat_data.json',
            'ven_bot.json', 'config.py', 'smtp_config.json'
        ]
        
        os.makedirs(backup_name)
        
        for file in important_files:
            if os.path.exists(file):
                shutil.copy2(file, backup_name)
                print_success(f"Сохранён: {file}")
        
        print_success(f"Бэкап создан: {backup_name}/")
        return backup_name
    
    except Exception as e:
        print_error(f"Ошибка создания бэкапа: {e}")
        return None

# Создать структуру папок
def create_structure():
    print_step("📁 Создание новой структуры папок")
    
    folders = [
        'bot',
        'web',
        'web/static',
        'web/static/css',
        'web/static/js',
        'web/templates',
        'config',
        'data',
        'photos/temp',
        'scripts',
        'docs',
        'archive'  # Для старых файлов
    ]
    
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print_success(f"Создана: {folder}/")
        except Exception as e:
            print_error(f"Не удалось создать {folder}: {e}")

# Переместить файлы бота
def move_bot_files():
    print_step("🤖 Перемещение файлов бота")
    
    bot_files = {
        'bot.py': 'bot/bot.py',
        'commands.py': 'bot/commands.py',
        'commands_handlers.py': 'bot/commands_handlers.py',
        'chat_manager.py': 'bot/chat_manager.py',
        'dse_manager.py': 'bot/dse_manager.py',
        'dse_watcher.py': 'bot/dse_watcher.py',
        'user_manager.py': 'bot/user_manager.py',
        'email_manager.py': 'bot/email_manager.py',
        'gui_manager.py': 'bot/gui_manager.py',
        'pdf_generator.py': 'bot/pdf_generator.py',
    }
    
    for src, dst in bot_files.items():
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print_success(f"{src} → {dst}")
            except Exception as e:
                print_error(f"Ошибка перемещения {src}: {e}")
        else:
            print_warning(f"Файл не найден: {src}")

# Переместить файлы веба
def move_web_files():
    print_step("🌐 Перемещение файлов веб-интерфейса")
    
    # Главный файл
    if os.path.exists('web_app.py'):
        shutil.move('web_app.py', 'web/web_app.py')
        print_success("web_app.py → web/web_app.py")
    
    # Static файлы
    if os.path.exists('static'):
        if os.path.exists('web/static'):
            shutil.rmtree('web/static')
        shutil.move('static', 'web/static')
        print_success("static/ → web/static/")
    
    # Templates
    if os.path.exists('templates'):
        if os.path.exists('web/templates'):
            shutil.rmtree('web/templates')
        shutil.move('templates', 'web/templates')
        print_success("templates/ → web/templates/")

# Переместить конфигурацию
def move_config_files():
    print_step("⚙️ Перемещение конфигурации")
    
    config_files = {
        'config.py': 'config/config.py',
        'ven_bot.json': 'config/ven_bot.json',
        'ven_bot.json.example': 'config/ven_bot.json.example',
        'smtp_config.json': 'config/smtp_config.json',
        'smtp_config.json.example': 'config/smtp_config.json.example',
    }
    
    for src, dst in config_files.items():
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print_success(f"{src} → {dst}")
            except Exception as e:
                print_error(f"Ошибка перемещения {src}: {e}")

# Переместить данные
def move_data_files():
    print_step("💾 Перемещение файлов данных")
    
    data_files = {
        'bot_data.json': 'data/bot_data.json',
        'users_data.json': 'data/users_data.json',
        'chat_data.json': 'data/chat_data.json',
        'watched_dse.json': 'data/watched_dse.json',
    }
    
    for src, dst in data_files.items():
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print_success(f"{src} → {dst}")
            except Exception as e:
                print_error(f"Ошибка перемещения {src}: {e}")

# Переместить полезные скрипты
def move_scripts():
    print_step("🛠️ Перемещение полезных скриптов")
    
    scripts = [
        'server_check.py',
        'check_dse_id.py',
        'diagnose_dse.py',
        'emergency_check.py',
        'clear_logs.py',
        'restart_web.sh',
        'start_bot.sh',
        'install.sh',
        'setup.sh',
        'show_users_roles.py',
    ]
    
    for script in scripts:
        if os.path.exists(script):
            try:
                dst = f'scripts/{script}'
                shutil.move(script, dst)
                print_success(f"{script} → scripts/")
            except Exception as e:
                print_error(f"Ошибка перемещения {script}: {e}")

# Переместить документацию
def move_docs():
    print_step("📚 Перемещение документации")
    
    docs = [
        'README.md',
        'INSTALLATION.md',
        'TROUBLESHOOTING.md',
        'QUICK_FIX.md',
    ]
    
    for doc in docs:
        if os.path.exists(doc):
            try:
                # README остаётся в корне
                if doc == 'README.md':
                    continue
                dst = f'docs/{doc}'
                shutil.move(doc, dst)
                print_success(f"{doc} → docs/")
            except Exception as e:
                print_error(f"Ошибка перемещения {doc}: {e}")

# Архивировать старые файлы
def archive_old_files():
    print_step("🗑️ Архивирование устаревших файлов")
    
    old_files = [
        # Дубликаты
        'add-pdf-menu-function.sh',
        'apply-fixes.ps1', 'apply-fixes.sh',
        'cleanup-bot.sh', 'cleanup-docs.ps1', 'cleanup-docs.sh',
        'deploy_fixes.ps1',
        'fix-502.sh', 'fix_server.sh',
        'quick_fix.sh',
        'diagnose-web.sh',
        'restructure.sh',
        'reorganize.ps1',
        'update_imports.py',
        'migrate_add_photo_field.py',
        
        # Старая документация
        'CHEATSHEET.md',
        'DOCKER_TROUBLESHOOTING.md',
        'FIXES_APPLIED.md',
        'FIX_502.md', 'FIX_HTTPS.md', 'FIX_MONITOR_BLACK_SCREEN.md',
        'HTTPS_QUICK_SETUP.txt', 'HTTPS_SETUP.md',
        'MONITOR.md', 'MONITOR_README.md', 'MONITOR_QUICKSTART.md',
        'MONITOR_TESTING.md', 'MONITOR_HTOP_GUIDE.md',
        'QUICKSTART_REORGANIZATION.md',
        'REORGANIZATION_GUIDE.md',
        'ROLE_MANAGEMENT_GUIDE.md',
        'test_role_management.md',
        'HELP_EMERGENCY.txt',
        
        # Тесты
        'test_report.pdf',
        'test_monitor_data.py',
        'RezultBot.xlsx',
        'genereteTabl.py',
        
        # Monitor файлы
        'monitor.py',
        'monitor_cheatsheet.sh',
        'monitor_integration.py',
        'start_monitor.sh',
        
        # Nginx
        'nginx-ssl.conf',
        'nginx.conf',
        'setup-https.sh',
        'setup-ssl-quick.sh',
        
        # Systemd
        'telegrambot.service',
        
        # Остальные скрипты
        'check_installation.sh',
        'restart-bot.sh',
        'setup_minimal.sh',
        'show-web-url.sh',
        
        # Windows
        'windows_service.py',
        'installer.nsi',
        'start_bot.bat',
        'run_web_dev.ps1',
    ]
    
    archived = 0
    for file in old_files:
        if os.path.exists(file):
            try:
                dst = f'archive/{file}'
                shutil.move(file, dst)
                print_success(f"{file} → archive/")
                archived += 1
            except Exception as e:
                print_error(f"Ошибка архивирования {file}: {e}")
    
    print(f"\n📦 Архивировано файлов: {archived}")

# Создать новый README
def create_new_readme():
    print_step("📝 Создание нового README.md")
    
    readme_content = """# TelegrammBolt - Telegram Bot + Web Interface

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
"""
    
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print_success("README.md создан")
    except Exception as e:
        print_error(f"Ошибка создания README: {e}")

# Основная функция
def main():
    print("\n" + "="*70)
    print("🧹 АВТОМАТИЧЕСКАЯ РЕОРГАНИЗАЦИЯ ПРОЕКТА")
    print("="*70)
    
    # Проверка
    if not os.path.exists('bot.py'):
        print_error("Ошибка: bot.py не найден! Запустите скрипт из корня проекта.")
        return
    
    print("\n⚠️  ВНИМАНИЕ!")
    print("Этот скрипт:")
    print("  1. Создаст резервную копию важных файлов")
    print("  2. Создаст новую структуру папок")
    print("  3. Переместит файлы по категориям")
    print("  4. Архивирует устаревшие файлы")
    print("")
    
    response = input("Продолжить? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Отменено.")
        return
    
    # Выполнение
    try:
        create_backup()
        create_structure()
        move_bot_files()
        move_web_files()
        move_config_files()
        move_data_files()
        move_scripts()
        move_docs()
        archive_old_files()
        create_new_readme()
        
        print_step("✅ РЕОРГАНИЗАЦИЯ ЗАВЕРШЕНА!")
        print("\n📋 Следующие шаги:\n")
        print("1. Проверьте новую структуру:")
        print("   ls -la bot/ web/ config/ data/ scripts/")
        print("")
        print("2. Обновите пути импорта (если нужно):")
        print("   python scripts/update_imports.py")
        print("")
        print("3. Протестируйте:")
        print("   cd bot && python bot.py")
        print("   cd web && python web_app.py")
        print("")
        print("4. Старые файлы в archive/ (можно удалить позже)")
        print("")
        print("✨ Проект теперь организован и чист!")
        
    except Exception as e:
        print_error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
