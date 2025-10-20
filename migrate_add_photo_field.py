#!/usr/bin/env python3
"""
Миграция: добавление поля photo_file_id ко всем существующим записям в bot_data.json
"""

import json
import shutil
from datetime import datetime

DATA_FILE = 'bot_data.json'
BACKUP_FILE = f'bot_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

def migrate_add_photo_field():
    """Добавляет поле photo_file_id ко всем записям"""
    
    print(f"📋 Загрузка данных из {DATA_FILE}...")
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл {DATA_FILE} не найден!")
        return
    except json.JSONDecodeError:
        print(f"❌ Ошибка чтения JSON из {DATA_FILE}!")
        return
    
    # Создаем резервную копию
    print(f"💾 Создание резервной копии в {BACKUP_FILE}...")
    shutil.copy(DATA_FILE, BACKUP_FILE)
    
    # Подсчет записей
    total_records = 0
    updated_records = 0
    
    # Обходим всех пользователей
    for user_id, records in data.items():
        if not isinstance(records, list):
            continue
            
        for record in records:
            total_records += 1
            
            # Добавляем поле photo_file_id если его нет
            if 'photo_file_id' not in record:
                record['photo_file_id'] = None
                updated_records += 1
    
    print(f"\n📊 Статистика:")
    print(f"   Всего записей: {total_records}")
    print(f"   Обновлено: {updated_records}")
    print(f"   Уже имели поле: {total_records - updated_records}")
    
    if updated_records > 0:
        # Сохраняем обновленные данные
        print(f"\n💾 Сохранение обновленных данных...")
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Миграция успешно завершена!")
        print(f"📁 Резервная копия сохранена в: {BACKUP_FILE}")
    else:
        print(f"\n✅ Все записи уже имеют поле photo_file_id. Миграция не требуется.")

if __name__ == '__main__':
    migrate_add_photo_field()
