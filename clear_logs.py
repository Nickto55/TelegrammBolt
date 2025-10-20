#!/usr/bin/env python3
"""Очистка логов для свежего старта"""
import os

log_files = [
    'bot.log',
    'web.log',
    'error.log'
]

print("Очистка логов...")
for log_file in log_files:
    if os.path.exists(log_file):
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('')
            print(f"✓ {log_file} очищен")
        except Exception as e:
            print(f"✗ Ошибка очистки {log_file}: {e}")
    else:
        print(f"  {log_file} не существует")

print("\nГотово! Теперь можно запустить сервер для чистого теста.")
