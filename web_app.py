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
from config import BOT_TOKEN
from user_manager import has_permission, get_user_data, is_user_registered
from dse_manager import get_all_dse, get_dse_by_id, add_dse, update_dse, delete_dse
from chat_manager import get_chat_history, send_chat_message
from pdf_generator import generate_pdf_report
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
        if not is_user_registered(user_id):
            return jsonify({
                'error': 'Пользователь не зарегистрирован',
                'message': 'Сначала запустите бота в Telegram: /start'
            }), 403
        
        # Сохранение данных в сессию
        session.permanent = True
        session['user_id'] = user_id
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
    user_data = get_user_data(user_id)
    
    # Статистика
    dse_data = get_all_dse()
    stats = {
        'total_dse': len(dse_data),
        'active_chats': 0,  # TODO: подсчет активных чатов
        'reports_generated': 0,  # TODO: статистика отчетов
    }
    
    return render_template('dashboard.html', 
                         user=user_data,
                         stats=stats,
                         permissions=get_user_permissions(user_id))


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
    # TODO: Реализовать получение username через Bot API
    # Временно возвращаем заглушку
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
                <ol class="mb-0 ps-3">
                    <li>Откройте @BotFather в Telegram</li>
                    <li>Отправьте: /mybots → Ваш бот → Bot Settings → Domain</li>
                    <li>Укажите домен: <code>{info['public_ip'] or info['local_ip']}</code></li>
                </ol>
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
