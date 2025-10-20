#!/usr/bin/env python3
"""
🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ИМПОРТОВ
Обновляет импорты во всех файлах после реорганизации
"""
import os
import re
import sys

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(msg):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

# Карта исправлений импортов
IMPORT_FIXES = {
    'bot/': {
        # В bot.py импорты должны быть из config и локальные
        r'from config import': r'from config.config import',
        r'^import config$': r'import config.config as config',
        
        # Локальные импорты в bot/ - используем относительные
        r'from commands import': r'from .commands import',
        r'from dse_watcher import': r'from .dse_watcher import',
        r'from chat_manager import': r'from .chat_manager import',
        r'from user_manager import': r'from .user_manager import',
        r'from dse_manager import': r'from .dse_manager import',
        r'from email_manager import': r'from .email_manager import',
        r'from gui_manager import': r'from .gui_manager import',
        r'from pdf_generator import': r'from .pdf_generator import',
        r'from commands_handlers import': r'from .commands_handlers import',
        
        # Для абсолютных импортов
        r'^import commands$': r'from . import commands',
        r'^import dse_watcher$': r'from . import dse_watcher',
        r'^import chat_manager$': r'from . import chat_manager',
        r'^import user_manager$': r'from . import user_manager',
        r'^import dse_manager$': r'from . import dse_manager',
    },
    'web/': {
        # В web_app.py импорты должны быть из других папок
        r'from config import': r'from config.config import',
        r'import config$': r'import config.config as config',
        
        # Импорты из bot/
        r'from user_manager import': r'from bot.user_manager import',
        r'from dse_manager import': r'from bot.dse_manager import',
        r'from pdf_generator import': r'from bot.pdf_generator import',
        r'from email_manager import': r'from bot.email_manager import',
        
        r'^import user_manager$': r'from bot import user_manager',
        r'^import dse_manager$': r'from bot import dse_manager',
    },
    'scripts/': {
        # В скриптах - абсолютные импорты
        r'from config import': r'from config.config import',
        r'import config$': r'import config.config as config',
        
        r'from user_manager import': r'from bot.user_manager import',
        r'from dse_manager import': r'from bot.dse_manager import',
        
        r'^import user_manager$': r'from bot import user_manager',
        r'^import dse_manager$': r'from bot import dse_manager',
    }
}

def fix_imports_in_file(file_path):
    """Исправляет импорты в одном файле"""
    
    # Определяем в какой папке находится файл
    directory = None
    for dir_name in ['bot/', 'web/', 'scripts/']:
        if dir_name in file_path.replace('\\', '/'):
            directory = dir_name
            break
    
    if not directory or directory not in IMPORT_FIXES:
        return 0, 0  # Файл не в целевой директории
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes = IMPORT_FIXES[directory]
        changes = 0
        
        # Применяем исправления
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            new_line = line
            for pattern, replacement in fixes.items():
                if re.search(pattern, new_line):
                    new_line = re.sub(pattern, replacement, new_line)
                    if new_line != line:
                        changes += 1
            new_lines.append(new_line)
        
        new_content = '\n'.join(new_lines)
        
        # Записываем если были изменения
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return changes, 1
        
        return 0, 0
        
    except Exception as e:
        print_error(f"Ошибка обработки {file_path}: {e}")
        return 0, 0

def add_init_files():
    """Добавляет __init__.py в пакеты"""
    print_header("📦 Создание __init__.py для пакетов")
    
    packages = ['bot', 'config', 'web']
    
    for package in packages:
        init_file = os.path.join(package, '__init__.py')
        if not os.path.exists(init_file):
            try:
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write(f'"""Пакет {package}"""\n')
                print_success(f"Создан: {init_file}")
            except Exception as e:
                print_error(f"Ошибка создания {init_file}: {e}")
        else:
            print_warning(f"Уже существует: {init_file}")

def main():
    print("\n" + "="*70)
    print("🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ИМПОРТОВ")
    print("="*70)
    
    # Проверка что мы в корне проекта
    if not os.path.exists('bot') or not os.path.exists('web'):
        print_error("Ошибка: Запустите скрипт из корня проекта!")
        return 1
    
    # Создаем __init__.py
    add_init_files()
    
    # Сканируем и исправляем файлы
    print_header("🔍 Сканирование и исправление файлов")
    
    total_files = 0
    total_changes = 0
    fixed_files = 0
    
    directories = ['bot', 'web', 'scripts']
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
        
        print(f"\n📁 {directory}/")
        
        for root, dirs, files in os.walk(directory):
            # Пропускаем __pycache__
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(root, file)
                    changes, fixed = fix_imports_in_file(file_path)
                    
                    total_files += 1
                    total_changes += changes
                    fixed_files += fixed
                    
                    rel_path = os.path.relpath(file_path)
                    if changes > 0:
                        print_success(f"  {rel_path}: {changes} изменений")
                    else:
                        print(f"  {rel_path}: OK")
    
    # Итоги
    print_header("📊 ИТОГИ")
    
    print(f"Обработано файлов: {total_files}")
    print(f"Исправлено файлов: {fixed_files}")
    print(f"Всего изменений: {total_changes}")
    
    if total_changes > 0:
        print(f"\n{Colors.GREEN}✅ ИМПОРТЫ ОБНОВЛЕНЫ!{Colors.END}")
        print("\n📝 Следующие шаги:")
        print("  1. Проверьте изменения: git diff")
        print("  2. Протестируйте бота: cd bot && python bot.py")
        print("  3. Протестируйте веб: cd web && python web_app.py")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Изменений не требуется{Colors.END}")
    
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
