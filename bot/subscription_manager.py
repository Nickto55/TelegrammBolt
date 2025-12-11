#!/usr/bin/env python3
"""
Модуль управления подписками на новые заявки
Позволяет пользователям подписаться на автоматическое получение PDF всех новых заявок
"""

import json
import os
import sys
from datetime import datetime

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import DATA_DIR

SUBSCRIPTIONS_FILE = str(DATA_DIR / "subscriptions.json")

# Типы доставки подписок
DELIVERY_TYPES = {
    'telegram': 'Telegram чат',
    'email': 'Email',
    'both': 'Telegram и Email'
}


def load_subscriptions():
    """Загрузить все подписки"""
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_subscriptions(data):
    """Сохранить подписки"""
    try:
        with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения подписок: {e}")
        return False


def add_subscription(user_id, delivery_type='telegram', email=None):
    """
    Добавить подписку на новые заявки
    
    Args:
        user_id: ID пользователя Telegram
        delivery_type: тип доставки ('telegram', 'email', 'both')
        email: email для отправки (если delivery_type == 'email' или 'both')
    
    Returns:
        bool: успешность операции
    """
    if delivery_type not in DELIVERY_TYPES:
        return False
    
    if delivery_type in ['email', 'both'] and not email:
        return False
    
    subscriptions = load_subscriptions()
    user_id_str = str(user_id)
    
    subscriptions[user_id_str] = {
        'delivery_type': delivery_type,
        'email': email if delivery_type in ['email', 'both'] else None,
        'created_at': datetime.now().isoformat(),
        'active': True
    }
    
    return save_subscriptions(subscriptions)


def remove_subscription(user_id):
    """
    Удалить подписку пользователя
    
    Args:
        user_id: ID пользователя Telegram
    
    Returns:
        bool: успешность операции
    """
    subscriptions = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str in subscriptions:
        del subscriptions[user_id_str]
        return save_subscriptions(subscriptions)
    
    return False


def get_subscription(user_id):
    """
    Получить подписку пользователя
    
    Args:
        user_id: ID пользователя Telegram
    
    Returns:
        dict или None: данные подписки или None если не подписан
    """
    subscriptions = load_subscriptions()
    return subscriptions.get(str(user_id))


def is_subscribed(user_id):
    """
    Проверить подписан ли пользователь
    
    Args:
        user_id: ID пользователя Telegram
    
    Returns:
        bool: True если подписан и подписка активна
    """
    subscription = get_subscription(user_id)
    return subscription is not None and subscription.get('active', False)


def toggle_subscription(user_id):
    """
    Переключить статус активности подписки
    
    Args:
        user_id: ID пользователя Telegram
    
    Returns:
        bool: новый статус (True = активна, False = неактивна)
    """
    subscriptions = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str in subscriptions:
        current_status = subscriptions[user_id_str].get('active', True)
        subscriptions[user_id_str]['active'] = not current_status
        save_subscriptions(subscriptions)
        return subscriptions[user_id_str]['active']
    
    return False


def get_all_active_subscriptions():
    """
    Получить все активные подписки
    
    Returns:
        dict: словарь {user_id: subscription_data} для всех активных подписок
    """
    subscriptions = load_subscriptions()
    return {
        user_id: data 
        for user_id, data in subscriptions.items() 
        if data.get('active', False)
    }


def get_telegram_subscribers():
    """
    Получить список user_id подписанных на уведомления в Telegram
    
    Returns:
        list: список user_id (строки)
    """
    active_subs = get_all_active_subscriptions()
    return [
        user_id 
        for user_id, data in active_subs.items() 
        if data.get('delivery_type') in ['telegram', 'both']
    ]


def get_email_subscribers():
    """
    Получить список email подписчиков
    
    Returns:
        list: список словарей {'user_id': str, 'email': str}
    """
    active_subs = get_all_active_subscriptions()
    return [
        {'user_id': user_id, 'email': data.get('email')}
        for user_id, data in active_subs.items() 
        if data.get('delivery_type') in ['email', 'both'] and data.get('email')
    ]


def update_subscription_email(user_id, email):
    """
    Обновить email подписки
    
    Args:
        user_id: ID пользователя Telegram
        email: новый email
    
    Returns:
        bool: успешность операции
    """
    subscriptions = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str in subscriptions:
        subscriptions[user_id_str]['email'] = email
        subscriptions[user_id_str]['updated_at'] = datetime.now().isoformat()
        return save_subscriptions(subscriptions)
    
    return False


def get_subscription_stats():
    """
    Получить статистику подписок
    
    Returns:
        dict: статистика подписок
    """
    subscriptions = load_subscriptions()
    active_subs = get_all_active_subscriptions()
    
    telegram_count = len([
        s for s in active_subs.values() 
        if s.get('delivery_type') in ['telegram', 'both']
    ])
    
    email_count = len([
        s for s in active_subs.values() 
        if s.get('delivery_type') in ['email', 'both']
    ])
    
    return {
        'total': len(subscriptions),
        'active': len(active_subs),
        'inactive': len(subscriptions) - len(active_subs),
        'telegram': telegram_count,
        'email': email_count
    }
