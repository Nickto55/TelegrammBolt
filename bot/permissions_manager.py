"""
Модуль управления правами и доступом пользователей
Единая система для веб-интерфейса и телеграм бота
"""

import json
import os
import sys
from typing import Dict, List, Set, Optional

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import USERS_FILE, ADMIN_IDS
from bot.user_manager import get_user_role, ROLES

# Определение всех доступных прав в системе
PERMISSIONS = {
    # Административные права
    'admin': {
        'name': 'Полный доступ администратора',
        'description': 'Доступ ко всем функциям системы',
        'roles': ['admin']
    },
    'manage_users': {
        'name': 'Управление пользователями',
        'description': 'Изменение ролей и прав пользователей',
        'roles': ['admin']
    },
    'view_users': {
        'name': 'Просмотр пользователей',
        'description': 'Просмотр списка пользователей',
        'roles': ['admin']
    },
    
    # Права на работу с ДСЕ
    'view_dse': {
        'name': 'Просмотр ДСЕ',
        'description': 'Просмотр списка и деталей ДСЕ',
        'roles': ['admin', 'responder']
    },
    'add_dse': {
        'name': 'Создание ДСЕ',
        'description': 'Создание новых заявок ДСЕ',
        'roles': ['admin', 'initiator']
    },
    'edit_dse': {
        'name': 'Редактирование ДСЕ',
        'description': 'Изменение существующих ДСЕ',
        'roles': ['admin']
    },
    'delete_dse': {
        'name': 'Удаление ДСЕ',
        'description': 'Удаление записей ДСЕ',
        'roles': ['admin']
    },
    'view_own_dse': {
        'name': 'Просмотр своих ДСЕ',
        'description': 'Просмотр только своих созданных ДСЕ',
        'roles': ['admin', 'responder', 'initiator']
    },
    
    # Права на экспорт и отчеты
    'export_data': {
        'name': 'Экспорт данных',
        'description': 'Экспорт данных в Excel и другие форматы',
        'roles': ['admin', 'responder']
    },
    'pdf_export': {
        'name': 'Создание PDF отчетов',
        'description': 'Генерация PDF отчетов по ДСЕ',
        'roles': ['admin', 'responder']
    },
    
    # Права на чат
    'chat_dse': {
        'name': 'Чат по ДСЕ',
        'description': 'Общение в чатах по ДСЕ (Инициатор: доступен чат для своих заявок)',
        'roles': ['admin', 'responder', 'initiator']
    },
    'view_chat_history': {
        'name': 'История чатов',
        'description': 'Просмотр истории всех чатов',
        'roles': ['admin', 'responder']
    },
    
    # Права на приглашения и QR коды
    'manage_invites': {
        'name': 'Управление приглашениями',
        'description': 'Создание и управление QR-приглашениями',
        'roles': ['admin']
    },
    'use_invite': {
        'name': 'Использование приглашений',
        'description': 'Активация QR-приглашений',
        'roles': ['admin', 'responder', 'initiator', 'user']
    },
    
    # Права на подписки и уведомления
    'manage_subscriptions': {
        'name': 'Управление подписками',
        'description': 'Подписка на уведомления о новых ДСЕ',
        'roles': ['admin']
    },
    
    # Права на терминал (только для веб-интерфейса)
    'use_terminal': {
        'name': 'Веб-терминал',
        'description': 'Доступ к веб-терминалу системы',
        'roles': ['admin', 'responder']
    },
    
    # Права на связывание аккаунтов
    'link_account': {
        'name': 'Связывание аккаунтов',
        'description': 'Связывание веб и телеграм аккаунтов',
        'roles': ['admin', 'responder', 'initiator', 'user']
    },
    'create_web_user': {
        'name': 'Создание веб-пользователей',
        'description': 'Создание пользователей для веб-интерфейса',
        'roles': ['admin']
    },
    
    # Права на использование форм
    'use_form': {
        'name': 'Использование формы',
        'description': 'Доступ к формам создания ДСЕ через бота',
        'roles': ['admin', 'initiator']
    },
    'view_main_menu': {
        'name': 'Главное меню',
        'description': 'Доступ к главному меню бота',
        'roles': ['admin', 'responder', 'initiator']
    },
    
    # Права на отслеживание
    'watch_dse': {
        'name': 'Отслеживание ДСЕ',
        'description': 'Подписка на обновления по конкретным ДСЕ',
        'roles': ['admin', 'responder']
    },
    
    # Права на профиль
    'view_dashboard_stats': {
        'name': 'Просмотр статистики дашборда',
        'description': 'Просмотр общей статистики в панели управления (для ответчика - как дополнительное право)',
        'roles': ['admin']  # Для responder только с индивидуальным правом
    },
    
    'view_profile': {
        'name': 'Просмотр профиля',
        'description': 'Просмотр своего профиля',
        'roles': ['admin', 'responder', 'initiator', 'user']
    },
    'edit_profile': {
        'name': 'Редактирование профиля',
        'description': 'Изменение данных профиля',
        'roles': ['admin', 'responder', 'initiator', 'user']
    },
}


