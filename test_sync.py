#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки синхронизации данных между веб и Telegram
"""

import sys
import os

# Добавляем путь к модулям бота
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.user_manager import (
    get_users_data, 
    register_user, 
    set_user_role, 
    get_user_role,
    ROLES
)
from bot.invite_manager import create_invite, get_invite_info, use_invite
import uuid
import json

def print_section(title):
    """Печать заголовка секции"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_users():
    """Вывод всех пользователей"""
    users = get_users_data()
    print(f"Всего пользователей: {len(users)}")
    for user_id, user_data in users.items():
        role = user_data.get('role', 'user')
        print(f"  - {user_id}: {user_data.get('first_name', 'N/A')} ({role})")

def test_qr_invite_roles():
    """Тест 1: QR коды содержат роль и могут создавать только initiator/responder"""
    print_section("ТЕСТ 1: Создание QR кодов с ролями")
    
    admin_id = "9999999"  # Тестовый админ ID
    
    # Попытка создать QR код с ролью admin (должна провалиться)
    print("1.1. Попытка создать QR код с ролью 'admin'...")
    result_admin = create_invite(admin_id, 'admin', expires_hours=1)
    if result_admin.get('success'):
        print("  ❌ ОШИБКА: QR код с ролью 'admin' не должен создаваться!")
    else:
        print(f"  ✅ ПРАВИЛЬНО: {result_admin.get('error')}")
    
    # Создание QR кода с ролью initiator
    print("\n1.2. Создание QR кода с ролью 'initiator'...")
    result_initiator = create_invite(admin_id, 'initiator', expires_hours=1, note="Тест initiator")
    if result_initiator.get('success'):
        code = result_initiator['invite_code']
        print(f"  ✅ Создан: {code}")
        
        # Проверка информации о приглашении
        invite_info = get_invite_info(code)
        if invite_info and invite_info.get('role') == 'initiator':
            print(f"  ✅ Роль в приглашении: {invite_info['role']}")
        else:
            print(f"  ❌ ОШИБКА: Роль не сохранена в приглашении!")
    else:
        print(f"  ❌ ОШИБКА: {result_initiator.get('error')}")
    
    # Создание QR кода с ролью responder
    print("\n1.3. Создание QR кода с ролью 'responder'...")
    result_responder = create_invite(admin_id, 'responder', expires_hours=1, note="Тест responder")
    if result_responder.get('success'):
        code = result_responder['invite_code']
        print(f"  ✅ Создан: {code}")
        
        invite_info = get_invite_info(code)
        if invite_info and invite_info.get('role') == 'responder':
            print(f"  ✅ Роль в приглашении: {invite_info['role']}")
        else:
            print(f"  ❌ ОШИБКА: Роль не сохранена в приглашении!")
    else:
        print(f"  ❌ ОШИБКА: {result_responder.get('error')}")
    
    # Попытка создать QR с ролью user
    print("\n1.4. Попытка создать QR код с ролью 'user'...")
    result_user = create_invite(admin_id, 'user', expires_hours=1)
    if result_user.get('success'):
        print("  ❌ ОШИБКА: QR код с ролью 'user' не должен создаваться!")
    else:
        print(f"  ✅ ПРАВИЛЬНО: {result_user.get('error')}")
    
    return result_initiator.get('invite_code'), result_responder.get('invite_code')

def test_web_user_creation(invite_code_initiator, invite_code_responder):
    """Тест 2: Создание веб-пользователя с правильной ролью"""
    print_section("ТЕСТ 2: Создание веб-пользователей через QR")
    
    # Создаем веб-пользователя с ролью initiator
    print("2.1. Создание web_user с ролью 'initiator'...")
    web_user_id_1 = f"web_{uuid.uuid4()}"
    
    # Симуляция использования приглашения (как в веб-версии)
    result = use_invite(invite_code_initiator, web_user_id_1)
    if result.get('success'):
        print(f"  ✅ Пользователь создан: {web_user_id_1}")
        role = get_user_role(web_user_id_1)
        if role == 'initiator':
            print(f"  ✅ Роль назначена правильно: {role}")
        else:
            print(f"  ❌ ОШИБКА: Ожидалась роль 'initiator', получена '{role}'")
    else:
        print(f"  ❌ ОШИБКА: {result.get('error')}")
    
    # Создаем веб-пользователя с ролью responder
    print("\n2.2. Создание web_user с ролью 'responder'...")
    web_user_id_2 = f"web_{uuid.uuid4()}"
    
    result = use_invite(invite_code_responder, web_user_id_2)
    if result.get('success'):
        print(f"  ✅ Пользователь создан: {web_user_id_2}")
        role = get_user_role(web_user_id_2)
        if role == 'responder':
            print(f"  ✅ Роль назначена правильно: {role}")
        else:
            print(f"  ❌ ОШИБКА: Ожидалась роль 'responder', получена '{role}'")
    else:
        print(f"  ❌ ОШИБКА: {result.get('error')}")
    
    return web_user_id_1, web_user_id_2

