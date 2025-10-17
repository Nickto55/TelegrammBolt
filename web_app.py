"""
TelegrammBolt Web Interface
Веб-интерфейс для бота с авторизацией через Telegram
"""

import os
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import parse_qs

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_cors import CORS

# Импорты из существующих модулей бота
from config import BOT_TOKEN, BOT_USERNAME
from user_manager import (
    has_permission, 
    get_users_data, 
    get_user_data,
    get_user_role, 
    register_user,
    is_user_registered,
    set_user_role,
    ROLES
)
from dse_manager import get_all_dse_records, get_dse_records_by_user, search_dse_records
# chat_manager не имеет нужных функций для веб, используем свои реализации
from pdf_generator import create_dse_pdf_report
import pandas as pd

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)
app.secret_key = os.urandom(32)  # Для production используйте фиксированный ключ из config
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# CORS для API
CORS(app)

# ============================================================================
# ФУНКЦИИ-ОБЕРТКИ ДЛЯ СОВМЕСТИМОСТИ
# ============================================================================

def get_all_dse():
    """Обертка для получения всех ДСЕ"""
    return get_all_dse_records()


def get_dse_by_id(dse_id):
    """Получить конкретное ДСЕ по ID (фильтрация из всех записей)"""
    records = get_all_dse_records()
    for record in records:
        if str(record.get('id', '')) == str(dse_id) or str(record.get('dse', '')) == str(dse_id):
            return record
    return None


def add_dse(data):
    """Заглушка для добавления ДСЕ - требует реализации"""
    # TODO: реализовать добавление через бота или напрямую в DATA_FILE
    logger.warning("add_dse() not fully implemented")
    return {"success": False, "error": "Функция в разработке"}


def update_dse(dse_id, data):
    """Заглушка для обновления ДСЕ - требует реализации"""
    # TODO: реализовать обновление через бота или напрямую в DATA_FILE
    logger.warning("update_dse() not fully implemented")
    return {"success": False, "error": "Функция в разработке"}


def delete_dse(dse_id):
    """Заглушка для удаления ДСЕ - требует реализации"""
    # TODO: реализовать удаление через бота или напрямую в DATA_FILE
    logger.warning("delete_dse() not fully implemented")
    return {"success": False, "error": "Функция в разработке"}


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


def generate_pdf_report(data):
    """Обертка для создания PDF отчета"""
    # Используем create_dse_pdf_report из pdf_generator
    return create_dse_pdf_report(data)


