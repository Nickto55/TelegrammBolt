#!/usr/bin/env python3
"""
Скрипт для быстрой проверки системы управления ролями
"""

import json
import os

USERS_FILE = 'users_data.json'

def show_users_and_roles():
    """Показать всех пользователей и их роли"""
    
    if not os.path.exists(USERS_FILE):
        print("❌ Файл users_data.json не найден!")
        return
    
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    print("\n" + "="*80)
    print("👥 СПИСОК ПОЛЬЗОВАТЕЛЕЙ И ИХ РОЛЕЙ")
    print("="*80 + "\n")
    
    # Группировка по ролям
    roles_users = {
        'admin': [],
        'responder': [],
        'initiator': [],
        'user': []
    }
    
    for user_id, user_data in users.items():
        role = user_data.get('role', 'user')
        if role in roles_users:
            roles_users[role].append((user_id, user_data))
    
    # Отображение по ролям
    role_icons = {
        'admin': '⭐',
        'responder': '🔧',
        'initiator': '📝',
        'user': '👤'
    }
    
    role_names = {
        'admin': 'Администраторы',
        'responder': 'Ответственные',
        'initiator': 'Инициаторы',
        'user': 'Пользователи'
    }
    
    for role, users_list in roles_users.items():
        if users_list:
            print(f"\n{role_icons[role]} {role_names[role].upper()} ({len(users_list)}):")
            print("-" * 80)
            
            for user_id, user_data in users_list:
                name = f"{user_data.get('first_name', 'Н/Д')} {user_data.get('last_name', '')}".strip()
                username = user_data.get('username', 'нет username')
                permissions = user_data.get('permissions', [])
                
                print(f"  • ID: {user_id}")
                print(f"    Имя: {name}")
                print(f"    Username: @{username}" if username != 'нет username' else f"    Username: {username}")
                
                if permissions:
                    print(f"    Права: {', '.join(permissions)}")
                else:
                    print(f"    Права: базовые права роли")
                print()
    
    print("="*80)
    print(f"\n📊 Всего пользователей: {len(users)}")
    print(f"   • Администраторов: {len(roles_users['admin'])}")
    print(f"   • Ответственных: {len(roles_users['responder'])}")
    print(f"   • Инициаторов: {len(roles_users['initiator'])}")
    print(f"   • Обычных: {len(roles_users['user'])}")
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    show_users_and_roles()
