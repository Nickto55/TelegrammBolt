#!/usr/bin/env python3
"""
TelegrammBolt Web Interface
Веб-интерфейс для бота с авторизацией через Telegram
"""

import os
import hashlib
import hmac
import json
import logging
import traceback
import sys
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import parse_qs

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Импорты из существующих модулей бота
from config.config import BOT_TOKEN, BOT_USERNAME, PROBLEM_TYPES, RC_TYPES, DATA_FILE, load_data, save_data
from bot.user_manager import (
    has_permission, 
    get_users_data, 
    get_user_data,
    get_user_role, 
    register_user,
    is_user_registered,
    set_user_role,
    ROLES
)
from bot.dse_manager import get_all_dse_records, get_dse_records_by_user, search_dse_records
# chat_manager не имеет нужных функций для веб, используем свои реализации
from bot.pdf_generator import create_dse_pdf_report
# Новые модули для QR кодов и привязки аккаунтов
from bot.invite_manager import (
    create_invite, generate_qr_code, get_active_invites, get_used_invites, 
    get_invite_stats, delete_invite, cleanup_expired_invites
)
from bot.account_linking import (
    create_web_user, find_web_user_by_email, generate_linking_code_for_web_user,
    authenticate_web_user, get_linking_stats, get_all_web_users
)
import pandas as pd

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определяем пути для Flask (относительно файла web_app.py)
web_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(web_dir, 'templates')
static_dir = os.path.join(web_dir, 'static')

# Инициализация Flask
app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir)

# Используем SECRET_KEY из config (постоянный ключ для всех workers)
from config.config import SECRET_KEY
app.secret_key = SECRET_KEY

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SESSION_COOKIE_SECURE'] = True  # Установите True если используете HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# CORS для API
CORS(app)

# Инициализация SocketIO для веб-терминала
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Импортируем менеджер терминалов
from web.terminal_manager import terminal_manager

# Добавляем функцию now() в Jinja2 для использования в шаблонах
app.jinja_env.globals['now'] = datetime.now

# ============================================================================
# ФУНКЦИИ-ОБЕРТКИ ДЛЯ СОВМЕСТИМОСТИ
# ============================================================================

def get_all_dse():
    """Обертка для получения всех ДСЕ"""
    return get_all_dse_records()


def get_dse_by_id(dse_id):
    """Получить конкретное ДСЕ по ID (фильтрация из всех записей)"""
    try:
        records = get_all_dse_records()
        if not records:
            logger.warning("get_all_dse_records() returned empty list")
            return None
            
        for record in records:
            # Проверяем оба поля: id и dse
            record_id = str(record.get('id', ''))
            record_dse = str(record.get('dse', ''))
            search_id = str(dse_id)
            
            if record_id == search_id or record_dse == search_id:
                logger.info(f"Found DSE: {record_dse} (id: {record_id})")
                return record
        
        logger.warning(f"DSE not found: {dse_id}")
        return None
    except Exception as e:
        logger.error(f"Error in get_dse_by_id({dse_id}): {e}")
        import traceback
        traceback.print_exc()
        return None


def add_dse(data):
    """Добавление нового ДСЕ"""
    try:
        from config.config import load_data, save_data, DATA_FILE
        from datetime import datetime
        
        # Получаем user_id из сессии
        user_id = session.get('user_id', 'web')
        
        # Создаем запись
        record = {
            'dse': data.get('dse', ''),
            'problem_type': data.get('problem_type', ''),
            'rc': data.get('rc', ''),
            'description': data.get('description', ''),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': str(user_id),
            'photo_file_id': None
        }
        
        # Загружаем данные
        data_dict = load_data(DATA_FILE)
        if str(user_id) not in data_dict:
            data_dict[str(user_id)] = []
        
        # Добавляем запись
        data_dict[str(user_id)].append(record)
        
        # Сохраняем
        save_data(data_dict, DATA_FILE)
        
        logger.info(f"DSE added: {record['dse']} by user {user_id}")
        return {"success": True, "message": "ДСЕ успешно добавлен"}
    except Exception as e:
        logger.error(f"Error in add_dse: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def update_dse(dse_id, data):
    """Обновление ДСЕ"""
    try:
        from config.config import load_data, save_data, DATA_FILE
        
        # Загружаем данные
        data_dict = load_data(DATA_FILE)
        
        # Ищем и обновляем запись
        found = False
        for user_id in data_dict:
            for i, record in enumerate(data_dict[user_id]):
                if str(record.get('dse', '')) == str(dse_id) or str(i) == str(dse_id):
                    # Обновляем поля
                    if 'dse' in data:
                        record['dse'] = data['dse']
                    if 'problem_type' in data:
                        record['problem_type'] = data['problem_type']
                    if 'rc' in data:
                        record['rc'] = data['rc']
                    if 'description' in data:
                        record['description'] = data['description']
                    
                    data_dict[user_id][i] = record
                    found = True
                    break
            if found:
                break
        
        if not found:
            return {"success": False, "error": "ДСЕ не найден"}
        
        # Сохраняем
        save_data(data_dict, DATA_FILE)
        
        logger.info(f"DSE updated: {dse_id}")
        return {"success": True, "message": "ДСЕ успешно обновлен"}
    except Exception as e:
        logger.error(f"Error in update_dse: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def delete_dse(dse_id):
    """Удаление ДСЕ"""
    try:
        from config.config import load_data, save_data, DATA_FILE
        
        # Загружаем данные
        data_dict = load_data(DATA_FILE)
        
        # Ищем и удаляем запись
        found = False
        for user_id in data_dict:
            for i, record in enumerate(data_dict[user_id]):
                if str(record.get('dse', '')) == str(dse_id) or str(i) == str(dse_id):
                    del data_dict[user_id][i]
                    found = True
                    break
            if found:
                break
        
        if not found:
            return {"success": False, "error": "ДСЕ не найден"}
        
        # Сохраняем
        save_data(data_dict, DATA_FILE)
        
        logger.info(f"DSE deleted: {dse_id}")
        return {"success": True, "message": "ДСЕ успешно удален"}
    except Exception as e:
        logger.error(f"Error in delete_dse: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def get_chat_history(user_id):
    """Заглушка для получения истории чата - требует реализации"""
    # TODO: реализовать получение истории из chat_manager или отдельного файла
    logger.warning("get_chat_history() not fully implemented")
    return []


def send_chat_message(user_id, target_user_id, message):
    """Заглушка для отправки сообщения - требует реализации"""
    # TODO: реализовать отправку через бота
    logger.warning("send_chat_message() not fully implemented")
    return {"success": False, "error": "Функция в разработке"}


def generate_pdf_report(options):
    """Генерация PDF отчета с новыми опциями"""
    import tempfile
    import zipfile
    from telegram import Bot
    import asyncio
    
    dse_numbers = options.get('dse_numbers', [])
    mode = options.get('mode', 'single')
    include_photos = options.get('include_photos', True)
    include_description = options.get('include_description', True)
    include_user_info = options.get('include_user_info', True)
    include_timestamp = options.get('include_timestamp', True)
    page_format = options.get('page_format', 'A4')
    page_orientation = options.get('page_orientation', 'portrait')
    
    # Получаем записи по номерам ДСЕ
    all_records = get_all_dse()
    selected_records = [r for r in all_records if r.get('dse') in dse_numbers]
    
    if not selected_records:
        raise ValueError("Не найдены записи с указанными номерами ДСЕ")
    
    logger.info(f"Generating PDF for {len(selected_records)} records in mode: {mode}")
    
    if mode == 'single':
        # Один PDF файл со всеми ДСЕ
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        try:
            # Создаем PDF с множественными записями
            from bot.pdf_generator import create_multi_dse_pdf_report
            success = create_multi_dse_pdf_report(
                selected_records, 
                temp_file.name,
                options={
                    'include_photos': include_photos,
                    'include_description': include_description,
                    'include_user_info': include_user_info,
                    'include_timestamp': include_timestamp,
                    'page_format': page_format,
                    'page_orientation': page_orientation,
                    'bot_token': BOT_TOKEN if include_photos else None
                }
            )
            
            if not success:
                raise Exception("Ошибка создания PDF файла")
            
            # Проверяем что файл существует и не пустой
            if not os.path.exists(temp_file.name) or os.path.getsize(temp_file.name) == 0:
                raise Exception("PDF файл пустой или не создан")
            
            logger.info(f"PDF created successfully: {temp_file.name}, size: {os.path.getsize(temp_file.name)} bytes")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            # Удаляем поврежденный файл
            try:
                if os.path.exists(temp_file.name):
                    os.remove(temp_file.name)
            except:
                pass
            raise
    
    else:
        # Множественные PDF файлы в ZIP архиве
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        try:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i, record in enumerate(selected_records):
                    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    temp_pdf.close()
                    
                    try:
                        # Создаем PDF для каждой записи
                        from bot.pdf_generator import create_single_dse_pdf_report
                        success = create_single_dse_pdf_report(
                            record,
                            temp_pdf.name,
                            options={
                                'include_photos': include_photos,
                                'include_description': include_description,
                                'include_user_info': include_user_info,
                                'include_timestamp': include_timestamp,
                                'page_format': page_format,
                                'page_orientation': page_orientation,
                                'bot_token': BOT_TOKEN if include_photos else None
                            }
                        )
                        
                        if success and os.path.exists(temp_pdf.name):
                            # Добавляем в ZIP
                            dse_safe = str(record.get('dse', f'dse_{i}')).replace('/', '_').replace('\\', '_')
                            zipf.write(temp_pdf.name, f'DSE_{dse_safe}.pdf')
                            logger.info(f"Added to ZIP: DSE_{dse_safe}.pdf")
                        
                    finally:
                        # Удаляем временный PDF
                        try:
                            if os.path.exists(temp_pdf.name):
                                os.remove(temp_pdf.name)
                        except:
                            pass
            
            # Проверяем что ZIP создан
            if not os.path.exists(temp_zip.name) or os.path.getsize(temp_zip.name) == 0:
                raise Exception("ZIP архив пустой или не создан")
            
            logger.info(f"ZIP created successfully: {temp_zip.name}, size: {os.path.getsize(temp_zip.name)} bytes")
            return temp_zip.name
            
        except Exception as e:
            logger.error(f"Error creating ZIP: {e}")
            # Удаляем поврежденный файл
            try:
                if os.path.exists(temp_zip.name):
                    os.remove(temp_zip.name)
            except:
                pass
            raise


def save_users_data(users_data):
    """Сохранение данных пользователей"""
    from config.config import USERS_FILE
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)


def load_permissions_log():
    """Загрузка истории изменений прав"""
    log_file = 'permissions_log.json'
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def log_permission_change(admin_id, target_user_id, old_role, new_role, old_permissions, new_permissions):
    """Логирование изменения прав пользователя"""
    log_file = 'permissions_log.json'
    
    # Загрузка существующих логов
    logs = load_permissions_log()
    
    # Получение имён пользователей
    users = get_users_data()
    admin_name = users.get(admin_id, {}).get('first_name', f'ID: {admin_id}')
    target_name = users.get(target_user_id, {}).get('first_name', f'ID: {target_user_id}')
    
    # Создание записи лога
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'admin_id': admin_id,
        'admin_name': admin_name,
        'target_user_id': target_user_id,
        'target_name': target_name,
        'changes': {
            'role': {
                'old': old_role,
                'new': new_role
            },
            'permissions': {
                'old': old_permissions,
                'new': new_permissions
            }
        }
    }
    
    # Добавление в начало списка (новые записи сверху)
    logs.insert(0, log_entry)
    
    # Ограничение размера лога (хранить последние 1000 записей)
    logs = logs[:1000]
    
    # Сохранение
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Права изменены: {admin_name} изменил роль {target_name} с {old_role} на {new_role}")


def load_email_subscriptions():
    """Загрузка подписок на email из subscription_manager"""
    from bot.subscription_manager import load_subscriptions
    
    subscriptions = load_subscriptions()
    # Конвертируем формат для обратной совместимости
    result = {}
    for user_id, data in subscriptions.items():
        if data.get('active') and data.get('delivery_type') in ['email', 'both']:
            result[user_id] = {
                'enabled': True,
                'email': data.get('email', ''),
                'updated_at': data.get('created_at', '')
            }
    return result


def save_email_subscription(user_id, enabled, email):
    """Сохранение подписки на email через subscription_manager"""
    from bot.subscription_manager import add_subscription, remove_subscription
    
    if enabled:
        # Добавляем/обновляем подписку с типом 'email'
        success = add_subscription(user_id, delivery_type='email', email=email)
        if success:
            logger.info(f"Email подписка включена для пользователя {user_id}: email={email}")
        else:
            logger.error(f"Ошибка включения email подписки для пользователя {user_id}")
    else:
        # Удаляем подписку
        success = remove_subscription(user_id)
        if success:
            logger.info(f"Email подписка отключена для пользователя {user_id}")
        else:
            logger.info(f"Подписка для пользователя {user_id} не найдена или уже отключена")


# ============================================================================
# УТИЛИТЫ ДЛЯ TELEGRAM LOGIN
# ============================================================================

def verify_telegram_auth(auth_data):
    """
    Проверка подлинности данных от Telegram Login Widget
    https://core.telegram.org/widgets/login#checking-authorization
    """
    check_hash = auth_data.get('hash')
    if not check_hash:
        return False
    
    auth_data_copy = {k: v for k, v in auth_data.items() if k != 'hash'}
    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted(auth_data_copy.items())])
    
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if calculated_hash != check_hash:
        return False
    
    # Проверка времени авторизации (не старше 1 дня)
    auth_date = int(auth_data.get('auth_date', 0))
    if datetime.now().timestamp() - auth_date > 86400:
        return False
    
    return True


