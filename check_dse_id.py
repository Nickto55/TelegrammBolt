#!/usr/bin/env python3
"""Проверка существования заявки по ID"""
import json
import sys

def check_dse_id(dse_id):
    """Поиск заявки по ID"""
    try:
        with open('bot_data.json', 'r', encoding='utf-8') as f:
            bot_data = json.load(f)
        
        print(f"\nПоиск заявки с ID: {dse_id}")
        print("-" * 50)
        
        found = False
        for user_id, records in bot_data.items():
            counter = 0
            for record in records:
                counter += 1
                # Генерируем ID так же, как в dse_manager.py
                generated_id = f"{user_id}_{counter}"
                record_dse = record.get('dse', '')
                
                # Проверяем все возможные варианты
                if (str(generated_id) == str(dse_id) or 
                    str(record_dse) == str(dse_id) or
                    str(record.get('id', '')) == str(dse_id)):
                    
                    found = True
                    print(f"✓ Заявка найдена!")
                    print(f"  User ID: {user_id}")
                    print(f"  Generated ID: {generated_id}")
                    print(f"  DSE Number: {record_dse}")
                    print(f"  Problem Type: {record.get('problem_type', 'N/A')}")
                    print(f"  DateTime: {record.get('datetime', 'N/A')}")
                    print(f"  Has Photo: {'photo_file_id' in record or 'photos' in record}")
                    print(f"\nПолная запись:")
                    print(json.dumps(record, ensure_ascii=False, indent=2))
                    return
        
        if not found:
            print(f"✗ Заявка с ID '{dse_id}' НЕ НАЙДЕНА")
            print("\nВсе доступные ID:")
            for user_id, records in bot_data.items():
                counter = 0
                for record in records:
                    counter += 1
                    generated_id = f"{user_id}_{counter}"
                    print(f"  - {generated_id} (DSE: {record.get('dse', 'N/A')})")
    
    except FileNotFoundError:
        print("✗ Файл bot_data.json не найден")
    except json.JSONDecodeError:
        print("✗ Ошибка чтения bot_data.json - некорректный JSON")
    except Exception as e:
        print(f"✗ Ошибка: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_dse_id(sys.argv[1])
    else:
        print("Использование: python check_dse_id.py <ID заявки>")
        print("Пример: python check_dse_id.py Hshd")