# Группировка прав для удобства отображения
PERMISSION_GROUPS = {
    'Административные': ['admin', 'manage_users', 'view_users', 'use_terminal', 'create_web_user'],
    'Работа с ДСЕ': ['view_dse', 'add_dse', 'edit_dse', 'delete_dse', 'view_own_dse'],
    'Экспорт и отчеты': ['export_data', 'pdf_export'],
    'Чат': ['chat_dse', 'view_chat_history'],
    'Приглашения': ['manage_invites', 'use_invite'],
    'Подписки': ['manage_subscriptions', 'watch_dse'],
    'Аккаунты': ['link_account'],
    'Бот': ['use_form', 'view_main_menu'],
    'Дашборд': ['view_dashboard_stats'],
    'Профиль': ['view_profile', 'edit_profile'],
}


def has_permission(user_id: str, permission: str) -> bool:
    """
    Проверить наличие права у пользователя
    
    Args:
        user_id: ID пользователя (строка)
        permission: Название права
        
    Returns:
        True если пользователь имеет право, иначе False
    """
    # Преобразуем в строку на всякий случай
    user_id = str(user_id)
    
    # Проверяем, является ли пользователь администратором по списку (наивысший приоритет)
    if user_id in ADMIN_IDS or str(user_id) in ADMIN_IDS:
        return True
    
    # Получаем роль пользователя
    role = get_user_role(user_id)
    
    # Администраторы имеют все права
    if role == 'admin':
        return True
    
    # Проверяем, существует ли такое право
    if permission not in PERMISSIONS:
        return False
    
    # Проверяем, имеет ли роль пользователя данное право
    allowed_roles = PERMISSIONS[permission]['roles']
    return role in allowed_roles


def get_user_permissions(user_id: str) -> Dict[str, bool]:
    """
    Получить словарь всех прав пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Словарь {permission_name: has_permission}
    """
    user_id = str(user_id)
    permissions_dict = {}
    
    for permission in PERMISSIONS.keys():
        permissions_dict[permission] = has_permission(user_id, permission)
    
    return permissions_dict


def get_role_permissions(role: str) -> List[str]:
    """
    Получить список всех прав для роли
    
    Args:
        role: Название роли
        
    Returns:
        Список названий прав
    """
    if role not in ROLES:
        return []
    
    role_permissions = []
    for permission, details in PERMISSIONS.items():
        if role in details['roles']:
            role_permissions.append(permission)
    
    return role_permissions


def get_permissions_by_group() -> Dict[str, List[Dict]]:
    """
    Получить права, сгруппированные по категориям
    
    Returns:
        Словарь {group_name: [permission_details]}
    """
    grouped = {}
    
    for group_name, permission_list in PERMISSION_GROUPS.items():
        grouped[group_name] = []
        for perm_name in permission_list:
            if perm_name in PERMISSIONS:
                perm_info = PERMISSIONS[perm_name].copy()
                perm_info['key'] = perm_name
                grouped[group_name].append(perm_info)
    
    return grouped


def can_manage_user(manager_id: str, target_user_id: str) -> bool:
    """
    Проверить, может ли manager изменять права target_user
    
    Args:
        manager_id: ID менеджера
        target_user_id: ID целевого пользователя
        
    Returns:
        True если может управлять, иначе False
    """
    manager_id = str(manager_id)
    target_user_id = str(target_user_id)
    
    # Проверяем права менеджера
    if not has_permission(manager_id, 'manage_users'):
        return False
    
    # Нельзя изменять себя
    if manager_id == target_user_id:
        return False
    
    # Нельзя изменять администраторов из списка ADMIN_IDS
    if target_user_id in ADMIN_IDS or str(target_user_id) in ADMIN_IDS:
        return False
    
    return True