def login_required(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"login_required check: session keys = {list(session.keys())}")
        if 'user_id' not in session:
            logger.warning(f"No user_id in session, redirecting to login")
            return redirect(url_for('login'))
        logger.info(f"login_required passed: user_id = {session.get('user_id')}")
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        if not has_permission(user_id, 'admin'):
            return jsonify({'error': 'Доступ запрещен'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def user_role_required(allowed_roles):
    """Декоратор для проверки ролей пользователей"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user_role = session.get('user_role', get_user_role(session['user_id']))
            
            if user_role not in allowed_roles:
                # Пользователи с ролью 'user' перенаправляются на сканирование QR
                if user_role == 'user':
                    return redirect(url_for('scan_invite_page'))
                else:
                    flash('У вас недостаточно прав для доступа к этой странице.', 'error')
                    return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# МАРШРУТЫ - АВТОРИЗАЦИЯ
# ============================================================================

@app.route('/')
def index():
    """Главная страница"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    """Страница входа через Telegram"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html', bot_username=get_bot_username())


@app.route('/auth/telegram', methods=['POST'])
def telegram_auth():
    """Обработка авторизации через Telegram"""
    try:
        auth_data = request.json
        
        # Проверка подлинности данных
        if not verify_telegram_auth(auth_data):
            return jsonify({'error': 'Неверные данные авторизации'}), 401
        
        user_id = str(auth_data['id'])
        
        # Проверка регистрации пользователя в боте
        users_data = get_users_data()
        if user_id not in users_data:
            # Автоматическая регистрация пользователя
            register_user(
                user_id,
                auth_data.get('username', ''),
                auth_data.get('first_name', ''),
                auth_data.get('last_name', '')
            )
        
        # Проверяем роль пользователя
        user_role = get_user_role(user_id)
        if user_role == 'user':
            return jsonify({
                'error': 'Доступ запрещён. У вас базовая роль. Обратитесь к администратору для получения прав доступа.'
            }), 403
        
        # Сохранение данных в сессию
        session.permanent = True
        session['user_id'] = user_id
        session['user_role'] = user_role
        session['first_name'] = auth_data.get('first_name', '')
        session['last_name'] = auth_data.get('last_name', '')
        session['username'] = auth_data.get('username', '')
        session['photo_url'] = auth_data.get('photo_url', '')
        
        logger.info(f"User {user_id} logged in via Telegram")
        
        redirect_url = url_for('dashboard')
        logger.info(f"Redirecting to: {redirect_url}")
        
        return jsonify({
            'success': True,
            'redirect': redirect_url
        })
    
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return jsonify({'error': 'Ошибка авторизации'}), 500


@app.route('/auth/admin', methods=['POST'])
def admin_auth():
    """Обработка авторизации администратора через логин/пароль"""
    try:
        auth_data = request.json
        username = auth_data.get('username', '').strip()
        password = auth_data.get('password', '').strip()
        
        # Загружаем админ-креды из config
        import config.config as config
        admin_credentials = getattr(config, 'ADMIN_CREDENTIALS', {})
        
        # Проверка логина/пароля
        if username in admin_credentials and admin_credentials[username] == hashlib.sha256(password.encode()).hexdigest():
            # Получаем user_id админа из конфига или создаём специальный
            admin_user_id = admin_credentials.get(f'{username}_user_id', f'admin_{username}')
            
            # Проверяем, что пользователь зарегистрирован и является админом
            users_data = get_users_data()
            if admin_user_id not in users_data:
                # Регистрируем админа если его нет
                register_user(admin_user_id, username, 'Администратор', '')
                # Устанавливаем роль admin
                from bot.user_manager import set_user_role
                set_user_role(admin_user_id, 'admin')
            else:
                # Пользователь существует - убедимся что у него роль admin
                from bot.user_manager import set_user_role
                set_user_role(admin_user_id, 'admin')
            
            # Сохранение данных в сессию (не проверяем get_user_role, т.к. только что установили)
            session.permanent = True
            session['user_id'] = admin_user_id
            session['user_role'] = 'admin'
            session['first_name'] = 'Администратор'
            session['last_name'] = ''
            session['username'] = username
            session['photo_url'] = ''
            session['auth_type'] = 'admin'  # Помечаем тип авторизации
            
            logger.info(f"Admin {username} logged in via credentials")
            
            redirect_url = url_for('dashboard')
            logger.info(f"Redirecting to: {redirect_url}")
            
            return jsonify({
                'success': True,
                'redirect': redirect_url
            })
        else:
            return jsonify({'error': 'Неверный логин или пароль'}), 401
    
    except Exception as e:
        logger.error(f"Admin auth error: {e}")
        return jsonify({'error': 'Ошибка авторизации'}), 500


@app.route('/auth/qr', methods=['POST'])
def qr_auth():
    """Обработка авторизации через QR код приглашения"""
    try:
        auth_data = request.json
        invite_code = auth_data.get('invite_code', '').strip().upper()
        
        if not invite_code:
            return jsonify({'error': 'Код приглашения не указан'}), 400
        
        # Проверяем и используем приглашение
        from bot.invite_manager import use_invite, get_invite_info
        
        # Сначала проверяем, существует ли приглашение
        invite_info = get_invite_info(invite_code)
        if not invite_info:
            return jsonify({'error': 'Неверный код приглашения'}), 404
        
        if invite_info.get('used'):
            return jsonify({'error': 'Код приглашения уже использован'}), 400
        
        # Генерируем временный user_id для веб-пользователя
        import uuid
        temp_user_id = f'web_{uuid.uuid4().hex[:8]}'
        
        # Используем приглашение
        result = use_invite(
            invite_code,
            temp_user_id,
            username='',
            first_name='Веб-пользователь',
            last_name=''
        )
        
        if not result.get('success'):
            return jsonify({'error': result.get('message', 'Ошибка активации приглашения')}), 400
        
        # Регистрируем пользователя
        register_user(temp_user_id, '', 'Веб-пользователь', '')
        
        # Устанавливаем роль из приглашения
        from bot.user_manager import set_user_role
        assigned_role = result.get('role', 'user')  # Роль из приглашения
        set_user_role(temp_user_id, assigned_role)
        
        # Сохранение данных в сессию
        session.permanent = True
        session['user_id'] = temp_user_id
        session['user_role'] = assigned_role  # Роль из приглашения
        session['first_name'] = 'Веб-пользователь'
        session['last_name'] = ''
        session['username'] = ''
        session['photo_url'] = ''
        session['auth_type'] = 'qr'
        session['telegram_linked'] = False  # Telegram не подключен
        
        logger.info(f"User {temp_user_id} logged in via QR code: {invite_code}")
        
        redirect_url = url_for('dashboard')
        
        return jsonify({
            'success': True,
            'redirect': redirect_url,
            'message': 'Вход выполнен. Для получения полных прав подключите Telegram аккаунт.'
        })
    
    except Exception as e:
        logger.error(f"QR auth error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка авторизации через QR код'}), 500


@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return redirect(url_for('login'))


# ============================================================================
# МАРШРУТЫ - ОСНОВНЫЕ СТРАНИЦЫ
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Главная панель управления"""
    try:
        user_id = session['user_id']
        user_role = session.get('user_role', get_user_role(user_id))
        logger.info(f"Dashboard access by user_id: {user_id}, role: {user_role}")
        
        # Получаем данные пользователя из сессии и user_manager
        users_data = get_users_data()
        user_data = users_data.get(user_id, {
            'username': session.get('username', ''),
            'first_name': session.get('first_name', ''),
            'last_name': session.get('last_name', ''),
            'role': get_user_role(user_id)
        })
        
        # Статистика
        dse_data = get_all_dse()
        
        # Подсчёт активных пользователей
        active_users = len([u for u in users_data.values() if u.get('role') != 'banned'])
        
        # Подсчёт записей по типам проблем
        problem_types = {}
        for record in dse_data:
            problem_type = record.get('problem_type', 'Неизвестно')
            problem_types[problem_type] = problem_types.get(problem_type, 0) + 1
        
        # Подсчёт записей за последние 7 дней
        from datetime import datetime, timedelta
        recent_date = datetime.now() - timedelta(days=7)
        recent_dse = 0
        for record in dse_data:
            try:
                record_date = datetime.strptime(record.get('datetime', ''), '%Y-%m-%d %H:%M:%S')
                if record_date >= recent_date:
                    recent_dse += 1
            except:
                pass
        
        # Безопасное определение top_problem_type
        top_problem_type = 'Нет данных'
        if problem_types:
            try:
                top_problem_type = max(problem_types.items(), key=lambda x: x[1])[0]
            except:
                pass
        
        stats = {
            'total_dse': len(dse_data),
            'active_users': active_users,
            'recent_dse': recent_dse,
            'problem_types': problem_types,
            'top_problem_type': top_problem_type
        }
        
        return render_template('dashboard.html', 
                             user=user_data,
                             stats=stats,
                             permissions=get_user_permissions(user_id),
                             bot_username=get_bot_username())
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        # Возвращаем простую страницу с ошибкой вместо редиректа
        return f"<h1>Ошибка загрузки панели</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>", 500


@app.route('/profile')
@login_required
def profile():
    """Профиль пользователя"""
    user_id = session['user_id']
    user_data = get_user_data(user_id)
    
    # Загрузка настроек подписок
    subscriptions = load_email_subscriptions()
    user_subscription = subscriptions.get(user_id, {})
    
    return render_template('profile.html', 
                         user=user_data,
                         subscription=user_subscription)


@app.route('/change-password')
@login_required
def change_password_page():
    """Страница смены/создания пароля"""
    # Проверяем роль - пользователи с role='user' не должны иметь доступ
    from bot.user_manager import get_user_role
    user_role = get_user_role(session['user_id'])
    
    if user_role == 'user':
        flash('Доступ запрещён. Обратитесь к администратору.', 'error')
        return redirect(url_for('logout'))
    
    # Проверяем есть ли уже веб-аккаунт
    from bot.account_linking import get_web_user_by_telegram_id
    web_user_id, web_user_data = get_web_user_by_telegram_id(session['user_id'])
    
    has_password = bool(web_user_id and web_user_data and web_user_data.get('password_hash'))
    current_username = web_user_data.get('email', '') if web_user_data else ''
    
    return render_template('change_password.html', 
                         has_password=has_password,
                         current_username=current_username)


@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def api_change_password():
    """API: Смена/создание пароля пользователя"""
    from bot.user_manager import get_user_role
    from bot.account_linking import get_web_user_by_telegram_id, create_or_update_web_credentials
    import hashlib
    
    # Проверяем роль
    user_role = get_user_role(session['user_id'])
    if user_role == 'user':
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    data = request.json
    username = data.get('username', '').strip()
    current_password = data.get('currentPassword', '')
    new_password = data.get('newPassword', '')
    
    if not username or not new_password:
        return jsonify({'error': 'Необходимо указать логин и новый пароль'}), 400
    
    # Проверяем существующий веб-аккаунт
    web_user_id, web_user_data = get_web_user_by_telegram_id(session['user_id'])
    
    # Если есть веб-аккаунт с паролем, проверяем старый пароль
    if web_user_data and web_user_data.get('password_hash'):
        if not current_password:
            return jsonify({'error': 'Необходимо указать текущий пароль'}), 400
        
        current_hash = hashlib.sha256(current_password.encode()).hexdigest()
        if web_user_data['password_hash'] != current_hash:
            return jsonify({'error': 'Неверный текущий пароль'}), 400
    
    # Создаём/обновляем креды
    new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    result = create_or_update_web_credentials(
        session['user_id'],
        username,
        new_password_hash
    )
    
    if result['success']:
        return jsonify({'success': True, 'message': result['message']})
    else:
        return jsonify({'success': False, 'error': result['error']}), 400


@app.route('/api/profile/email-subscription', methods=['POST'])
@login_required
def update_email_subscription():
    """API: Обновление email-подписки"""
    user_id = session['user_id']
    
    # Проверка прав администратора
    if get_user_role(user_id) != 'admin':
        return jsonify({'error': 'Только администраторы могут подписаться на рассылку'}), 403
    
    data = request.json
    enabled = data.get('enabled', False)
    email = data.get('email', '').strip()
    
    if enabled and not email:
        return jsonify({'error': 'Необходимо указать email адрес'}), 400
    
    if enabled and '@' not in email:
        return jsonify({'error': 'Некорректный email адрес'}), 400
    
    # Сохранение подписки
    save_email_subscription(user_id, enabled, email)
    
    return jsonify({'success': True, 'message': 'Настройки подписки обновлены'})


@app.route('/users')
@login_required
@user_role_required(['admin'])
def users_management():
    """Управление пользователями (только для админов)"""
    user_id = session['user_id']
    
    # Проверка прав администратора
    if get_user_role(user_id) != 'admin':
        return "Доступ запрещен. Только для администраторов.", 403
    
    users = get_users_data()
    
    # Загрузка истории изменений прав
    permissions_log = load_permissions_log()
    
    return render_template('users_management.html', 
                         users=users,
                         roles=ROLES,
                         permissions_log=permissions_log)


@app.route('/api/users/<user_id>/permissions', methods=['POST'])
@login_required
def update_user_permissions(user_id):
    """API: Обновление прав пользователя"""
    admin_id = session['user_id']
    
    # Проверка прав администратора
    if get_user_role(admin_id) != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    new_role = data.get('role')
    new_permissions = data.get('permissions', [])
    
    if not new_role or new_role not in ROLES:
        return jsonify({'error': 'Некорректная роль'}), 400
    
    # Проверяем, является ли пользователь веб-пользователем без Telegram
    users = get_users_data()
    target_user = users.get(user_id, {})
    
    # Если user_id начинается с 'web_' - это пользователь, вошедший через QR код
    if user_id.startswith('web_'):
        # Проверяем, подключен ли Telegram
        # Если нет подключенного Telegram аккаунта, ограничиваем роли initiator/responder
        allowed_web_roles = ['user', 'initiator', 'responder']
        if new_role not in allowed_web_roles:
            return jsonify({
                'error': 'Невозможно назначить роль администратора пользователю без подключенного Telegram аккаунта. '
                         'Доступные роли: Инициатор, Ответчик. Для роли администратора требуется подключение Telegram.'
            }), 400
    
    # Получение старых данных для логирования
    old_role = target_user.get('role', 'user')
    old_permissions = target_user.get('permissions', [])
    
    # Обновление роли
    set_user_role(user_id, new_role)
    
    # Обновление кастомных прав (если требуется)
    users = get_users_data()
    if user_id in users:
        users[user_id]['permissions'] = new_permissions
        save_users_data(users)
    
    # Логирование изменений
    log_permission_change(
        admin_id=admin_id,
        target_user_id=user_id,
        old_role=old_role,
        new_role=new_role,
        old_permissions=old_permissions,
        new_permissions=new_permissions
    )
    
    return jsonify({'success': True, 'message': 'Права обновлены'})


@app.route('/api/users/<user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """API: Удаление пользователя"""
    admin_id = session['user_id']
    
    # Проверка прав администратора
    if get_user_role(admin_id) != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    # Нельзя удалить самого себя
    if str(admin_id) == str(user_id):
        return jsonify({'error': 'Нельзя удалить самого себя'}), 400
    
    try:
        users = get_users_data()
        
        if user_id not in users:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Сохраняем информацию для логирования
        deleted_user_info = users[user_id]
        
        # Удаляем пользователя
        del users[user_id]
        save_users_data(users)
        
        # Логируем удаление
        log_permission_change(
            admin_id=admin_id,
            target_user_id=user_id,
            old_role=deleted_user_info.get('role', 'user'),
            new_role='deleted',
            old_permissions=deleted_user_info.get('permissions', []),
            new_permissions=[]
        )
        
        logger.info(f"Admin {admin_id} deleted user {user_id}")
        return jsonify({'success': True, 'message': 'Пользователь удален'})
        
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({'error': f'Ошибка удаления: {str(e)}'}), 500


@app.route('/api/users/<user_id>/credentials', methods=['PUT'])
@login_required
def update_user_credentials(user_id):
    """API: Обновление учетных данных пользователя (только для админов)"""
    admin_id = session['user_id']
    
    # Проверка прав администратора
    if get_user_role(admin_id) != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    new_email = data.get('email')
    new_password = data.get('password')
    
    # Получаем веб-пользователя по Telegram ID
    from bot.account_linking import get_web_user_by_telegram_id, admin_update_email, admin_change_password
    web_user_id, web_user_data = get_web_user_by_telegram_id(user_id)
    
    if not web_user_id:
        return jsonify({'error': 'У пользователя нет веб-аккаунта'}), 404
    
    try:
        changes_made = []
        
        # Обновление email если указан
        if new_email:
            email_result = admin_update_email(web_user_id, new_email)
            if not email_result['success']:
                return jsonify({'error': email_result['error']}), 400
            changes_made.append(f"email изменен на {new_email}")
        
        # Обновление пароля если указан
        if new_password:
            import hashlib
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            password_result = admin_change_password(web_user_id, password_hash)
            if not password_result['success']:
                return jsonify({'error': password_result['error']}), 400
            changes_made.append("пароль изменен")
        
        if not changes_made:
            return jsonify({'error': 'Нет данных для обновления'}), 400
        
        # Логируем изменение учетных данных
        log_permission_change(
            admin_id=admin_id,
            target_user_id=user_id,
            old_role=get_user_role(user_id),  # Не изменяем роль
            new_role=get_user_role(user_id),
            old_permissions=[],  # Не изменяем права
            new_permissions=[f"credentials_updated: {', '.join(changes_made)}"]
        )
        
        logger.info(f"Admin {admin_id} updated credentials for user {user_id}: {', '.join(changes_made)}")
        return jsonify({'success': True, 'message': f'Учетные данные обновлены: {", ".join(changes_made)}'})
        
    except Exception as e:
        logger.error(f"Error updating credentials for user {user_id}: {e}")
        return jsonify({'error': f'Ошибка обновления учетных данных: {str(e)}'}), 500


@app.route('/api/users/<user_id>/credentials/info', methods=['GET'])
@login_required
def get_user_credentials_info(user_id):
    """API: Получение информации об учетных данных пользователя (только для админов)"""
    admin_id = session['user_id']
    
    # Проверка прав администратора
    if get_user_role(admin_id) != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    try:
        # Получаем веб-пользователя по Telegram ID
        from bot.account_linking import get_web_user_by_telegram_id
        web_user_id, web_user_data = get_web_user_by_telegram_id(user_id)
        
        if not web_user_id:
            return jsonify({'success': False, 'error': 'У пользователя нет веб-аккаунта'}), 404
        
        return jsonify({
            'success': True,
            'web_user_id': web_user_id,
            'email': web_user_data.get('email', ''),
            'first_name': web_user_data.get('first_name', ''),
            'last_name': web_user_data.get('last_name', ''),
            'role': web_user_data.get('role', 'initiator')
        })
        
    except Exception as e:
        logger.error(f"Error getting credentials info for user {user_id}: {e}")
        return jsonify({'error': f'Ошибка получения информации об учетных данных: {str(e)}'}), 500


@app.route('/api/users/credentials/create', methods=['POST'])
@login_required
def create_user_credentials():
    """API: Создание учетных данных для пользователя (только для админов)"""
    admin_id = session['user_id']
    
    # Проверка прав администратора
    if get_user_role(admin_id) != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    telegram_user_id = data.get('telegram_user_id')  # Опционально - для привязки к существующему Telegram аккаунту
    role = data.get('role', 'initiator')
    
    if not email or not password or not first_name:
        return jsonify({'error': 'Заполните обязательные поля: email, пароль, имя'}), 400
    
    try:
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Создаем веб-пользователя
        from bot.account_linking import admin_create_web_user, get_all_web_users
        web_user_id = admin_create_web_user(email, password_hash, first_name, last_name, role)
        
        if not web_user_id:
            return jsonify({'error': 'Email уже используется другим пользователем'}), 400
        
        # Если указан Telegram ID, привязываем к нему
        if telegram_user_id:
            from bot.account_linking import load_linking_data, save_linking_data
            linking_data = load_linking_data()
            linking_data["web_users"][web_user_id]["telegram_id"] = telegram_user_id
            
            # Также обновляем роль в основной системе пользователей
            from bot.user_manager import set_user_role
            set_user_role(telegram_user_id, role)
            
            save_linking_data(linking_data)
        
        logger.info(f"Admin {admin_id} created web user {web_user_id} with email {email}")
        return jsonify({
            'success': True, 
            'message': 'Веб-аккаунт создан успешно',
            'web_user_id': web_user_id
        })
        
    except Exception as e:
        logger.error(f"Error creating web user: {e}")
        return jsonify({'error': f'Ошибка создания веб-аккаунта: {str(e)}'}), 500


@app.route('/dse')
@login_required
@user_role_required(['admin', 'responder', 'initiator'])
def dse_list():
    """Список всех ДСЕ"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'view_dse'):
        return "Доступ запрещен", 403
    
    try:
        dse_data = get_all_dse()
        if not dse_data:
            logger.info("No DSE data found, showing empty list")
            dse_data = []
    except Exception as e:
        logger.error(f"Error loading DSE data: {e}")
        dse_data = []
        flash("Ошибка загрузки данных. Возможно, бот ещё не запускался.", "warning")
    
    return render_template('dse_list.html', 
                         dse_data=dse_data,
                         permissions=get_user_permissions(user_id))


@app.route('/dse/<dse_id>')
@login_required
def dse_detail(dse_id):
    """Детальная информация о ДСЕ"""
    try:
        user_id = session['user_id']
        logger.info(f"User {user_id} trying to access DSE: {dse_id}")
        
        if not has_permission(user_id, 'view_dse'):
            logger.warning(f"User {user_id} has no permission to view DSE")
            return "Доступ запрещен", 403
        
        dse = get_dse_by_id(dse_id)
        if not dse:
            logger.warning(f"DSE not found: {dse_id}")
            return render_template('error.html', 
                                 error="Заявка не найдена",
                                 message=f"Заявка с ID '{dse_id}' не существует или была удалена."), 404
        
        logger.info(f"DSE found: {dse.get('dse', 'N/A')}, user_id: {dse.get('user_id', 'N/A')}")
        
        # Получить информацию о пользователе, создавшем ДСЕ
        user_info = None
        if dse.get('user_id'):
            try:
                user_info = get_user_data(str(dse['user_id']))
                logger.info(f"User info loaded: {user_info.get('name', 'N/A') if user_info else 'None'}")
            except Exception as e:
                logger.warning(f"Не удалось получить информацию о пользователе {dse.get('user_id')}: {e}")
                user_info = None
        
        logger.info(f"Rendering dse_detail.html for DSE: {dse_id}")
        return render_template('dse_detail.html', 
                             dse=dse, 
                             user_info=user_info,
                             permissions=get_user_permissions(user_id))
    
    except Exception as e:
        logger.error(f"Ошибка при открытии ДСЕ {dse_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return render_template('error.html',
                             error="Ошибка загрузки заявки",
                             message=f"Не удалось загрузить заявку. Попробуйте обновить страницу."), 500


@app.route('/dse/create', methods=['GET', 'POST'])
@login_required
def create_dse():
    """Создание новой заявки ДСЕ"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'add_dse'):
        return "Доступ запрещен. Требуется право на создание заявок.", 403
    
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            dse_number = request.form.get('dse_number', '').strip()
            problem_type = request.form.get('problem_type', '').strip()
            rc = request.form.get('rc', '').strip()
            description = request.form.get('description', '').strip()
            machine_number = request.form.get('machine_number', '').strip()
            installer_fio = request.form.get('installer_fio', '').strip()
            programmer_name = request.form.get('programmer_name', '').strip()
            
            # Валидация
            if not dse_number:
                return render_template('create_dse.html',
                                     error="Номер ДСЕ обязателен",
                                     problem_types=PROBLEM_TYPES,
                                     rc_types=RC_TYPES,
                                     permissions=get_user_permissions(user_id))
            
            if not problem_type or problem_type not in PROBLEM_TYPES:
                return render_template('create_dse.html',
                                     error="Выберите тип проблемы",
                                     problem_types=PROBLEM_TYPES,
                                     rc_types=RC_TYPES,
                                     permissions=get_user_permissions(user_id))
            
            if not machine_number:
                return render_template('create_dse.html',
                                     error="Номер станка обязателен",
                                     problem_types=PROBLEM_TYPES,
                                     rc_types=RC_TYPES,
                                     permissions=get_user_permissions(user_id))
            
            if not installer_fio:
                return render_template('create_dse.html',
                                     error="ФИО Наладчика обязательно",
                                     problem_types=PROBLEM_TYPES,
                                     rc_types=RC_TYPES,
                                     permissions=get_user_permissions(user_id))
            
            if not programmer_name:
                return render_template('create_dse.html',
                                     error="ФИО Программиста обязательно",
                                     problem_types=PROBLEM_TYPES,
                                     rc_types=RC_TYPES,
                                     permissions=get_user_permissions(user_id))
            
            # Создаем запись
            from datetime import datetime
            record = {
                'dse': dse_number,
                'problem_type': problem_type,
                'rc': rc,
                'description': description,
                'machine_number': machine_number,
                'installer_fio': installer_fio,
                'programmer_name': programmer_name,
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': user_id,
                'photo_file_id': None,
                'created_via': 'web'
            }
            
            # Загружаем данные
            data_dict = load_data(DATA_FILE)
            if user_id not in data_dict:
                data_dict[user_id] = []
            data_dict[user_id].append(record)
            
            # Сохраняем
            save_data(data_dict, DATA_FILE)
            
            logger.info(f"Создана новая заявка ДСЕ {dse_number} пользователем {user_id} через веб-интерфейс")
            
            # Перенаправляем на страницу просмотра
            flash('Заявка успешно создана!', 'success')
            return redirect(url_for('dse_list'))
            
        except Exception as e:
            logger.error(f"Ошибка создания заявки: {e}")
            return render_template('create_dse.html',
                                 error=f"Ошибка при создании заявки: {str(e)}",
                                 problem_types=PROBLEM_TYPES,
                                 rc_types=RC_TYPES,
                                 permissions=get_user_permissions(user_id))
    
    # GET запрос - показываем форму
    return render_template('create_dse.html',
                         problem_types=PROBLEM_TYPES,
                         rc_types=RC_TYPES,
                         permissions=get_user_permissions(user_id))


@app.route('/photo/<photo_id>')
@login_required
def get_photo(photo_id):
    """Получить фото по file_id из Telegram"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'view_dse'):
        return "Доступ запрещен", 403
    
    try:
        # Создаем директорию для временных фото если нет
        temp_dir = 'photos/temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        # Безопасное имя файла
        safe_filename = photo_id.replace('/', '_').replace('\\', '_')
        photo_path = f"{temp_dir}/{safe_filename}.jpg"
        
        # Если файл уже скачан, возвращаем его
        if os.path.exists(photo_path) and os.path.getsize(photo_path) > 0:
            logger.info(f"Returning cached photo: {photo_path}")
            return send_file(photo_path, mimetype='image/jpeg')
        
        # Скачиваем фото из Telegram
        logger.info(f"Downloading photo from Telegram: {photo_id}")
        
        from telegram.ext import Application
        import asyncio
        
        async def download_photo_async():
            """Асинхронная загрузка фото"""
            try:
                # Создаем приложение
                application = Application.builder().token(BOT_TOKEN).build()
                
                # Инициализируем бот
                await application.initialize()
                await application.bot.initialize()
                
                # Получаем файл
                file = await application.bot.get_file(photo_id)
                logger.info(f"File info: {file.file_path}")
                
                # Скачиваем файл
                await file.download_to_drive(photo_path)
                logger.info(f"Photo downloaded successfully to {photo_path}")
                
                # Завершаем работу бота
                await application.bot.shutdown()
                await application.shutdown()
                
                return photo_path
                
            except Exception as e:
                logger.error(f"Error in download_photo_async: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Создаем новый event loop для синхронного контекста
        try:
            # Пытаемся получить существующий loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
        except RuntimeError:
            # Создаем новый loop если текущий не существует или закрыт
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Запускаем загрузку
        try:
            loop.run_until_complete(download_photo_async())
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                # Если loop уже запущен, используем nest_asyncio
                import nest_asyncio
                nest_asyncio.apply()
                loop.run_until_complete(download_photo_async())
            else:
                raise
        
        # Проверяем что файл скачан
        if os.path.exists(photo_path) and os.path.getsize(photo_path) > 0:
            logger.info(f"Successfully downloaded photo, size: {os.path.getsize(photo_path)} bytes")
            return send_file(photo_path, mimetype='image/jpeg')
        else:
            logger.error(f"Photo file not found or empty after download: {photo_path}")
            raise Exception("Файл не был скачан или пустой")
        
    except Exception as e:
        logger.error(f"Ошибка загрузки фото {photo_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Возвращаем SVG-заглушку с сообщением об ошибке
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
    <rect width="400" height="300" fill="#f8f9fa"/>
    <rect x="10" y="10" width="380" height="280" fill="#e9ecef" stroke="#dee2e6" stroke-width="2"/>
    <text x="200" y="130" font-family="Arial, sans-serif" font-size="20" fill="#6c757d" text-anchor="middle">
        ⚠️ Ошибка загрузки фото
    </text>
    <text x="200" y="160" font-family="Arial, sans-serif" font-size="14" fill="#6c757d" text-anchor="middle">
        Фото временно недоступно
    </text>
    <text x="200" y="185" font-family="Arial, sans-serif" font-size="12" fill="#adb5bd" text-anchor="middle">
        Попробуйте обновить страницу
    </text>
</svg>'''
        from flask import Response
        return Response(svg_content, mimetype='image/svg+xml')


@app.route('/pdf-export')
@login_required
def pdf_export_page():
    """Страница выбора ДСЕ для экспорта в PDF"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'export_data'):
        return "Доступ запрещен", 403
    
    # Получаем все ДСЕ
    dse_data = get_all_dse()
    
    # Получаем уникальные типы проблем
    problem_types = sorted(list(set([d.get('problem_type', '') for d in dse_data if d.get('problem_type')])))
    
    # Получаем уникальные ID пользователей
    user_ids = sorted(list(set([d.get('user_id', '') for d in dse_data if d.get('user_id')])))
    
    return render_template('pdf_export.html', 
                         dse_data=dse_data,
                         problem_types=problem_types,
                         user_ids=user_ids)


@app.route('/reports')
@login_required
@user_role_required(['admin', 'responder', 'initiator'])
def reports():
    """Страница отчетов"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'export_data'):
        return "Доступ запрещен", 403
    
    return render_template('reports.html')


@app.route('/chat')
@login_required
@user_role_required(['admin', 'responder', 'initiator'])
def chat():
    """Страница чата"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'chat_dse'):
        return "Доступ запрещен", 403
    
    # Получить историю чата
    chat_history = get_chat_history(user_id)
    
    return render_template('chat.html', messages=chat_history)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/dse', methods=['GET'])
@login_required
def api_get_dse():
    """API: Получить список ДСЕ"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'view_dse'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    dse_data = get_all_dse()
    return jsonify(dse_data)


@app.route('/api/dse/<int:dse_id>', methods=['GET'])
@login_required
def api_get_dse_detail(dse_id):
    """API: Получить детали ДСЕ"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'view_dse'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    dse = get_dse_by_id(dse_id)
    if not dse:
        return jsonify({'error': 'ДСЕ не найдено'}), 404
    
    return jsonify(dse)


@app.route('/api/dse', methods=['POST'])
@login_required
def api_create_dse():
    """API: Создать новое ДСЕ"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'add_dse'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    result = add_dse(data)
    
    return jsonify(result), 201


@app.route('/api/dse/<int:dse_id>', methods=['PUT'])
@login_required
def api_update_dse(dse_id):
    """API: Обновить ДСЕ"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'edit_dse'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    result = update_dse(dse_id, data)
    
    return jsonify(result)


@app.route('/api/dse/<int:dse_id>', methods=['DELETE'])
@login_required
def api_delete_dse(dse_id):
    """API: Удалить ДСЕ"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'delete_dse'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    result = delete_dse(dse_id)
    return jsonify(result)


@app.route('/api/export/excel', methods=['GET'])
@login_required
def api_export_excel():
    """API: Экспорт в Excel"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'export_data'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    try:
        import tempfile
        import pandas as pd
        
        # Получаем все данные ДСЕ
        dse_data = get_all_dse()
        
        if not dse_data:
            return jsonify({'error': 'Нет данных для экспорта'}), 400
        
        # Подготовка данных для Excel
        rows = []
        for record in dse_data:
            # Получаем данные пользователя
            user_info = None
            if record.get('user_id'):
                try:
                    user_info = get_user_data(str(record['user_id']))
                except:
                    pass
            
            row = {
                'ДСЕ': record.get('dse', ''),
                'Тип проблемы': record.get('problem_type', ''),
                'RC': record.get('rc', ''),
                'Номер станка': record.get('machine_number', ''),
                'ФИО Наладчика': record.get('installer_fio', ''),
                'ФИО Программиста': record.get('programmer_name', ''),
                'Описание': record.get('description', ''),
                'Дата создания': record.get('datetime', ''),
                'Пользователь': user_info.get('name', '') if user_info else f"ID: {record.get('user_id', '')}",
                'ID пользователя': record.get('user_id', ''),
                'Есть фото': 'Да' if record.get('photo_file_id') or record.get('photos') else 'Нет',
                'Отправлено на email': 'Да' if record.get('sent_to_emails') else 'Нет'
            }
            rows.append(row)
        
        # Создание DataFrame
        df = pd.DataFrame(rows)
        
        # Создание временного файла
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()
        
        # Сохранение в Excel
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Отчет ДСЕ')
            
            # Настройка ширины колонок
            worksheet = writer.sheets['Отчет ДСЕ']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Excel файл создан: {temp_file.name}, записей: {len(rows)}")
        
        return send_file(temp_file.name, 
                        as_attachment=True,
                        download_name=f'dse_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                        
    except Exception as e:
        logger.error(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка экспорта: {str(e)}'}), 500


@app.route('/api/export/pdf', methods=['POST'])
@login_required
def api_export_pdf():
    """API: Генерация PDF отчета"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'export_data'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    try:
        options = request.json
        
        if not options.get('dse_numbers'):
            return jsonify({'error': 'Не указаны номера ДСЕ'}), 400
        
        pdf_path = generate_pdf_report(options)
        
        # Определяем MIME тип и имя файла
        if options.get('mode') == 'multiple':
            mimetype = 'application/zip'
            download_name = f'DSE_Export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        else:
            mimetype = 'application/pdf'
            download_name = f'DSE_Export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return send_file(pdf_path,
                        as_attachment=True,
                        download_name=download_name,
                        mimetype=mimetype)
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return jsonify({'error': f'Ошибка генерации PDF: {str(e)}'}), 500


@app.route('/api/chat/messages', methods=['GET'])
@login_required
def api_get_messages():
    """API: Получить сообщения чата"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'chat_dse'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    messages = get_chat_history(user_id)
    return jsonify(messages)


@app.route('/api/chat/send', methods=['POST'])
@login_required
def api_send_message():
    """API: Отправить сообщение в чат"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'chat_dse'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    message = data.get('message')
    target_user_id = data.get('target_user_id')
    
    if not message:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    result = send_chat_message(user_id, target_user_id, message)
    return jsonify(result)


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_bot_username():
    """Получить username бота для Telegram Login Widget"""
    # Сначала проверяем конфигурацию
    if BOT_USERNAME and BOT_USERNAME != "":
        return BOT_USERNAME
    
    # Если не указан в конфиге, пытаемся получить через API
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot_info = loop.run_until_complete(bot.get_me())
        loop.close()
        logger.info(f"Username бота получен через API: @{bot_info.username}")
        return bot_info.username
    except Exception as e:
        logger.error(f"Ошибка получения username бота: {e}")
        logger.warning("Укажите BOT_USERNAME в ven_bot.json!")
        # Возвращаем заглушку если не удалось получить
        return "YourBotUsername"


def get_server_url():
    """
    Определить URL сервера для отображения в веб-интерфейсе
    Учитывает Docker окружение и публичный IP
    """
    import socket
    import os
    
    # Проверка Docker окружения
    is_docker = os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')
    
    # Попытка получить публичный IP
    try:
        import urllib.request
        public_ip = urllib.request.urlopen('https://ifconfig.me', timeout=2).read().decode('utf-8').strip()
    except:
        try:
            import urllib.request
            public_ip = urllib.request.urlopen('https://icanhazip.com', timeout=2).read().decode('utf-8').strip()
        except:
            public_ip = None
    
    # Получить локальный IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = 'localhost'
    
    # Определить порт
    port = int(os.getenv('WEB_PORT', '5000'))
    
    # Выбрать лучший URL
    if public_ip and public_ip != local_ip:
        url = f"http://{public_ip}:{port}"
        url_type = "Public"
    elif local_ip != 'localhost':
        url = f"http://{local_ip}:{port}"
        url_type = "Local Network"
    else:
        url = f"http://localhost:{port}"
        url_type = "Local"
    
    return {
        'url': url,
        'type': url_type,
        'public_ip': public_ip,
        'local_ip': local_ip,
        'port': port,
        'is_docker': is_docker
    }


def get_user_permissions(user_id):
    """Получить все права пользователя"""
    permissions = {
        'admin': has_permission(user_id, 'admin'),
        'view_dse': has_permission(user_id, 'view_dse'),
        'add_dse': has_permission(user_id, 'add_dse'),
        'edit_dse': has_permission(user_id, 'edit_dse'),
        'delete_dse': has_permission(user_id, 'delete_dse'),
        'export_data': has_permission(user_id, 'export_data'),
        'chat_dse': has_permission(user_id, 'chat_dse'),
    }
    return permissions


# ============================================================================
# ОБРАБОТЧИКИ ОШИБОК
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Обработка 404 ошибки"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработка 500 ошибки"""
    logger.error(f"Internal error: {error}")
    return render_template('500.html'), 500


# ============================================================================
# API ДЛЯ ПРОФИЛЯ
# ============================================================================

@app.route('/api/profile/stats')
@login_required
def get_profile_stats():
    """API: Получение статистики пользователя"""
    user_id = session['user_id']
    
    # Подсчёт статистики
    dse_data = get_all_dse()
    user_dse = [d for d in dse_data if d.get('user_id') == user_id]
    
    stats = {
        'dse_count': len(user_dse),
        'reports_count': 0,  # TODO: подсчёт отчётов
        'chats_count': 0,    # TODO: подсчёт чатов
        'activity_days': calculate_activity_days(user_id)
    }
    
    return jsonify(stats)


@app.route('/api/profile/test-email', methods=['POST'])
@login_required
def send_test_email():
    """API: Отправка тестового email"""
    user_id = session['user_id']
    
    # Проверка прав администратора
    if get_user_role(user_id) != 'admin':
        return jsonify({'error': 'Только администраторы могут отправлять тестовые письма'}), 403
    
    data = request.json
    email = data.get('email', '').strip()
    
    if not email or '@' not in email:
        return jsonify({'error': 'Некорректный email адрес'}), 400
    
    try:
        # Отправка тестового письма
        send_test_notification_email(email, user_id)
        return jsonify({'success': True, 'message': 'Тестовое письмо отправлено'})
    except Exception as e:
        logger.error(f"Ошибка отправки тестового письма: {e}")
        return jsonify({'error': str(e)}), 500


def calculate_activity_days(user_id):
    """Подсчёт дней активности пользователя"""
    dse_data = get_all_dse()
    user_dse = [d for d in dse_data if d.get('user_id') == user_id]
    
    if not user_dse:
        return 0
    
    # Получение уникальных дат
    dates = set()
    for record in user_dse:
        try:
            date_str = record.get('datetime', '').split(' ')[0]
            if date_str:
                dates.add(date_str)
        except:
            pass
    
    return len(dates)


def send_test_notification_email(email, user_id):
    """Отправка тестового уведомления на email"""
    
    # Создание тестового сообщения
    subject = "BOLT - Тестовое уведомление"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #1E5EFF;">BOLT - Тестовое уведомление</h2>
        <p>Это тестовое письмо для проверки настроек email-рассылки.</p>
        <p><strong>ID пользователя:</strong> {user_id}</p>
        <p><strong>Дата отправки:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            Вы получили это письмо, потому что подписались на уведомления о новых заявлениях в системе BOLT.
        </p>
    </body>
    </html>
    """
    
    # Отправка без вложения
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    # Загрузка SMTP настроек
    smtp_config = {}
    # try:
    from config.config import CONFIG_DIR

    smtp_file = CONFIG_DIR / "smtp_config.json"
    with open(smtp_file, 'r', encoding='utf-8') as f:
        smtp_config = json.load(f)
    # except:
    #     raise Exception("SMTP настройки не найдены. Настройте config/smtp_config.json")
    
    msg = MIMEMultipart()
    from_name = smtp_config.get('FROM_NAME', 'BOLT Bot')
    from_email = smtp_config.get('SMTP_USER', 'noreply@bolt.local')
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    server = smtplib.SMTP(smtp_config['SMTP_SERVER'], smtp_config['SMTP_PORT'])
    server.starttls()
    server.login(smtp_config['SMTP_USER'], smtp_config['SMTP_PASSWORD'])
    server.send_message(msg)
    server.quit()
    
    logger.info(f"Тестовое письмо отправлено на {email}")


# ============================================================================
# API ДЛЯ ИСТОРИИ ИЗМЕНЕНИЙ ПРАВ
# ============================================================================

@app.route('/api/permissions/log')
@login_required
def get_permissions_log_api():
    """API: Получение истории изменений прав"""
    user_id = session['user_id']
    
    # Проверка прав администратора
    if get_user_role(user_id) != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    logs = load_permissions_log()
    return jsonify(logs)


# ============================================================================
# СПЕЦИАЛЬНЫЙ ЭНДПОИНТ ДЛЯ ПОЛУЧЕНИЯ URL
# ============================================================================

@app.route('/api/server-info')
def server_info():
    """API для получения информации о сервере и URL"""
    info = get_server_url()
    return jsonify(info)


@app.route('/show-url')
def show_url():
    """Страница для отображения URL сервера"""
    info = get_server_url()
    
    # Определить домен для Telegram Login
    # Telegram Login Widget работает ТОЛЬКО с доменами или IP (без протокола и порта)
    if info['public_ip']:
        telegram_domain = info['public_ip']
    elif info['local_ip'] != 'localhost':
        telegram_domain = info['local_ip']
    else:
        telegram_domain = 'localhost'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TelegrammBolt - Server URL</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
        <style>
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            .info-box {{
                background: white;
                border-radius: 20px;
                padding: 3rem;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                width: 100%;
            }}
            .url-display {{
                background: #f8f9fa;
                border: 2px solid #667eea;
                border-radius: 10px;
                padding: 1.5rem;
                font-size: 1.2rem;
                font-weight: bold;
                color: #667eea;
                text-align: center;
                margin: 1.5rem 0;
                word-break: break-all;
            }}
            .badge-custom {{
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-size: 0.9rem;
            }}
            .copy-btn {{
                background: linear-gradient(135deg, #667eea, #764ba2);
                border: none;
                color: white;
                padding: 0.75rem 2rem;
                border-radius: 10px;
                font-weight: 600;
                transition: transform 0.2s;
            }}
            .copy-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }}
            .info-item {{
                display: flex;
                justify-content: space-between;
                padding: 0.75rem 0;
                border-bottom: 1px solid #e9ecef;
            }}
            .info-item:last-child {{
                border-bottom: none;
            }}
        </style>
    </head>
    <body>
        <div class="info-box">
            <div class="text-center mb-4">
                <i class="bi bi-robot display-1 text-primary"></i>
                <h1 class="mt-3">TelegrammBolt</h1>
                <p class="text-muted">Веб-интерфейс готов!</p>
            </div>
            
            <div class="mb-4">
                <span class="badge bg-success badge-custom">
                    <i class="bi bi-check-circle"></i> Online
                </span>
                {'<span class="badge bg-info badge-custom ms-2"><i class="bi bi-cloud"></i> Docker</span>' if info['is_docker'] else ''}
            </div>
            
            <h4 class="mb-3"><i class="bi bi-link-45deg"></i> URL для доступа:</h4>
            
            <div class="url-display" id="serverUrl">
                {info['url']}
            </div>
            
            <div class="text-center mb-4">
                <button class="copy-btn" onclick="copyUrl()">
                    <i class="bi bi-clipboard"></i> Копировать ссылку
                </button>
            </div>
            
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i>
                <strong>Тип доступа:</strong> {info['type']}
            </div>
            
            <hr>
            
            <h5 class="mb-3">Информация о сервере:</h5>
            
            <div class="info-item">
                <span><i class="bi bi-hdd-network"></i> Публичный IP:</span>
                <strong>{info['public_ip'] or 'Недоступен'}</strong>
            </div>
            
            <div class="info-item">
                <span><i class="bi bi-ethernet"></i> Локальный IP:</span>
                <strong>{info['local_ip']}</strong>
            </div>
            
            <div class="info-item">
                <span><i class="bi bi-door-open"></i> Порт:</span>
                <strong>{info['port']}</strong>
            </div>
            
            <hr>
            
            <div class="alert alert-warning">
                <h6><i class="bi bi-telegram"></i> Настройка Telegram Login:</h6>
                <p class="mb-2"><strong>Для работы Telegram Login Widget настройте домен в @BotFather:</strong></p>
                <ol class="mb-2 ps-3">
                    <li>Откройте @BotFather в Telegram</li>
                    <li>Отправьте: <code>/mybots</code> → Ваш бот → <code>Bot Settings</code> → <code>Domain</code></li>
                    <li>Укажите: <code>{telegram_domain}</code> <strong>(БЕЗ http:// и порта!)</strong></li>
                </ol>
                <div class="alert alert-info mb-0">
                    <strong>⚠️ Важно:</strong> Telegram принимает только домен или IP без протокола (http/https) и порта.<br>
                    <strong>Правильно:</strong> <code>{telegram_domain}</code><br>
                    <strong>Неправильно:</strong> <code>http://{telegram_domain}:5000</code>
                </div>
            </div>
            
            <div class="text-center mt-4">
                <a href="/" class="btn btn-primary">
                    <i class="bi bi-box-arrow-in-right"></i> Перейти к входу
                </a>
            </div>
        </div>
        
        <script>
            function copyUrl() {{
                const url = document.getElementById('serverUrl').textContent.trim();
                navigator.clipboard.writeText(url).then(() => {{
                    const btn = document.querySelector('.copy-btn');
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '<i class="bi bi-check2"></i> Скопировано!';
                    btn.classList.add('btn-success');
                    setTimeout(() => {{
                        btn.innerHTML = originalText;
                        btn.classList.remove('btn-success');
                    }}, 2000);
                }});
            }}
            
            // Автоматически копировать при загрузке (опционально)
            // copyUrl();
        </script>
    </body>
    </html>
    """
    
    return html


# ============================================================================
# API ДЛЯ QR КОДОВ И ПРИГЛАШЕНИЙ
# ============================================================================

@app.route('/invites')
@login_required
@admin_required
def invites_page():
    """Страница управления приглашениями"""
    user_id = session.get('user_id')
    
    # Получаем статистику
    stats = get_invite_stats(user_id)
    
    # Получаем активные и использованные приглашения
    active_invites = get_active_invites(user_id)
    used_invites = get_used_invites(user_id)
    
    # Статистика привязки аккаунтов
    linking_stats = get_linking_stats()
    
    return render_template('invites.html', 
                         stats=stats,
                         active_invites=active_invites,
                         used_invites=used_invites,
                         linking_stats=linking_stats,
                         roles=ROLES)

@app.route('/api/invites/create', methods=['POST'])
@login_required
@admin_required
def create_invite_api():
    """API для создания приглашения"""
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        role = data.get('role', 'initiator')
        expires_hours = int(data.get('expires_hours', 168))  # 7 дней по умолчанию
        note = data.get('note', '')
        
        # Проверяем что роль валидна и не admin
        if role not in ROLES or role == 'admin':
            return jsonify({"success": False, "error": "Недопустимая роль для приглашения"})
        
        # Создаем приглашение
        result = create_invite(user_id, role, expires_hours, note)
        
        if result["success"]:
            # Генерируем QR код
            invite_code = result["invite_code"]
            qr_data = generate_qr_code(invite_code)
            
            return jsonify({
                "success": True,
                "invite_code": invite_code,
                "qr_code": qr_data["base64"],
                "qr_url": qr_data["url"],
                "role": role,
                "role_name": ROLES[role],
                "expires_hours": expires_hours,
                "note": note
            })
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error creating invite: {e}")
        return jsonify({"success": False, "error": "Ошибка создания приглашения"})

@app.route('/api/invites/<invite_code>', methods=['DELETE'])
@login_required
@admin_required
def delete_invite_api(invite_code):
    """API для удаления приглашения"""
    user_id = session.get('user_id')
    
    try:
        result = delete_invite(invite_code, user_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error deleting invite: {e}")
        return jsonify({"success": False, "error": "Ошибка удаления приглашения"})

@app.route('/api/invites/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_invites_api():
    """API для очистки истекших приглашений"""
    try:
        cleaned_count = cleanup_expired_invites()
        return jsonify({
            "success": True,
            "message": f"Очищено истекших приглашений: {cleaned_count}"
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up invites: {e}")
        return jsonify({"success": False, "error": "Ошибка очистки приглашений"})

@app.route('/scan-invite')
@login_required
def scan_invite_page():
    """Страница сканирования приглашений"""
    return render_template('scan_invite.html')

@app.route('/api/scan-invite', methods=['POST'])
@login_required
def scan_invite_api():
    """API для активации приглашения по коду"""
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        invite_code = data.get('invite_code', '').strip().upper()
        
        if not invite_code:
            return jsonify({"success": False, "error": "Код приглашения не указан"})
        
        # Получаем данные пользователя из сессии
        username = session.get('username', '')
        first_name = session.get('first_name', '')
        last_name = session.get('last_name', '')
        
        # Используем приглашение
        from bot.invite_manager import use_invite
        result = use_invite(invite_code, user_id, username, first_name, last_name)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error using invite: {e}")
        return jsonify({"success": False, "error": "Ошибка активации приглашения"})

# ============================================================================
# API ДЛЯ ПРИВЯЗКИ АККАУНТОВ
# ============================================================================

@app.route('/link-account')
def link_account_page():
    """Страница привязки аккаунтов"""
    return render_template('link_account.html')

@app.route('/api/account/create-web', methods=['POST'])
def create_web_account_api():
    """API для создания веб-аккаунта"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        if not email or not password or not first_name:
            return jsonify({"success": False, "error": "Заполните все обязательные поля"})
        
        # Простое хеширование пароля (в продакшне использовать bcrypt)
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Создаем веб-пользователя
        web_user_id = create_web_user(email, password_hash, first_name, last_name)
        
        if web_user_id:
            # Генерируем код привязки
            link_code = generate_linking_code_for_web_user(web_user_id)
            
            return jsonify({
                "success": True,
                "message": "Аккаунт создан! Используйте код для привязки Telegram аккаунта",
                "link_code": link_code,
                "web_user_id": web_user_id
            })
        else:
            return jsonify({"success": False, "error": "Email уже используется"})
            
    except Exception as e:
        logger.error(f"Error creating web account: {e}")
        return jsonify({"success": False, "error": "Ошибка создания аккаунта"})

@app.route('/api/account/generate-link-code', methods=['POST'])
def generate_link_code_api():
    """API для генерации кода привязки для существующего веб-аккаунта"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"success": False, "error": "Введите email и пароль"})
        
        # Простое хеширование пароля
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Аутентификация
        web_user_id, user_data = authenticate_web_user(email, password_hash)
        
        if not web_user_id:
            return jsonify({"success": False, "error": "Неверный email или пароль"})
        
        # Проверяем что аккаунт еще не привязан
        if user_data.get('telegram_id'):
            return jsonify({"success": False, "error": "Аккаунт уже привязан к Telegram"})
        
        # Генерируем код привязки
        link_code = generate_linking_code_for_web_user(web_user_id)
        
        return jsonify({
            "success": True,
            "message": "Код привязки сгенерирован",
            "link_code": link_code
        })
        
    except Exception as e:
        logger.error(f"Error generating link code: {e}")
        return jsonify({"success": False, "error": "Ошибка генерации кода"})


# ============================================================================
# API ПОДПИСОК НА ЗАЯВКИ
# ============================================================================

@app.route('/api/subscription/status', methods=['GET'])
@login_required
@user_role_required(['admin'])
def api_subscription_status():
    """API: Получить статус подписки пользователя (только админы)"""
    try:
        user_id = session['user_id']
        
        from bot.subscription_manager import get_subscription
        subscription = get_subscription(user_id)
        
        if subscription:
            return jsonify({
                'success': True,
                'subscribed': subscription.get('active', False),
                'delivery_type': subscription.get('delivery_type'),
                'email': subscription.get('email'),
                'created_at': subscription.get('created_at')
            })
        else:
            return jsonify({
                'success': True,
                'subscribed': False
            })
    
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/subscription/add', methods=['POST'])
@login_required
@user_role_required(['admin'])
def api_subscription_add():
    """API: Добавить подписку (только админы)"""
    try:
        user_id = session['user_id']
        data = request.json
        
        delivery_type = data.get('delivery_type', 'telegram')
        email = data.get('email')
        
        if delivery_type not in ['telegram', 'email', 'both']:
            return jsonify({'success': False, 'error': 'Некорректный тип доставки'}), 400
        
        if delivery_type in ['email', 'both'] and not email:
            return jsonify({'success': False, 'error': 'Email обязателен для выбранного типа доставки'}), 400
        
        from bot.subscription_manager import add_subscription
        
        if add_subscription(user_id, delivery_type, email):
            return jsonify({
                'success': True,
                'message': 'Подписка успешно создана'
            })
        else:
            return jsonify({'success': False, 'error': 'Ошибка создания подписки'}), 500
    
    except Exception as e:
        logger.error(f"Error adding subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/subscription/remove', methods=['POST'])
@login_required
@user_role_required(['admin'])
def api_subscription_remove():
    """API: Удалить подписку (только админы)"""
    try:
        user_id = session['user_id']
        
        from bot.subscription_manager import remove_subscription
        
        if remove_subscription(user_id):
            return jsonify({
                'success': True,
                'message': 'Подписка удалена'
            })
        else:
            return jsonify({'success': False, 'error': 'Подписка не найдена'}), 404
    
    except Exception as e:
        logger.error(f"Error removing subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/subscription/toggle', methods=['POST'])
@login_required
@user_role_required(['admin'])
def api_subscription_toggle():
    """API: Переключить активность подписки (только админы)"""
    try:
        user_id = session['user_id']
        
        from bot.subscription_manager import toggle_subscription
        
        new_status = toggle_subscription(user_id)
        
        return jsonify({
            'success': True,
            'active': new_status,
            'message': 'Подписка активирована' if new_status else 'Подписка приостановлена'
        })
    
    except Exception as e:
        logger.error(f"Error toggling subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/subscription/stats', methods=['GET'])
@login_required
@user_role_required(['admin'])
def api_subscription_stats():
    """API: Статистика подписок (только для админов)"""
    try:
        from bot.subscription_manager import get_subscription_stats
        
        stats = get_subscription_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting subscription stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ВЕБ-ТЕРМИНАЛ
# ============================================================================

@app.route('/terminal')
@login_required
def terminal():
    """Страница веб-терминала"""
    try:
        # Проверяем права доступа (только для админов)
        user_id = session.get('user_id')
        user_role = get_user_role(user_id)
        
        if user_role not in ['admin', 'owner']:
            flash('У вас нет доступа к терминалу', 'error')
            return redirect(url_for('dashboard'))
        
        return render_template('terminal.html', 
                             username=session.get('username', 'User'))
    except Exception as e:
        logger.error(f"Error loading terminal page: {e}")
        flash('Ошибка загрузки терминала', 'error')
        return redirect(url_for('dashboard'))


# WebSocket обработчики для терминала

@socketio.on('connect', namespace='/terminal')
def handle_connect():
    """Обработка подключения к терминалу"""
    try:
        # Проверяем авторизацию
        if 'user_id' not in session:
            return False
        
        user_id = session.get('user_id')
        user_role = get_user_role(user_id)
        
        if user_role not in ['admin', 'owner']:
            return False
        
        logger.info(f"User {user_id} connected to terminal")
        emit('connected', {'status': 'ready'})
        
    except Exception as e:
        logger.error(f"Error in terminal connect: {e}")
        return False


@socketio.on('disconnect', namespace='/terminal')
def handle_disconnect():
    """Обработка отключения от терминала"""
    try:
        user_id = session.get('user_id')
        session_id = request.sid
        
        # Выходим из комнаты
        leave_room(session_id, namespace='/terminal')
        
        # Останавливаем сессию терминала
        terminal_manager.remove_session(session_id)
        
        logger.info(f"User {user_id} disconnected from terminal, session {session_id} stopped")
        
    except Exception as e:
        logger.error(f"Error in terminal disconnect: {e}")


@socketio.on('start_terminal', namespace='/terminal')
def handle_start_terminal(data):
    """Запуск терминальной сессии"""
    try:
        user_id = session.get('user_id')
        session_id = request.sid
        
        # Присоединяемся к комнате для этой сессии
        join_room(session_id, namespace='/terminal')
        
        cols = data.get('cols', 80)
        rows = data.get('rows', 24)
        
        logger.info(f"Starting terminal for user {user_id}, session {session_id}, size {cols}x{rows}")
        
        # Создаем новую сессию
        terminal_session = terminal_manager.create_session(session_id, user_id, cols, rows)
        
        if terminal_session:
            # Запускаем поток для отправки вывода клиенту
            import threading
            
            def send_output():
                while terminal_session.running:
                    output = terminal_session.read(timeout=0.05)
                    if output:
                        try:
                            socketio.emit('output', 
                                        {'data': output.decode('utf-8', errors='replace')},
                                        namespace='/terminal',
                                        room=session_id)
                        except Exception as e:
                            logger.error(f"Error sending output: {e}")
                            break
            
            output_thread = threading.Thread(target=send_output)
            output_thread.daemon = True
            output_thread.start()
            
            emit('started', {'status': 'success', 'session_id': session_id}, namespace='/terminal')
            logger.info(f"Terminal started successfully for user {user_id}")
        else:
            emit('error', {'message': 'Не удалось запустить терминал'}, namespace='/terminal')
            
    except Exception as e:
        logger.error(f"Error starting terminal: {e}")
        emit('error', {'message': str(e)}, namespace='/terminal')


@socketio.on('input', namespace='/terminal')
def handle_input(data):
    """Обработка ввода в терминал"""
    try:
        session_id = request.sid
        terminal_session = terminal_manager.get_session(session_id)
        
        if terminal_session:
            input_data = data.get('data', '')
            logger.debug(f"Terminal input from {session_id}: {repr(input_data)}")
            success = terminal_session.write(input_data)
            if not success:
                logger.error(f"Failed to write to terminal session {session_id}")
        else:
            logger.warning(f"Terminal session not found for {session_id}")
            emit('error', {'message': 'Терминальная сессия не найдена'}, namespace='/terminal')
            
    except Exception as e:
        logger.error(f"Error handling terminal input: {e}")
        emit('error', {'message': str(e)}, namespace='/terminal')


@socketio.on('resize', namespace='/terminal')
def handle_resize(data):
    """Изменение размера терминала"""
    try:
        session_id = request.sid
        terminal_session = terminal_manager.get_session(session_id)
        
        if terminal_session:
            cols = data.get('cols', 80)
            rows = data.get('rows', 24)
            terminal_session.resize(cols, rows)
            
    except Exception as e:
        logger.error(f"Error resizing terminal: {e}")


# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == '__main__':
    # Чтение конфигурации домена
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'domain.conf')
    web_port = int(os.getenv('WEB_PORT', '5000'))  # Порт можно задать через переменную окружения
    domain = 'localhost'
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() == 'WEB_PORT':
                                web_port = int(value.strip())
                            elif key.strip() == 'DOMAIN':
                                domain = value.strip()
            logger.info(f"Configuration loaded from {config_file}")
        except Exception as e:
            logger.warning(f"Could not read config: {e}, using defaults")
    
    # Вывод информации о сервере при запуске
    info = get_server_url()
    
    print("\n" + "="*60)
    print("TelegrammBolt Web Interface Starting...")
    print("="*60)
    print(f"Access URL: {info['url']}")
    print(f"Environment: {'Docker' if info['is_docker'] else 'Native'}")
    print(f"Server Info Page: {info['url']}/show-url")
    
    if info['public_ip']:
        print(f"Public IP: {info['public_ip']}")
    print(f"Local IP: {info['local_ip']}")
    print(f"Port: {web_port}")
    if domain != 'localhost':
        print(f"Domain: {domain}")
    
    print("\n" + "="*60)
    print("Server is ready!")
    print("="*60 + "\n")
    
    # Для разработки и тестирования (с поддержкой WebSocket)
    # В продакшене используйте Gunicorn через manage.sh (опция 6)
    print(" WARNING: Используется встроенный сервер Werkzeug")
    print("   Для продакшена запустите через: ./manage.sh (опция 6)")
    print("   Или: gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:{} web.web_app:app\n".format(web_port))
    
    socketio.run(app, host='0.0.0.0', port=web_port, debug=True, allow_unsafe_werkzeug=True)
