# user_manager.py
import json
import os
import sys

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import USERS_FILE, ADMIN_IDS

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

    # Маппинг прав для совместимости с веб-интерфейсом
    permission_mapping = {
        'view_dse': 'view_dse_list',
        'export_data': 'pdf_export',
        'add_dse': 'use_form',  # Только админы могут добавлять
        'edit_dse': 'admin',    # Только админы могут редактировать
        'delete_dse': 'admin',  # Только админы могут удалять
        'manage_subscriptions': 'admin',  # Только админы управляют подписками
    }
    
    # Если используется веб-право, преобразуем его в право бота
    if permission in permission_mapping:
        permission = permission_mapping[permission]

    # Ответчик может просматривать ДСЕ, отслеживать, общаться по ДСЕ и создавать PDF отчеты
    if role == 'responder':
        if permission in ['chat_dse', 'view_main_menu', 'view_dse_list', 'watch_dse', 'pdf_export']:
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


# === ФУНКЦИИ РАБОТЫ С КЛИЧКАМИ ===

def set_user_nickname(user_id, nickname):
    """Установить кличку пользователю"""
    users_data = get_users_data()
    
    if str(user_id) in users_data:
        users_data[str(user_id)]['nickname'] = nickname
        save_users_data(users_data)
        return True
    return False


def remove_user_nickname(user_id):
    """Удалить кличку пользователя"""
    users_data = get_users_data()
    
    if str(user_id) in users_data and 'nickname' in users_data[str(user_id)]:
        del users_data[str(user_id)]['nickname']
        save_users_data(users_data)
        return True
    return False


def get_user_nickname(user_id):
    """Получить кличку пользователя"""
    users_data = get_users_data()
    user = users_data.get(str(user_id), {})
    return user.get('nickname', None)


def get_user_display_name(user_id):
    """Получить отображаемое имя пользователя (кличка или имя)"""
    users_data = get_users_data()
    user = users_data.get(str(user_id), {})
    
    # Если есть кличка, возвращаем её
    nickname = user.get('nickname')
    if nickname:
        return nickname
    
    # Иначе возвращаем имя или username
    first_name = user.get('first_name', '')
    username = user.get('username', '')
    
    if first_name:
        return first_name
    elif username:
        return f"@{username}"
    else:
        return f"ID:{user_id}"


def check_nickname_exists(nickname):
    """Проверить, существует ли уже такая кличка"""
    users_data = get_users_data()
    
    for user_id, user_data in users_data.items():
        if user_data.get('nickname', '').lower() == nickname.lower():
            return True
    return False


def get_all_nicknames():
    """Получить все существующие клички"""
    users_data = get_users_data()
    nicknames = {}
    
    for user_id, user_data in users_data.items():
        nickname = user_data.get('nickname')
        if nickname:
            nicknames[user_id] = nickname
    
    return nicknames


# === ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ВЕБ-ИНТЕРФЕЙСА ===

def is_user_registered(user_id):
    """Проверить, зарегистрирован ли пользователь"""
    users_data = get_users_data()
    return str(user_id) in users_data


def get_user_data(user_id):
    """Получить данные конкретного пользователя"""
    users_data = get_users_data()
    return users_data.get(str(user_id), None)
