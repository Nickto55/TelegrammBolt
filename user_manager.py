# user_manager.py
import json
import os
from config import USERS_FILE, ADMIN_IDS

# Роли пользователей
ROLES = {
    'admin': 'Администратор',
    'responder': 'Ответчик',
    'initiator': 'Инициатор',
    'user': 'Пользователь'
}


def get_users_data():
    """Получить данные пользователей"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_users_data(data):
    """Сохранить данные пользователей"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def register_user(user_id, username, first_name, last_name):
    """Регистрация пользователя"""
    users_data = get_users_data()

    if user_id not in users_data:
        # Проверяем, является ли пользователь администратором по списку
        role = 'admin' if user_id in ADMIN_IDS else 'user'
        users_data[user_id] = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'registered': True
        }
        save_users_data(users_data)

    return users_data[user_id]


def get_user_role(user_id):
    """Получить роль пользователя"""
    # Проверяем, является ли пользователь администратором по списку (приоритет)
    if str(user_id) in ADMIN_IDS:
        return 'admin'

    users_data = get_users_data()
    user = users_data.get(str(user_id), {})
    return user.get('role', 'user')


def set_user_role(user_id, role):
    """Установить роль пользователю"""
    if role not in ROLES:
        return False

    users_data = get_users_data()
    if str(user_id) in users_data:
        users_data[str(user_id)]['role'] = role
        save_users_data(users_data)
        return True
    return False


def has_permission(user_id, permission):
    """Проверить права пользователя"""
    # Администраторы из списка имеют приоритет
    if str(user_id) in ADMIN_IDS:
        return True

    role = get_user_role(user_id)

    # Админ может всё
    if role == 'admin':
        return True

    # Ответчик может просматривать ДСЕ, отслеживать и общаться по ДСЕ
    if role == 'responder':
        if permission in ['chat_dse', 'view_main_menu', 'view_dse_list', 'watch_dse']:
            return True

    # Инициатор может использовать форму
    if role == 'initiator' and permission in ['use_form', 'view_main_menu']:
        return True

    # Обычные пользователи ничего не могут
    if role == 'user':
        return False

    # По умолчанию для других ролей
    return permission == 'user'


def get_all_users():
    """Получить список всех пользователей"""
    return get_users_data()


def get_users_by_role(role):
    """Получить пользователей по роли"""
    users_data = get_users_data()
    return {uid: user for uid, user in users_data.items() if user.get('role') == role}
