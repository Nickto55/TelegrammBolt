#!/usr/bin/env python3
"""
Скрипт для автоматического обновления импортов после реструктуризации
Запускать из корня проекта после выполнения restructure.sh
"""

import os
import re
from pathlib import Path

# Маппинг старых путей на новые
IMPORT_MAPPING = {
    # Bot managers
    'from user_manager import': 'from src.bot.managers.user_manager import',
    'import user_manager': 'import src.bot.managers.user_manager as user_manager',
    'from chat_manager import': 'from src.bot.managers.chat_manager import',
    'import chat_manager': 'import src.bot.managers.chat_manager as chat_manager',
    'from dse_manager import': 'from src.bot.managers.dse_manager import',
    'import dse_manager': 'import src.bot.managers.dse_manager as dse_manager',
    'from gui_manager import': 'from src.bot.managers.gui_manager import',
    'import gui_manager': 'import src.bot.managers.gui_manager as gui_manager',
    
    # Bot handlers
    'from commands import': 'from src.bot.handlers.commands import',
    'import commands': 'import src.bot.handlers.commands as commands',
    'from commands_handlers import': 'from src.bot.handlers.commands_handlers import',
    'import commands_handlers': 'import src.bot.handlers.commands_handlers as commands_handlers',
    
    # Bot workers
    'from dse_watcher import': 'from src.bot.workers.dse_watcher import',
    'import dse_watcher': 'import src.bot.workers.dse_watcher as dse_watcher',
    
    # Bot utils
    'from config import': 'from src.bot.utils.config import',
    'import config': 'import src.bot.utils.config as config',
    'from pdf_generator import': 'from src.bot.utils.pdf_generator import',
    'import pdf_generator': 'import src.bot.utils.pdf_generator as pdf_generator',
    'from genereteTabl import': 'from src.bot.utils.excel_generator import',
    'import genereteTabl': 'import src.bot.utils.excel_generator as genereteTabl',
}

# Маппинг путей к файлам
FILE_PATH_MAPPING = {
    'bot_data.json': 'data/bot_data.json',
    'users_data.json': 'data/users_data.json',
    'RezultBot.xlsx': 'data/RezultBot.xlsx',
    'photos/': 'data/photos/',
    'ven_bot.json': 'config/ven_bot.json',
    'smtp_config.json': 'config/smtp_config.json',
}


def update_imports_in_file(file_path):
    """Обновить импорты в Python файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Обновить импорты
        for old_import, new_import in IMPORT_MAPPING.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes.append(f"  - {old_import} → {new_import}")
        
        # Обновить пути к файлам
        for old_path, new_path in FILE_PATH_MAPPING.items():
            # Различные варианты кавычек
            for quote in ['"', "'"]:
                old_pattern = f'{quote}{old_path}'
                new_pattern = f'{quote}{new_path}'
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    changes.append(f"  - {old_path} → {new_path}")
        
        # Сохранить только если были изменения
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ {file_path}")
            for change in changes:
                print(change)
            return True
        
        return False
    
    except Exception as e:
        print(f"✗ Ошибка в {file_path}: {e}")
        return False


def update_shell_scripts():
    """Обновить пути в shell скриптах"""
    script_updates = {
        'scripts/start/start_bot.sh': [
            ('python bot.py', 'python src/bot/main.py'),
            ('python3 bot.py', 'python3 src/bot/main.py'),
        ],
        'scripts/start/start_bot.bat': [
            ('python bot.py', 'python src\\bot\\main.py'),
        ],
        'scripts/setup/setup.sh': [
            ('cp ven_bot.json.example ven_bot.json', 'cp config/ven_bot.json.example config/ven_bot.json'),
            ('cp smtp_config.json.example smtp_config.json', 'cp config/smtp_config.json.example config/smtp_config.json'),
        ],
    }
    
    for script_path, replacements in script_updates.items():
        if os.path.exists(script_path):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for old, new in replacements:
                    content = content.replace(old, new)
                
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✓ {script_path}")
            except Exception as e:
                print(f"✗ Ошибка в {script_path}: {e}")


def main():
    print("🔄 Обновление импортов и путей...")
    print()
    
    # Найти все Python файлы
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Пропустить .venv, __pycache__, .git
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git', '.idea']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    
    print(f"📝 Найдено {len(python_files)} Python файлов")
    print()
    
    # Обновить Python файлы
    print("🐍 Обновление Python файлов:")
    updated_count = 0
    for file_path in python_files:
        if update_imports_in_file(file_path):
            updated_count += 1
    
    print()
    print(f"✓ Обновлено {updated_count} файлов")
    print()
    
    # Обновить shell скрипты
    print("📜 Обновление shell скриптов:")
    update_shell_scripts()
    print()
    
    print("✅ Готово!")
    print()
    print("⚠️  Рекомендуется:")
    print("  1. Проверить изменения: git diff")
    print("  2. Протестировать бота: python src/bot/main.py")
    print("  3. Протестировать веб: python src/web/app.py")


if __name__ == '__main__':
    main()
