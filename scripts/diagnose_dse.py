#!/usr/bin/env python3
"""
Диагностика проблем с заявками
Проверяет структуру данных и наличие всех необходимых полей
"""

import json
import os
import sys

DATA_FILE = 'bot_data.json'

def diagnose():
    print("="*80)
    print("🔍 ДИАГНОСТИКА ЗАЯВОК")
    print("="*80)
    print()
    
    # Проверка существования файла
    if not os.path.exists(DATA_FILE):
        print(f"❌ Файл {DATA_FILE} не найден!")
        return
    
    print(f"✅ Файл {DATA_FILE} найден")
    
    # Загрузка данных
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Данные успешно загружены")
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        return
    
    print()
    print("📊 СТАТИСТИКА:")
    print(f"   Пользователей: {len(data)}")
    
    total_records = 0
    records_with_photo = 0
    records_without_id = 0
    problematic_records = []
    
    # Анализ каждого пользователя
    for user_id, records in data.items():
        if not isinstance(records, list):
            print(f"⚠️  Пользователь {user_id}: данные не являются списком!")
            continue
        
        print(f"\n👤 Пользователь {user_id}:")
        print(f"   Заявок: {len(records)}")
        
        for idx, record in enumerate(records):
            total_records += 1
            
            # Проверка обязательных полей
            required_fields = ['dse', 'problem_type', 'datetime']
            missing_fields = [f for f in required_fields if f not in record]
            
            if missing_fields:
                problematic_records.append({
                    'user_id': user_id,
                    'index': idx,
                    'dse': record.get('dse', 'N/A'),
                    'missing': missing_fields
                })
                print(f"   ⚠️  Заявка #{idx}: отсутствуют поля {missing_fields}")
            
            # Проверка ID
            if 'id' not in record:
                records_without_id += 1
            
            # Проверка фото
            if record.get('photo_file_id'):
                records_with_photo += 1
                print(f"   📷 Заявка #{idx} ({record.get('dse', 'N/A')}): есть фото")
    
    print()
    print("="*80)
    print("📈 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Всего заявок: {total_records}")
    print(f"   С фото: {records_with_photo}")
    print(f"   Без ID: {records_without_id}")
    print(f"   Проблемных: {len(problematic_records)}")
    print()
    
    if records_without_id > 0:
        print(f"⚠️  {records_without_id} заявок без поля 'id'")
        print("   Это нормально - ID генерируются автоматически при загрузке")
        print()
    
    if problematic_records:
        print("❌ ПРОБЛЕМНЫЕ ЗАЯВКИ:")
        for rec in problematic_records[:5]:  # Показываем первые 5
            print(f"   • Пользователь {rec['user_id']}, индекс {rec['index']}")
            print(f"     ДСЕ: {rec['dse']}")
            print(f"     Отсутствуют поля: {', '.join(rec['missing'])}")
        
        if len(problematic_records) > 5:
            print(f"   ... и еще {len(problematic_records) - 5} заявок")
    else:
        print("✅ Все заявки имеют обязательные поля!")
    
    print()
    print("="*80)
    print("💡 РЕКОМЕНДАЦИИ:")
    print()
    
    if records_with_photo > 0:
        print(f"✅ Найдено {records_with_photo} заявок с фото")
        print("   Убедитесь что:")
        print("   • BOT_TOKEN правильный в config.py")
        print("   • Папка photos/temp/ существует и доступна для записи")
        print("   • Установлен nest-asyncio: pip install nest-asyncio")
        print()
    
    if problematic_records:
        print("⚠️  Исправьте проблемные заявки в bot_data.json")
        print("   Добавьте отсутствующие обязательные поля")
        print()
    
    print("🔧 Для тестирования веб-интерфейса:")
    print("   1. Запустите: python run_web_dev.py")
    print("   2. Откройте: http://127.0.0.1:5000")
    print("   3. Проверьте логи в консоли при открытии заявки")
    print()
    print("="*80)

if __name__ == '__main__':
    diagnose()
