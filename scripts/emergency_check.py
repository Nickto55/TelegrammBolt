#!/usr/bin/env python3
"""
Экстренная диагностика сервера - что сломалось?
"""
import json
import os
import sys
from datetime import datetime

print("=" * 70)
print("  🔥 ЭКСТРЕННАЯ ДИАГНОСТИКА - ЧТО СЛОМАЛОСЬ?")
print("=" * 70)
print()

issues_found = []

# 1. Проверка bot_data.json
print("1️⃣  Проверка bot_data.json...")
try:
    with open('bot_data.json', 'r', encoding='utf-8') as f:
        bot_data = json.load(f)
    
    total_records = sum(len(records) for records in bot_data.values())
    print(f"   ✓ Файл читается: {len(bot_data)} пользователей, {total_records} заявок")
    
    # Ищем заявку Hshd
    found_hshd = False
    for user_id, records in bot_data.items():
        for i, record in enumerate(records, 1):
            if (record.get('dse') == 'Hshd' or 
                record.get('id') == 'Hshd' or
                f"{user_id}_{i}" == 'Hshd'):
                found_hshd = True
                print(f"   ✓ Заявка 'Hshd' найдена: user={user_id}, index={i}")
                print(f"     DSE: {record.get('dse')}")
                print(f"     Problem: {record.get('problem_type')}")
                print(f"     DateTime: {record.get('datetime')}")
                break
    
    if not found_hshd:
        issues_found.append("Заявка 'Hshd' НЕ НАЙДЕНА в bot_data.json")
        print("   ❌ Заявка 'Hshd' НЕ НАЙДЕНА!")
        print("   Доступные ID заявок:")
        for user_id, records in bot_data.items():
            for i, record in enumerate(records, 1):
                print(f"     - {user_id}_{i} (DSE: {record.get('dse', 'N/A')})")
                if i >= 3:  # Показываем только первые 3 на пользователя
                    print(f"     ... и еще {len(records) - 3} заявок")
                    break
                    
except FileNotFoundError:
    issues_found.append("bot_data.json НЕ СУЩЕСТВУЕТ")
    print("   ❌ bot_data.json НЕ НАЙДЕН!")
except json.JSONDecodeError as e:
    issues_found.append(f"bot_data.json поврежден: {e}")
    print(f"   ❌ ОШИБКА JSON: {e}")
except Exception as e:
    issues_found.append(f"Ошибка чтения bot_data.json: {e}")
    print(f"   ❌ ОШИБКА: {e}")

print()

# 2. Проверка логов
print("2️⃣  Проверка последних ошибок в логах...")
log_files = ['web.log', 'bot.log']
found_recent_errors = False

for log_file in log_files:
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Ищем последние ошибки
            recent_errors = [line for line in lines[-50:] 
                           if 'ERROR' in line or 'Exception' in line or '500' in line]
            
            if recent_errors:
                found_recent_errors = True
                print(f"   ⚠️  {log_file}: найдено {len(recent_errors)} ошибок")
                print("   Последние 3 ошибки:")
                for err in recent_errors[-3:]:
                    print(f"     {err.strip()}")
                issues_found.append(f"{log_file}: {len(recent_errors)} ошибок")
        except Exception as e:
            print(f"   ⚠️  Не удалось прочитать {log_file}: {e}")

if not found_recent_errors:
    print("   ✓ Критических ошибок в логах не найдено")

print()

# 3. Проверка config.py
print("3️⃣  Проверка config.py...")
try:
    import config.config as config
    
    checks = {
        'BOT_TOKEN': bool(getattr(config, 'BOT_TOKEN', None)),
        'SECRET_KEY': bool(getattr(config, 'SECRET_KEY', None)),
        'PROBLEM_TYPES': bool(getattr(config, 'PROBLEM_TYPES', None)),
    }
    
    for key, value in checks.items():
        status = "✓" if value else "❌"
        print(f"   {status} {key}: {'OK' if value else 'ОТСУТСТВУЕТ'}")
        if not value:
            issues_found.append(f"config.py: отсутствует {key}")
            
except ImportError:
    issues_found.append("config.py не найден или не импортируется")
    print("   ❌ config.py НЕ НАЙДЕН или содержит ошибки!")
except Exception as e:
    issues_found.append(f"Ошибка config.py: {e}")
    print(f"   ❌ ОШИБКА: {e}")

print()

# 4. Проверка процессов
print("4️⃣  Проверка запущенных процессов...")
try:
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    
    web_processes = [line for line in result.stdout.split('\n') 
                     if 'web_app' in line or 'gunicorn' in line and 'grep' not in line]
    
    if web_processes:
        print(f"   ✓ Найдено {len(web_processes)} процессов веб-сервера")
        for proc in web_processes:
            print(f"     {proc}")
    else:
        issues_found.append("Веб-сервер НЕ ЗАПУЩЕН")
        print("   ❌ Веб-сервер НЕ ЗАПУЩЕН!")
except Exception as e:
    print(f"   ⚠️  Не удалось проверить процессы: {e}")

print()

# 5. Проверка зависимостей
print("5️⃣  Проверка Python зависимостей...")
required = ['flask', 'telegram', 'openpyxl', 'reportlab', 'nest_asyncio']
missing = []

for package in required:
    try:
        __import__(package)
        print(f"   ✓ {package}")
    except ImportError:
        missing.append(package)
        print(f"   ❌ {package} НЕ УСТАНОВЛЕН")
        issues_found.append(f"Отсутствует пакет: {package}")

print()

# ИТОГИ
print("=" * 70)
print("  📊 ИТОГИ ДИАГНОСТИКИ")
print("=" * 70)
print()

if not issues_found:
    print("✅ ВСЁ В ПОРЯДКЕ!")
    print("   Система работает нормально, проблема может быть временной.")
    print()
    print("Рекомендации:")
    print("  1. Перезапустите сервер: bash restart_web.sh")
    print("  2. Проверьте логи: tail -f web.log")
else:
    print(f"❌ НАЙДЕНО {len(issues_found)} ПРОБЛЕМ:")
    print()
    for i, issue in enumerate(issues_found, 1):
        print(f"  {i}. {issue}")
    
    print()
    print("🔧 ЧТО ДЕЛАТЬ:")
    print()
    
    if any('Hshd' in issue for issue in issues_found):
        print("  → Заявка 'Hshd' не существует в базе данных")
        print("    Попробуйте открыть другую заявку")
        print("    Доступные ID указаны выше")
        print()
    
    if any('bot_data.json' in issue for issue in issues_found):
        print("  → Проблема с файлом данных")
        print("    Проверьте целостность: python3 diagnose_dse.py")
        print()
    
    if any('НЕ ЗАПУЩЕН' in issue for issue in issues_found):
        print("  → Веб-сервер не работает")
        print("    Запустите: bash restart_web.sh")
        print()
    
    if missing:
        print("  → Отсутствуют зависимости")
        print("    Установите: pip3 install -r requirements.txt")
        print()
    
    if any('ERROR' in issue or 'Exception' in issue for issue in issues_found):
        print("  → Есть ошибки в логах")
        print("    Просмотрите: tail -100 web.log | grep ERROR")
        print()

print("=" * 70)
print()
