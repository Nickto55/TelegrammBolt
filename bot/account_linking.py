"""
Account Linking Manager
Модуль для связывания веб-аккаунтов с Telegram аккаунтами
"""
import json
import os
import sys
import secrets
import string
from datetime import datetime, timedelta

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import DATA_DIR
from bot.user_manager import get_users_data, save_users_data, register_user

# Файл для хранения данных привязки аккаунтов
LINKING_FILE = os.path.join(DATA_DIR, "account_linking.json")

def load_linking_data():
    """Загрузить данные привязки аккаунтов"""
    if os.path.exists(LINKING_FILE):
        try:
            with open(LINKING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"web_users": {}, "pending_links": {}, "link_codes": {}}
    return {"web_users": {}, "pending_links": {}, "link_codes": {}}

def save_linking_data(data):
    """Сохранить данные привязки аккаунтов"""
    with open(LINKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_link_code():
    """Генерировать код для привязки аккаунта (6 символов)"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def create_web_user(email, password_hash, first_name, last_name=None):
    """
    Создать веб-пользователя без Telegram привязки
    Возвращает web_user_id
    """
    linking_data = load_linking_data()
    
    # Генерируем уникальный ID для веб-пользователя
    web_user_id = f"web_{int(datetime.now().timestamp())}"
    
    # Проверяем, есть ли уже пользователь с таким email
    for wid, wuser in linking_data["web_users"].items():
        if wuser.get("email") == email:
            return None  # Email уже занят
    
    linking_data["web_users"][web_user_id] = {
        "email": email,
        "password_hash": password_hash,
        "first_name": first_name,
        "last_name": last_name,
        "created_at": datetime.now().isoformat(),
        "telegram_id": None,  # Еще не привязан
        "role": "initiator"  # По умолчанию
    }
    
    save_linking_data(linking_data)
    return web_user_id

def find_web_user_by_email(email):
    """Найти веб-пользователя по email"""
    linking_data = load_linking_data()
    
    for web_user_id, user_data in linking_data["web_users"].items():
        if user_data.get("email") == email:
            return web_user_id, user_data
    
    return None, None

def generate_linking_code_for_web_user(web_user_id):
    """
    Генерировать код привязки для веб-пользователя
    Код действует 24 часа
    """
    linking_data = load_linking_data()
    
    if web_user_id not in linking_data["web_users"]:
        return None
    
    # Генерируем уникальный код
    link_code = generate_link_code()
    
    # Убеждаемся что код уникален
    while link_code in linking_data["link_codes"]:
        link_code = generate_link_code()
    
    # Сохраняем код с истечением через 24 часа
    linking_data["link_codes"][link_code] = {
        "web_user_id": web_user_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        "used": False
    }
    
    save_linking_data(linking_data)
    return link_code

def link_telegram_account(link_code, telegram_id, username, first_name, last_name):
    """
    Привязать Telegram аккаунт к веб-пользователю по коду
    """
    linking_data = load_linking_data()
    
    # Проверяем код
    if link_code not in linking_data["link_codes"]:
        return {"success": False, "error": "Неверный код привязки"}
    
    code_data = linking_data["link_codes"][link_code]
    
    # Проверяем что код не использован
    if code_data["used"]:
        return {"success": False, "error": "Код уже использован"}
    
    # Проверяем что код не истек
    expires_at = datetime.fromisoformat(code_data["expires_at"])
    if datetime.now() > expires_at:
        return {"success": False, "error": "Код истек"}
    
    web_user_id = code_data["web_user_id"]
    web_user = linking_data["web_users"][web_user_id]
    
    # Проверяем что аккаунт еще не привязан
    if web_user["telegram_id"] is not None:
        return {"success": False, "error": "Аккаунт уже привязан к Telegram"}
    
    # Проверяем что этот Telegram ID не привязан к другому веб-аккаунту
    for wid, wuser in linking_data["web_users"].items():
        if wuser.get("telegram_id") == telegram_id:
            return {"success": False, "error": "Этот Telegram аккаунт уже привязан к другому веб-аккаунту"}
    
    # Выполняем привязку
    linking_data["web_users"][web_user_id]["telegram_id"] = telegram_id
    linking_data["web_users"][web_user_id]["telegram_username"] = username
    linking_data["web_users"][web_user_id]["linked_at"] = datetime.now().isoformat()
    
    # Отмечаем код как использованный
    linking_data["link_codes"][link_code]["used"] = True
    linking_data["link_codes"][link_code]["used_at"] = datetime.now().isoformat()
    
    # Регистрируем пользователя в основной системе
    role = web_user.get("role", "initiator")
    register_user(telegram_id, username, first_name, last_name)
    
    # Устанавливаем роль из веб-аккаунта
    from bot.user_manager import set_user_role
    set_user_role(telegram_id, role)
    
    save_linking_data(linking_data)
    
    return {
        "success": True, 
        "message": f"Аккаунт успешно привязан! Ваша роль: {role}",
        "role": role,
        "web_user_id": web_user_id
    }

def get_web_user_by_telegram_id(telegram_id):
    """Получить веб-пользователя по Telegram ID"""
    linking_data = load_linking_data()
    
    for web_user_id, user_data in linking_data["web_users"].items():
        if user_data.get("telegram_id") == telegram_id:
            return web_user_id, user_data
    
    return None, None

def get_telegram_id_by_web_user(web_user_id):
    """Получить Telegram ID по веб-пользователю"""
    linking_data = load_linking_data()
    
    web_user = linking_data["web_users"].get(web_user_id)
    if web_user:
        return web_user.get("telegram_id")
    
    return None

def is_account_linked(web_user_id=None, telegram_id=None):
    """Проверить привязан ли аккаунт"""
    linking_data = load_linking_data()
    
    if web_user_id:
        web_user = linking_data["web_users"].get(web_user_id)
        return web_user and web_user.get("telegram_id") is not None
    
    if telegram_id:
        for web_user_id, user_data in linking_data["web_users"].items():
            if user_data.get("telegram_id") == telegram_id:
                return True
    
    return False

def cleanup_expired_codes():
    """Очистить истекшие коды привязки"""
    linking_data = load_linking_data()
    
    now = datetime.now()
    expired_codes = []
    
    for code, code_data in linking_data["link_codes"].items():
        expires_at = datetime.fromisoformat(code_data["expires_at"])
        if now > expires_at:
            expired_codes.append(code)
    
    for code in expired_codes:
        del linking_data["link_codes"][code]
    
    if expired_codes:
        save_linking_data(linking_data)
    
    return len(expired_codes)

def get_linking_stats():
    """Получить статистику привязки аккаунтов"""
    linking_data = load_linking_data()
    
    total_web_users = len(linking_data["web_users"])
    linked_accounts = sum(1 for user in linking_data["web_users"].values() 
                         if user.get("telegram_id") is not None)
    pending_codes = sum(1 for code in linking_data["link_codes"].values() 
                       if not code["used"] and datetime.fromisoformat(code["expires_at"]) > datetime.now())
    
    return {
        "total_web_users": total_web_users,
        "linked_accounts": linked_accounts,
        "unlinked_accounts": total_web_users - linked_accounts,
        "pending_codes": pending_codes
    }

def authenticate_web_user(email, password_hash):
    """Аутентификация веб-пользователя"""
    web_user_id, user_data = find_web_user_by_email(email)
    
    if web_user_id and user_data.get("password_hash") == password_hash:
        return web_user_id, user_data
    
    return None, None

def update_web_user_role(web_user_id, new_role):
    """Обновить роль веб-пользователя и связанного Telegram аккаунта"""
    linking_data = load_linking_data()
    
    if web_user_id not in linking_data["web_users"]:
        return False
    
    # Обновляем роль веб-пользователя
    linking_data["web_users"][web_user_id]["role"] = new_role
    
    # Если есть привязанный Telegram аккаунт, обновляем и его роль
    telegram_id = linking_data["web_users"][web_user_id].get("telegram_id")
    if telegram_id:
        from bot.user_manager import set_user_role
        set_user_role(telegram_id, new_role)
    
    save_linking_data(linking_data)
    return True

def get_all_web_users():
    """Получить всех веб-пользователей"""
    linking_data = load_linking_data()
    return linking_data["web_users"]


def change_password(web_user_id, old_password_hash, new_password_hash):
    """
    Сменить пароль веб-пользователя
    Возвращает словарь с результатом операции
    """
    linking_data = load_linking_data()
    
    if web_user_id not in linking_data["web_users"]:
        return {"success": False, "error": "Пользователь не найден"}
    
    # Проверяем старый пароль
    current_password_hash = linking_data["web_users"][web_user_id]["password_hash"]
    if current_password_hash != old_password_hash:
        return {"success": False, "error": "Неверный текущий пароль"}
    
    # Меняем пароль
    linking_data["web_users"][web_user_id]["password_hash"] = new_password_hash
    linking_data["web_users"][web_user_id]["password_changed_at"] = datetime.now().isoformat()
    
    save_linking_data(linking_data)
    
    return {"success": True, "message": "Пароль успешно изменен"}