"""
Invite Manager - QR коды для приглашения пользователей
Система генерации и валидации QR кодов приглашений с ролями
"""
import json
import os
import sys
import secrets
import string
import qrcode
import base64
from io import BytesIO
from datetime import datetime, timedelta

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import DATA_DIR, PHOTOS_DIR
from bot.user_manager import register_user, set_user_role, ROLES

# Файл для хранения приглашений
INVITES_FILE = os.path.join(DATA_DIR, "invites.json")

def load_invites_data():
    """Загрузить данные приглашений"""
    if os.path.exists(INVITES_FILE):
        try:
            with open(INVITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"invites": {}, "used_invites": {}}
    return {"invites": {}, "used_invites": {}}

def save_invites_data(data):
    """Сохранить данные приглашений"""
    with open(INVITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_invite_code():
    """Генерировать уникальный код приглашения (12 символов)"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))

def create_invite(admin_id, role, expires_hours=168, note=""):
    """
    Создать приглашение
    :param admin_id: ID администратора создающего приглашение
    :param role: Роль которая будет назначена (только 'initiator' или 'responder')
    :param expires_hours: Количество часов до истечения (по умолчанию 7 дней)
    :param note: Заметка для приглашения
    :return: dict с кодом приглашения и данными
    """
    # QR коды могут добавлять только инициаторов и ответчиков
    allowed_roles = ['initiator', 'responder']
    if role not in allowed_roles:
        return {"success": False, "error": f"QR коды могут создавать только роли: {', '.join(allowed_roles)}"}
    
    invites_data = load_invites_data()
    
    # Генерируем уникальный код
    invite_code = generate_invite_code()
    while invite_code in invites_data["invites"] or invite_code in invites_data["used_invites"]:
        invite_code = generate_invite_code()
    
    # Создаем данные приглашения
    invite_data = {
        "code": invite_code,
        "admin_id": admin_id,
        "role": role,
        "note": note,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
        "used": False,
        "max_uses": 1  # Один код = один пользователь
    }
    
    invites_data["invites"][invite_code] = invite_data
    save_invites_data(invites_data)
    
    return {"success": True, "invite_code": invite_code, "data": invite_data}

def generate_qr_code(invite_code, format='PNG'):
    """
    Генерировать QR код для приглашения
    :param invite_code: Код приглашения
    :param format: Формат изображения ('PNG', 'JPEG')
    :return: Base64 encoded изображение или путь к файлу
    """
    # Получаем информацию о приглашении для включения роли
    invites_data = load_invites_data()
    invite_info = invites_data.get("invites", {}).get(invite_code)
    role_suffix = f"_{invite_info.get('role', '')}" if invite_info else ""
    
    # URL для сканирования (используем имя бота из конфига)
    from config.config import BOT_USERNAME
    invite_url = f"https://t.me/{BOT_USERNAME}?start=invite_{invite_code}{role_suffix}"
    
    # Создаем QR код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(invite_url)
    qr.make(fit=True)
    
    # Создаем изображение
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Сохраняем в память как base64
    buffer = BytesIO()
    img.save(buffer, format=format)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # Также сохраняем файл для возможного использования
    qr_filename = f"invite_{invite_code}.png"
    qr_filepath = os.path.join(PHOTOS_DIR, "qr_codes", qr_filename)
    
    # Создаем папку если не существует
    os.makedirs(os.path.join(PHOTOS_DIR, "qr_codes"), exist_ok=True)
    
    # Сохраняем файл
    with open(qr_filepath, 'wb') as f:
        f.write(base64.b64decode(img_str))
    
    return {
        "base64": f"data:image/{format.lower()};base64,{img_str}",
        "filepath": qr_filepath,
        "filename": qr_filename,
        "url": invite_url
    }

def validate_invite(invite_code):
    """
    Валидировать приглашение
    :param invite_code: Код приглашения
    :return: dict с результатом валидации
    """
    invites_data = load_invites_data()
    
    if invite_code not in invites_data["invites"]:
        return {"valid": False, "error": "Приглашение не найдено"}
    
    invite_data = invites_data["invites"][invite_code]
    
    # Проверяем что приглашение не использовано
    if invite_data["used"]:
        return {"valid": False, "error": "Приглашение уже использовано"}
    
    # Проверяем срок действия
    expires_at = datetime.fromisoformat(invite_data["expires_at"])
    if datetime.now() > expires_at:
        return {"valid": False, "error": "Срок действия приглашения истек"}
    
    return {"valid": True, "data": invite_data}

def use_invite(invite_code, telegram_id, username, first_name, last_name):
    """
    Использовать приглашение для регистрации пользователя
    :param invite_code: Код приглашения
    :param telegram_id: Telegram ID пользователя
    :param username: Username пользователя
    :param first_name: Имя пользователя
    :param last_name: Фамилия пользователя
    :return: dict с результатом
    """
    # Валидируем приглашение
    validation = validate_invite(invite_code)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    invite_data = validation["data"]
    
    # Проверяем что пользователь еще не зарегистрирован
    from bot.user_manager import is_user_registered
    if is_user_registered(telegram_id):
        return {"success": False, "error": "Пользователь уже зарегистрирован"}
    
    # Регистрируем пользователя
    user_data = register_user(telegram_id, username, first_name, last_name)
    
    # Устанавливаем роль из приглашения
    role = invite_data["role"]
    set_user_role(telegram_id, role)
    
    # Отмечаем приглашение как использованное
    invites_data = load_invites_data()
    invites_data["invites"][invite_code]["used"] = True
    invites_data["invites"][invite_code]["used_at"] = datetime.now().isoformat()
    invites_data["invites"][invite_code]["used_by"] = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name
    }
    
    # Перемещаем в использованные приглашения
    invites_data["used_invites"][invite_code] = invites_data["invites"][invite_code]
    del invites_data["invites"][invite_code]
    
    save_invites_data(invites_data)
    
    return {
        "success": True,
        "message": f"Добро пожаловать! Вам назначена роль: {ROLES[role]}",
        "role": role,
        "role_name": ROLES[role]
    }

def get_active_invites(admin_id=None):
    """
    Получить активные приглашения
    :param admin_id: ID администратора (если указан, только его приглашения)
    :return: список активных приглашений
    """
    invites_data = load_invites_data()
    active_invites = []
    
    now = datetime.now()
    
    for code, invite_data in invites_data["invites"].items():
        # Пропускаем использованные
        if invite_data["used"]:
            continue
            
        # Пропускаем истекшие
        expires_at = datetime.fromisoformat(invite_data["expires_at"])
        if now > expires_at:
            continue
            
        # Фильтруем по админу если указан
        if admin_id and invite_data["admin_id"] != admin_id:
            continue
            
        active_invites.append(invite_data)
    
    return active_invites

def get_used_invites(admin_id=None):
    """
    Получить использованные приглашения
    :param admin_id: ID администратора (если указан, только его приглашения)
    :return: список использованных приглашений
    """
    invites_data = load_invites_data()
    used_invites = []
    
    for code, invite_data in invites_data["used_invites"].items():
        # Фильтруем по админу если указан
        if admin_id and invite_data["admin_id"] != admin_id:
            continue
            
        used_invites.append(invite_data)
    
    return used_invites

def delete_invite(invite_code, admin_id):
    """
    Удалить приглашение (только создатель может удалить)
    :param invite_code: Код приглашения
    :param admin_id: ID администратора
    :return: dict с результатом
    """
    invites_data = load_invites_data()
    
    if invite_code not in invites_data["invites"]:
        return {"success": False, "error": "Приглашение не найдено"}
    
    invite_data = invites_data["invites"][invite_code]
    
    # Проверяем что это создатель приглашения
    if invite_data["admin_id"] != admin_id:
        return {"success": False, "error": "Вы можете удалять только свои приглашения"}
    
    # Удаляем приглашение
    del invites_data["invites"][invite_code]
    save_invites_data(invites_data)
    
    # Удаляем QR код файл если существует
    qr_filename = f"invite_{invite_code}.png"
    qr_filepath = os.path.join(PHOTOS_DIR, "qr_codes", qr_filename)
    if os.path.exists(qr_filepath):
        os.remove(qr_filepath)
    
    return {"success": True, "message": "Приглашение удалено"}

def cleanup_expired_invites():
    """Очистить истекшие приглашения"""
    invites_data = load_invites_data()
    
    now = datetime.now()
    expired_codes = []
    
    for code, invite_data in invites_data["invites"].items():
        expires_at = datetime.fromisoformat(invite_data["expires_at"])
        if now > expires_at:
            expired_codes.append(code)
    
    # Перемещаем истекшие в отдельную категорию для истории
    for code in expired_codes:
        invite_data = invites_data["invites"][code]
        invite_data["expired"] = True
        invites_data["used_invites"][code] = invite_data
        del invites_data["invites"][code]
    
    if expired_codes:
        save_invites_data(invites_data)
    
    return len(expired_codes)

def get_invite_stats(admin_id=None):
    """
    Получить статистику приглашений
    :param admin_id: ID администратора (если указан, только его статистика)
    :return: dict со статистикой
    """
    invites_data = load_invites_data()
    
    total_created = 0
    active_invites = 0
    used_invites = 0
    expired_invites = 0
    
    now = datetime.now()
    
    # Считаем активные приглашения
    for code, invite_data in invites_data["invites"].items():
        if admin_id and invite_data["admin_id"] != admin_id:
            continue
            
        total_created += 1
        
        if invite_data["used"]:
            continue
            
        expires_at = datetime.fromisoformat(invite_data["expires_at"])
        if now > expires_at:
            expired_invites += 1
        else:
            active_invites += 1
    
    # Считаем использованные приглашения
    for code, invite_data in invites_data["used_invites"].items():
        if admin_id and invite_data["admin_id"] != admin_id:
            continue
            
        if not invite_data.get("used"):
            total_created += 1
            
        if invite_data.get("expired"):
            expired_invites += 1
        else:
            used_invites += 1
    
    return {
        "total_created": total_created,
        "active_invites": active_invites,
        "used_invites": used_invites,
        "expired_invites": expired_invites
    }

def parse_invite_from_start_command(start_param):
    """
    Извлечь код приглашения из параметра команды /start
    :param start_param: Параметр команды start
    :return: код приглашения или None
    """
    if start_param and start_param.startswith("invite_"):
        return start_param[7:]  # Убираем префикс "invite_"
    return None