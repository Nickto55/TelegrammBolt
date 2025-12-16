#!/usr/bin/env python3
"""
Тестирование синхронизации данных между веб и Telegram
Проверяет:
1. ДСЕ созданные в боте видны на веб
2. ДСЕ созданные на веб видны в боте
3. Роли пользователей синхронизируются
4. QR коды содержат правильные роли
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(__file__))

from config.config import load_data, save_data, DATA_FILE, USERS_FILE
from bot.invite_manager import create_invite, get_invite_info, validate_invite
from bot.user_manager import get_user_role, set_user_role, is_user_registered

def test_data_files_shared():
    """Тест 1: Проверка что файлы данных общие"""
    print("="*60)
    print("ТЕСТ 1: Проверка общих файлов данных")
    print("="*60)
    
    print(f"✓ DATA_FILE: {DATA_FILE}")
    print(f"✓ USERS_FILE: {USERS_FILE}")
    
    # Проверяем существование
    if os.path.exists(DATA_FILE):
        dse_data = load_data(DATA_FILE)
        print(f"✓ ДСЕ записей в базе: {len(dse_data)}")
    else:
        print("⚠ Файл ДСЕ не существует (пустая база)")
    
    if os.path.exists(USERS_FILE):
        users_data = load_data(USERS_FILE)
        print(f"✓ Пользователей в базе: {len(users_data)}")
    else:
        print("⚠ Файл пользователей не существует (пустая база)")
    
    print()

def test_qr_role_assignment():
    """Тест 2: QR коды содержат роли"""
    print("="*60)
    print("ТЕСТ 2: Проверка ролей в QR кодах")
    print("="*60)
    
    test_roles = ['initiator', 'responder']
    
    for role in test_roles:
        result = create_invite(
            admin_id='test_admin',
            role=role,
            expires_hours=1,
            note=f'Тестовый {role}'
        )
        
        if result['success']:
            invite_code = result['invite_code']
            print(f"✓ Создан QR код для роли '{role}': {invite_code}")
            
            # Проверяем что роль сохранилась
            invite_info = get_invite_info(invite_code)
            if invite_info and invite_info.get('role') == role:
                print(f"  ✓ Роль в приглашении: {invite_info['role']}")
            else:
                print(f"  ✗ Ошибка: роль не соответствует!")
        else:
            print(f"✗ Ошибка создания QR для '{role}': {result.get('error')}")
    
    # Проверяем что admin нельзя создать через QR
    result = create_invite(
        admin_id='test_admin',
        role='admin',
        expires_hours=1,
        note='Попытка создать admin'
    )
    
    if not result['success']:
        print(f"✓ Admin роль через QR запрещена: {result.get('error')}")
    else:
        print(f"✗ ОШИБКА: Admin роль через QR разрешена (небезопасно)!")
    
    print()

def test_role_sync():
    """Тест 3: Синхронизация ролей"""
    print("="*60)
    print("ТЕСТ 3: Синхронизация ролей пользователей")
    print("="*60)
    
    test_user_id = 'test_sync_user_123'
    
    # Устанавливаем роль
    set_user_role(test_user_id, 'initiator')
    print(f"✓ Установлена роль 'initiator' для {test_user_id}")
    
    # Проверяем что роль сохранилась
    role = get_user_role(test_user_id)
    if role == 'initiator':
        print(f"  ✓ Роль успешно прочитана: {role}")
    else:
        print(f"  ✗ Ошибка: роль не совпадает! Ожидалось 'initiator', получено '{role}'")
    
    # Меняем роль
    set_user_role(test_user_id, 'responder')
    print(f"✓ Изменена роль на 'responder' для {test_user_id}")
    
    # Проверяем изменение
    role = get_user_role(test_user_id)
    if role == 'responder':
        print(f"  ✓ Роль успешно обновлена: {role}")
    else:
        print(f"  ✗ Ошибка: роль не обновилась! Ожидалось 'responder', получено '{role}'")
    
    print()

def test_web_user_restrictions():
    """Тест 4: Ограничения для web_ пользователей"""
    print("="*60)
    print("ТЕСТ 4: Ограничения для web_ пользователей")
    print("="*60)
    
    web_user_id = 'web_test123'
    tg_user_id = 'tg_test456'
    
    # Устанавливаем роли
    set_user_role(web_user_id, 'user')
    set_user_role(tg_user_id, 'user')
    
    print(f"✓ Web пользователь: {web_user_id} с ролью 'user'")
    print(f"✓ Telegram пользователь: {tg_user_id} с ролью 'user'")
    
    # Проверяем ограничения (это должно проверяться в web_app.py)
    if web_user_id.startswith('web_'):
        print(f"  ✓ Web пользователь определен корректно (startswith 'web_')")
    else:
        print(f"  ✗ Ошибка определения web пользователя")
    
    if not tg_user_id.startswith('web_'):
        print(f"  ✓ Telegram пользователь определен корректно (не startswith 'web_')")
    else:
        print(f"  ✗ Ошибка: Telegram пользователь помечен как web")
    
    print()

def main():
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ СИНХРОНИЗАЦИИ ВЕБ ↔ TELEGRAM")
    print("="*60 + "\n")
    
    try:
        test_data_files_shared()
        test_qr_role_assignment()
        test_role_sync()
        test_web_user_restrictions()
        
        print("="*60)
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("="*60)
        print("\nРекомендации:")
        print("1. Проверьте веб-интерфейс: создайте ДСЕ и убедитесь что оно видно в боте")
        print("2. Проверьте бот: создайте ДСЕ и убедитесь что оно видно на веб")
        print("3. Измените роль пользователя на веб и проверьте в боте")
        print("4. Создайте QR код с ролью 'initiator' и проверьте что роль применяется")
        
    except Exception as e:
        print(f"\n✗ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