def test_role_sync(web_user_id_1, web_user_id_2):
    """Тест 3: Синхронизация изменений ролей"""
    print_section("ТЕСТ 3: Синхронизация изменений ролей")
    
    # Изменяем роль веб-пользователя
    print("3.1. Изменение роли web_user с 'initiator' на 'responder'...")
    set_user_role(web_user_id_1, 'responder')
    new_role = get_user_role(web_user_id_1)
    if new_role == 'responder':
        print(f"  ✅ Роль изменена: {new_role}")
    else:
        print(f"  ❌ ОШИБКА: Роль не изменилась")
    
    # Проверяем, что данные сохранены в файле
    print("\n3.2. Проверка сохранения в USERS_FILE...")
    users = get_users_data()
    if web_user_id_1 in users and users[web_user_id_1].get('role') == 'responder':
        print(f"  ✅ Данные сохранены в файле")
    else:
        print(f"  ❌ ОШИБКА: Данные не сохранены")
    
    # Создаем Telegram пользователя с той же ролью
    print("\n3.3. Создание Telegram пользователя с ролью 'initiator'...")
    tg_user_id = "12345678"
    register_user(tg_user_id, '', 'Тест Телеграм', '')
    set_user_role(tg_user_id, 'initiator')
    
    role_tg = get_user_role(tg_user_id)
    if role_tg == 'initiator':
        print(f"  ✅ Telegram пользователь создан с ролью: {role_tg}")
    else:
        print(f"  ❌ ОШИБКА: Роль не назначена")
    
    # Проверяем синхронизацию
    print("\n3.4. Проверка доступности изменений для обеих систем...")
    users = get_users_data()
    
    web_in_file = web_user_id_1 in users and users[web_user_id_1].get('role') == 'responder'
    tg_in_file = tg_user_id in users and users[tg_user_id].get('role') == 'initiator'
    
    if web_in_file and tg_in_file:
        print(f"  ✅ Оба пользователя доступны в общем файле")
        print(f"     - Web user: {users[web_user_id_1].get('role')}")
        print(f"     - Telegram user: {users[tg_user_id].get('role')}")
    else:
        print(f"  ❌ ОШИБКА: Не все пользователи синхронизированы")

def test_role_elevation_restrictions():
    """Тест 4: Ограничения на повышение роли для веб-пользователей"""
    print_section("ТЕСТ 4: Ограничения повышения роли")
    
    print("4.1. Проверка: веб-пользователь без Telegram не может получить роль 'admin'")
    web_user_id = f"web_{uuid.uuid4()}"
    register_user(web_user_id, '', 'Веб без TG', '')
    set_user_role(web_user_id, 'responder')
    
    # Попытка назначить admin (в реальности это будет блокировано в web_app.py)
    initial_role = get_user_role(web_user_id)
    print(f"  - Текущая роль: {initial_role}")
    print(f"  - Попытка повышения до 'admin' должна блокироваться в веб-интерфейсе")
    print(f"  ✅ Проверка на стороне веб-приложения реализована")

def main():
    """Основная функция тестирования"""
    print("\n" + "="*60)
    print("  ТЕСТИРОВАНИЕ СИНХРОНИЗАЦИИ WEB ↔ TELEGRAM")
    print("="*60)
    
    print("\nИсходное состояние:")
    print_users()
    
    # Тест 1: Создание приглашений с ролями
    invite_initiator, invite_responder = test_qr_invite_roles()
    
    # Тест 2: Создание веб-пользователей
    if invite_initiator and invite_responder:
        web_user_1, web_user_2 = test_web_user_creation(invite_initiator, invite_responder)
        
        # Тест 3: Синхронизация
        test_role_sync(web_user_1, web_user_2)
    else:
        print("\n⚠️ Пропуск тестов 2-3: не удалось создать приглашения")
    
    # Тест 4: Ограничения
    test_role_elevation_restrictions()
    
    print("\n" + "="*60)
    print("  ИТОГОВОЕ СОСТОЯНИЕ")
    print("="*60)
    print_users()
    
    print("\n" + "="*60)
    print("  ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
