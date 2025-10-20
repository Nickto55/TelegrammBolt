#!/usr/bin/env python3
"""
🚀 УНИВЕРСАЛЬНЫЙ УСТАНОВЩИК TelegrammBolt
Автоматическая установка и настройка бота + веб-интерфейса
"""
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(msg):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{msg:^70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def check_python_version():
    """Проверка версии Python"""
    print_header("Проверка Python")
    
    version = sys.version_info
    print_info(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error("Требуется Python 3.8 или выше!")
        return False
    
    print_success("Версия Python подходит")
    return True

def install_dependencies():
    """Установка зависимостей"""
    print_header("Установка зависимостей")
    
    if not os.path.exists('requirements.txt'):
        print_error("Файл requirements.txt не найден!")
        return False
    
    try:
        print_info("Установка пакетов из requirements.txt...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '--quiet'])
        print_success("Все зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Ошибка установки зависимостей: {e}")
        return False

def create_directories():
    """Создание необходимых директорий"""
    print_header("Создание директорий")
    
    directories = [
        'data',
        'photos/temp',
        'config',
        'logs'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print_success(f"Создана: {directory}/")
        except Exception as e:
            print_error(f"Ошибка создания {directory}: {e}")
            return False
    
    return True

def create_config_files():
    """Создание конфигурационных файлов"""
    print_header("Настройка конфигурации")
    
    # 1. ven_bot.json
    ven_bot_path = 'config/ven_bot.json'
    if not os.path.exists(ven_bot_path):
        print_info("Создаём config/ven_bot.json...")
        
        bot_token = input(f"\n{Colors.YELLOW}Введите BOT_TOKEN (от @BotFather):{Colors.END} ").strip()
        
        if not bot_token:
            print_warning("Токен не введён, создаём файл с заглушкой")
            bot_token = "YOUR_BOT_TOKEN_HERE"
        
        admin_id = input(f"{Colors.YELLOW}Введите ваш Telegram ID (admin):{Colors.END} ").strip()
        
        if not admin_id or not admin_id.isdigit():
            print_warning("ID не введён, используем заглушку")
            admin_id = "123456789"
        
        config_data = {
            "BOT_TOKEN": bot_token,
            "BOT_USERNAME": "@your_bot",
            "ADMIN_IDS": [int(admin_id)]
        }
        
        try:
            with open(ven_bot_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print_success(f"Создан: {ven_bot_path}")
        except Exception as e:
            print_error(f"Ошибка создания {ven_bot_path}: {e}")
            return False
    else:
        print_info(f"{ven_bot_path} уже существует")
    
    # 2. smtp_config.json (опционально)
    smtp_path = 'config/smtp_config.json'
    if not os.path.exists(smtp_path):
        print_info("\nНастройка email (можно пропустить - нажмите Enter)")
        
        smtp_server = input(f"{Colors.YELLOW}SMTP сервер (например smtp.gmail.com):{Colors.END} ").strip()
        
        if smtp_server:
            smtp_port = input(f"{Colors.YELLOW}SMTP порт (обычно 587):{Colors.END} ").strip() or "587"
            smtp_user = input(f"{Colors.YELLOW}Email адрес:{Colors.END} ").strip()
            smtp_pass = input(f"{Colors.YELLOW}Пароль:{Colors.END} ").strip()
            
            smtp_data = {
                "SMTP_SERVER": smtp_server,
                "SMTP_PORT": int(smtp_port),
                "SMTP_USER": smtp_user,
                "SMTP_PASSWORD": smtp_pass
            }
            
            try:
                with open(smtp_path, 'w', encoding='utf-8') as f:
                    json.dump(smtp_data, f, indent=2)
                print_success(f"Создан: {smtp_path}")
            except Exception as e:
                print_error(f"Ошибка создания {smtp_path}: {e}")
        else:
            print_warning("Email не настроен (можно настроить позже)")
    else:
        print_info(f"{smtp_path} уже существует")
    
    return True

def create_data_files():
    """Создание файлов данных"""
    print_header("Создание файлов данных")
    
    data_files = {
        'data/bot_data.json': {},
        'data/users_data.json': {},
        'data/chat_data.json': {},
        'data/watched_dse.json': {}
    }
    
    for file_path, default_data in data_files.items():
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2)
                print_success(f"Создан: {file_path}")
            except Exception as e:
                print_error(f"Ошибка создания {file_path}: {e}")
                return False
        else:
            print_info(f"{file_path} уже существует")
    
    return True

def create_startup_scripts():
    """Создание скриптов запуска"""
    print_header("Создание скриптов запуска")
    
    # Скрипт запуска бота (Linux/Mac)
    start_bot_sh = """#!/bin/bash
# Запуск Telegram бота TelegrammBolt

# Переход в папку бота
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Активация виртуального окружения если есть
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запуск бота
echo "🤖 Запуск Telegram бота..."
cd bot
python3 bot.py
"""
    
    # Скрипт запуска веба (Linux/Mac)
    start_web_sh = """#!/bin/bash
# Запуск веб-интерфейса TelegrammBolt

# Переход в папку проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Активация виртуального окружения если есть
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запуск веб-приложения
echo "🌐 Запуск веб-интерфейса..."
cd web
python3 web_app.py
"""
    
    # Скрипт запуска бота (Windows)
    start_bot_bat = """@echo off
REM Запуск Telegram бота

cd /d "%~dp0bot"
python bot.py
pause
"""
    
    # Скрипт запуска веба (Windows)
    start_web_bat = """@echo off
REM Запуск веб-интерфейса

cd /d "%~dp0web"
python web_app.py
pause
"""
    
    scripts = {
        'start_bot.sh': start_bot_sh,
        'start_web.sh': start_web_sh,
        'start_bot.bat': start_bot_bat,
        'start_web.bat': start_web_bat,
    }
    
    for filename, content in scripts.items():
        try:
            with open(filename, 'w', encoding='utf-8', newline='\n' if filename.endswith('.sh') else None) as f:
                f.write(content)
            
            # Делаем исполняемым для .sh файлов
            if filename.endswith('.sh') and os.name != 'nt':
                os.chmod(filename, 0o755)
            
            print_success(f"Создан: {filename}")
        except Exception as e:
            print_error(f"Ошибка создания {filename}: {e}")
    
    return True

def test_installation():
    """Тестирование установки"""
    print_header("Тестирование установки")
    
    # Проверка импортов
    required_modules = [
        'telegram',
        'flask',
        'openpyxl',
        'reportlab',
        'nest_asyncio'
    ]
    
    all_ok = True
    for module in required_modules:
        try:
            __import__(module)
            print_success(f"Модуль {module} импортируется")
        except ImportError:
            print_error(f"Модуль {module} не установлен!")
            all_ok = False
    
    # Проверка конфигурации
    if os.path.exists('config/ven_bot.json'):
        try:
            with open('config/ven_bot.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if config.get('BOT_TOKEN') == 'YOUR_BOT_TOKEN_HERE':
                print_warning("BOT_TOKEN не настроен! Отредактируйте config/ven_bot.json")
            else:
                print_success("Конфигурация бота OK")
        except Exception as e:
            print_error(f"Ошибка чтения конфигурации: {e}")
            all_ok = False
    
    return all_ok

def print_final_instructions():
    """Финальные инструкции"""
    print_header("✅ Установка завершена!")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}Что дальше:{Colors.END}\n")
    
    print("1️⃣  Настройте конфигурацию:")
    print(f"   {Colors.YELLOW}nano config/ven_bot.json{Colors.END}")
    print("   Добавьте ваш BOT_TOKEN от @BotFather\n")
    
    print("2️⃣  Запустите бота:")
    if os.name == 'nt':
        print(f"   {Colors.YELLOW}start_bot.bat{Colors.END}")
        print("   или")
        print(f"   {Colors.YELLOW}cd bot && python bot.py{Colors.END}\n")
    else:
        print(f"   {Colors.YELLOW}./start_bot.sh{Colors.END}")
        print("   или")
        print(f"   {Colors.YELLOW}cd bot && python3 bot.py{Colors.END}\n")
    
    print("3️⃣  Запустите веб-интерфейс:")
    if os.name == 'nt':
        print(f"   {Colors.YELLOW}start_web.bat{Colors.END}")
        print("   или")
        print(f"   {Colors.YELLOW}cd web && python web_app.py{Colors.END}\n")
    else:
        print(f"   {Colors.YELLOW}./start_web.sh{Colors.END}")
        print("   или")
        print(f"   {Colors.YELLOW}cd web && python3 web_app.py{Colors.END}\n")
    
    print("4️⃣  Откройте в браузере:")
    print(f"   {Colors.BLUE}http://localhost:5000{Colors.END}\n")
    
    print(f"\n{Colors.BLUE}📚 Документация:{Colors.END}")
    print("   README.md - Общее описание")
    print("   docs/INSTALLATION.md - Установка")
    print("   docs/TROUBLESHOOTING.md - Решение проблем\n")
    
    print(f"{Colors.GREEN}✨ Готово! Удачной работы! ✨{Colors.END}\n")

def main():
    """Основная функция установщика"""
    
    print("\n" + "="*70)
    print(f"{Colors.BOLD}{'TelegrammBolt - Установщик':^70}{Colors.END}")
    print("="*70 + "\n")
    
    # Проверка что запущено из корня проекта
    if not os.path.exists('bot') or not os.path.exists('web'):
        print_error("Ошибка: Запустите установщик из корня проекта!")
        print_info("Должны существовать папки: bot/ и web/")
        return 1
    
    steps = [
        ("Проверка Python", check_python_version),
        ("Установка зависимостей", install_dependencies),
        ("Создание директорий", create_directories),
        ("Настройка конфигурации", create_config_files),
        ("Создание файлов данных", create_data_files),
        ("Создание скриптов запуска", create_startup_scripts),
        ("Тестирование", test_installation),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print_error(f"\n❌ Установка прервана на этапе: {step_name}")
            return 1
    
    print_final_instructions()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Установка прервана пользователем{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Критическая ошибка: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