def save_users_data(users_data):
    """Сохранение данных пользователей"""
    from config import USERS_FILE
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
    """Загрузка подписок на email"""
    subscriptions_file = 'email_subscriptions.json'
    if os.path.exists(subscriptions_file):
        try:
            with open(subscriptions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_email_subscription(user_id, enabled, email):
    """Сохранение подписки на email"""
    subscriptions_file = 'email_subscriptions.json'
    subscriptions = load_email_subscriptions()
    
    subscriptions[user_id] = {
        'enabled': enabled,
        'email': email,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(subscriptions_file, 'w', encoding='utf-8') as f:
        json.dump(subscriptions, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Email подписка обновлена для пользователя {user_id}: enabled={enabled}, email={email}")


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
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
        
        # Сохранение данных в сессию
        session.permanent = True
        session['user_id'] = user_id
        session['user_role'] = get_user_role(user_id)
        session['first_name'] = auth_data.get('first_name', '')
        session['last_name'] = auth_data.get('last_name', '')
        session['username'] = auth_data.get('username', '')
        session['photo_url'] = auth_data.get('photo_url', '')
        
        logger.info(f"User {user_id} logged in via Telegram")
        
        return jsonify({
            'success': True,
            'redirect': url_for('dashboard')
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
        import config
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
                from user_manager import set_user_role
                set_user_role(admin_user_id, 'admin')
            
            # Проверяем, что роль действительно admin
            if get_user_role(admin_user_id) != 'admin':
                return jsonify({'error': 'У пользователя нет прав администратора'}), 403
            
            # Сохранение данных в сессию
            session.permanent = True
            session['user_id'] = admin_user_id
            session['user_role'] = 'admin'
            session['first_name'] = 'Администратор'
            session['last_name'] = ''
            session['username'] = username
            session['photo_url'] = ''
            session['auth_type'] = 'admin'  # Помечаем тип авторизации
            
            logger.info(f"Admin {username} logged in via credentials")
            
            return jsonify({
                'success': True,
                'redirect': url_for('dashboard')
            })
        else:
            return jsonify({'error': 'Неверный логин или пароль'}), 401
    
    except Exception as e:
        logger.error(f"Admin auth error: {e}")
        return jsonify({'error': 'Ошибка авторизации'}), 500


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
    user_id = session['user_id']
    
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
    
    stats = {
        'total_dse': len(dse_data),
        'active_users': active_users,
        'recent_dse': recent_dse,
        'problem_types': problem_types,
        'top_problem_type': max(problem_types.items(), key=lambda x: x[1])[0] if problem_types else 'Нет данных'
    }
    
    return render_template('dashboard.html', 
                         user=user_data,
                         stats=stats,
                         permissions=get_user_permissions(user_id))


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
    
    # Получение старых данных для логирования
    users = get_users_data()
    old_role = users.get(user_id, {}).get('role', 'user')
    old_permissions = users.get(user_id, {}).get('permissions', [])
    
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


@app.route('/dse')
@login_required
def dse_list():
    """Список всех ДСЕ"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'view_dse'):
        return "Доступ запрещен", 403
    
    dse_data = get_all_dse()
    return render_template('dse_list.html', dse_data=dse_data)


@app.route('/dse/<int:dse_id>')
@login_required
def dse_detail(dse_id):
    """Детальная информация о ДСЕ"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'view_dse'):
        return "Доступ запрещен", 403
    
    dse = get_dse_by_id(dse_id)
    if not dse:
        return "ДСЕ не найдено", 404
    
    return render_template('dse_detail.html', dse=dse)


@app.route('/reports')
@login_required
def reports():
    """Страница отчетов"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'export_data'):
        return "Доступ запрещен", 403
    
    return render_template('reports.html')


@app.route('/chat')
@login_required
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
        file_path = 'RezultBot.xlsx'
        return send_file(file_path, 
                        as_attachment=True,
                        download_name=f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'error': 'Ошибка экспорта'}), 500


@app.route('/api/export/pdf', methods=['POST'])
@login_required
def api_export_pdf():
    """API: Генерация PDF отчета"""
    user_id = session['user_id']
    
    if not has_permission(user_id, 'export_data'):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    try:
        data = request.json
        pdf_path = generate_pdf_report(data)
        
        return send_file(pdf_path,
                        as_attachment=True,
                        download_name=f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                        mimetype='application/pdf')
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return jsonify({'error': 'Ошибка генерации PDF'}), 500


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
    from email_manager import send_email_with_pdf
    
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
    try:
        with open('smtp_config.json', 'r', encoding='utf-8') as f:
            smtp_config = json.load(f)
    except:
        raise Exception("SMTP настройки не найдены. Настройте smtp_config.json")
    
    msg = MIMEMultipart()
    msg['From'] = smtp_config.get('from_email', 'noreply@bolt.local')
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
    server.starttls()
    server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
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
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == '__main__':
    # Вывод информации о сервере при запуске
    info = get_server_url()
    
    print("\n" + "="*60)
    print("🚀 TelegrammBolt Web Interface Starting...")
    print("="*60)
    print(f"\n🌐 Access URL: {info['url']}")
    print(f"📍 Environment: {'Docker' if info['is_docker'] else 'Native'}")
    print(f"🔗 Server Info Page: {info['url']}/show-url")
    
    if info['public_ip']:
        print(f"🌍 Public IP: {info['public_ip']}")
    print(f"🏠 Local IP: {info['local_ip']}")
    print(f"🚪 Port: {info['port']}")
    
    print("\n" + "="*60)
    print("✅ Server is ready!")
    print("="*60 + "\n")
    
    # Для разработки
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    # Для production используйте gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
