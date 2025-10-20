#!/usr/bin/env python3
"""Быстрая проверка и исправление проблем на сервере"""
import json
import os
import sys
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_bot_data():
    """Проверка bot_data.json"""
    print("\n" + "="*50)
    print("ПРОВЕРКА bot_data.json")
    print("="*50)
    
    if not os.path.exists('bot_data.json'):
        print("❌ ОШИБКА: bot_data.json не найден!")
        return False
    
    try:
        with open('bot_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_records = sum(len(records) for records in data.values())
        total_users = len(data.keys())
        
        print(f"✓ Файл прочитан успешно")
        print(f"  Пользователей: {total_users}")
        print(f"  Всего заявок: {total_records}")
        
        # Проверка записей
        problems = []
        records_with_photos = 0
        
        for user_id, records in data.items():
            for i, record in enumerate(records, 1):
                record_id = f"{user_id}_{i}"
                
                # Проверка обязательных полей
                if not record.get('dse'):
                    problems.append(f"{record_id}: отсутствует 'dse'")
                if not record.get('problem_type'):
                    problems.append(f"{record_id}: отсутствует 'problem_type'")
                if not record.get('datetime'):
                    problems.append(f"{record_id}: отсутствует 'datetime'")
                
                # Подсчет фото
                if record.get('photo_file_id') or record.get('photos'):
                    records_with_photos += 1
        
        print(f"  Заявок с фото: {records_with_photos}")
        
        if problems:
            print(f"\n⚠️  НАЙДЕНО {len(problems)} ПРОБЛЕМ:")
            for p in problems[:10]:
                print(f"   - {p}")
            if len(problems) > 10:
                print(f"   ... и еще {len(problems) - 10} проблем")
            return False
        else:
            print("\n✓ Все записи корректны")
            return True
            
    except json.JSONDecodeError as e:
        print(f"❌ ОШИБКА JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

def check_logs():
    """Проверка логов на ошибки"""
    print("\n" + "="*50)
    print("ПРОВЕРКА ЛОГОВ")
    print("="*50)
    
    log_files = ['web.log', 'bot.log', 'error.log']
    found_errors = False
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Ищем последние ошибки
                errors = [line for line in lines[-100:] if 'ERROR' in line or 'Exception' in line or 'Traceback' in line]
                
                if errors:
                    print(f"\n📋 {log_file}: найдено {len(errors)} ошибок")
                    print("   Последние ошибки:")
                    for error in errors[-5:]:
                        print(f"   {error.strip()}")
                    found_errors = True
                else:
                    print(f"✓ {log_file}: ошибок не найдено")
                    
            except Exception as e:
                print(f"⚠️  Не удалось прочитать {log_file}: {e}")
        else:
            print(f"  {log_file}: не существует")
    
    return not found_errors

def check_config():
    """Проверка конфигурации"""
    print("\n" + "="*50)
    print("ПРОВЕРКА КОНФИГУРАЦИИ")
    print("="*50)
    
    try:
        import config
        
        # Проверка основных параметров
        checks = {
            'BOT_TOKEN': hasattr(config, 'BOT_TOKEN') and config.BOT_TOKEN,
            'SECRET_KEY': hasattr(config, 'SECRET_KEY') and config.SECRET_KEY,
            'PROBLEM_TYPES': hasattr(config, 'PROBLEM_TYPES') and config.PROBLEM_TYPES,
        }
        
        all_ok = True
        for key, value in checks.items():
            status = "✓" if value else "❌"
            print(f"{status} {key}: {'OK' if value else 'ОТСУТСТВУЕТ'}")
            if not value:
                all_ok = False
        
        return all_ok
        
    except ImportError:
        print("❌ ОШИБКА: Не удалось импортировать config.py")
        return False
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

def check_dependencies():
    """Проверка зависимостей"""
    print("\n" + "="*50)
    print("ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    print("="*50)
    
    required = [
        'flask',
        'telegram',
        'openpyxl',
        'reportlab',
        'nest_asyncio'
    ]
    
    all_ok = True
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}: установлен")
        except ImportError:
            print(f"❌ {package}: НЕ УСТАНОВЛЕН")
            all_ok = False
    
    return all_ok

def main():
    """Основная функция"""
    print("\n" + "="*70)
    print("  ДИАГНОСТИКА СЕРВЕРА BOLT")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)
    
    results = {
        'bot_data': check_bot_data(),
        'config': check_config(),
        'dependencies': check_dependencies(),
        'logs': check_logs(),
    }
    
    print("\n" + "="*70)
    print("ИТОГИ")
    print("="*70)
    
    all_ok = all(results.values())
    
    for check, result in results.items():
        status = "✓" if result else "❌"
        print(f"{status} {check.upper()}: {'OK' if result else 'ПРОБЛЕМЫ'}")
    
    if all_ok:
        print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("\nРекомендации:")
        print("  1. Перезапустите веб-сервер:")
        print("     sudo systemctl restart boltweb")
        print("  2. Проверьте логи:")
        print("     tail -f web.log")
    else:
        print("\n⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print("\nЧто делать:")
        if not results['dependencies']:
            print("  1. Установите зависимости:")
            print("     pip install -r requirements.txt")
        if not results['bot_data']:
            print("  2. Проверьте bot_data.json на корректность")
        if not results['config']:
            print("  3. Проверьте config.py")
        print("  4. Перезапустите сервер после исправлений")
    
    print("="*70 + "\n")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