def set_custom_permission(user_id: str, permission: str, value: bool) -> bool:
    """
    Установить индивидуальное право пользователю (переопределяет роль)
    
    Args:
        user_id: ID пользователя
        permission: Название права
        value: True для разрешения, False для запрета
        
    Returns:
        True если успешно, иначе False
    """
    user_id = str(user_id)
    
    # Проверяем, существует ли такое право
    if permission not in PERMISSIONS:
        return False
    
    # Загружаем данные пользователей
    from bot.user_manager import get_users_data, save_users_data
    users_data = get_users_data()
    
    if user_id not in users_data:
        return False
    
    # Создаем словарь индивидуальных прав, если его нет
    if 'custom_permissions' not in users_data[user_id]:
        users_data[user_id]['custom_permissions'] = {}
    
    # Устанавливаем право
    users_data[user_id]['custom_permissions'][permission] = value
    
    # Сохраняем
    save_users_data(users_data)
    return True


def get_custom_permissions(user_id: str) -> Dict[str, bool]:
    """
    Получить индивидуальные права пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Словарь индивидуальных прав или пустой словарь
    """
    user_id = str(user_id)
    
    from bot.user_manager import get_user_data
    user_data = get_user_data(user_id)
    
    if not user_data:
        return {}
    
    return user_data.get('custom_permissions', {})


def has_permission_with_custom(user_id: str, permission: str) -> bool:
    """
    Проверить право с учетом индивидуальных настроек
    
    Args:
        user_id: ID пользователя
        permission: Название права
        
    Returns:
        True если имеет право, иначе False
    """
    user_id = str(user_id)
    
    # Сначала проверяем индивидуальные права
    custom_perms = get_custom_permissions(user_id)
    if permission in custom_perms:
        return custom_perms[permission]
    
    # Если индивидуального права нет, проверяем по роли
    return has_permission(user_id, permission)


def get_all_permissions_info() -> Dict:
    """
    Получить информацию обо всех правах в системе
    
    Returns:
        Словарь с информацией о правах
    """
    return PERMISSIONS.copy()


def check_telegram_bot_access(user_id: str) -> Dict[str, bool]:
    """
    Проверить доступ к функциям телеграм бота

        Args:
        user_id: ID пользователя
        
    Returns:
        Словарь с доступными функциями бота
    """
    return {
        'use_main_menu': has_permission(user_id, 'view_main_menu'),
        'create_dse': has_permission(user_id, 'add_dse'),
        'view_dse': has_permission(user_id, 'view_dse'),
        'chat': has_permission(user_id, 'chat_dse'),
        'watch_dse': has_permission(user_id, 'watch_dse'),
        'export_pdf': has_permission(user_id, 'pdf_export'),
        'use_form': has_permission(user_id, 'use_form'),
    }


def check_web_access(user_id: str) -> Dict[str, bool]:
    """
    Проверить доступ к функциям веб-интерфейса
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Словарь с доступными функциями веб-интерфейса
    """
    return {
        'dashboard': True,  # Все авторизованные пользователи могут видеть дашборд
        'view_dashboard_stats': has_permission(user_id, 'view_dashboard_stats'),  # Статистика только для admin и responder с доп правом
        'view_dse': has_permission(user_id, 'view_dse'),
        'create_dse': has_permission(user_id, 'add_dse'),
        'edit_dse': has_permission(user_id, 'edit_dse'),
        'delete_dse': has_permission(user_id, 'delete_dse'),
        'export_excel': has_permission(user_id, 'export_data'),
        'export_pdf': has_permission(user_id, 'pdf_export'),
        'chat': has_permission(user_id, 'chat_dse'),
        'manage_users': has_permission(user_id, 'manage_users'),
        'view_users': has_permission(user_id, 'view_users'),
        'manage_invites': has_permission(user_id, 'manage_invites'),
        'terminal': has_permission(user_id, 'use_terminal'),
        'admin_panel': has_permission(user_id, 'admin'),
    }
