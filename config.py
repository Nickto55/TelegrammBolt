# config.py
import json
import logging
import os
from datetime import datetime as dt

# Отключение лишних логов
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Application").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Файлы для хранения данных
DATA_FILE = "bot_data.json"
USERS_FILE = "users_data.json"
CHAT_FILE = "chat_data.json"
WATCHED_DSE_FILE = "watched_dse.json"  # Новый файл для отслеживания
PHOTOS_DIR = "photos"
os.makedirs(PHOTOS_DIR, exist_ok=True) # Создаем директорию при импорте модуля


def load_data(filename):
    """Загрузка данных из файла"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            # Можно добавить логирование ошибки, если нужно
            # logging.error(f"Ошибка загрузки {filename}: {e}")
            return {}
    return {}


def save_data(data, filename):
    """Сохранение данных в файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения в {filename}: {e}")
        raise  # Перебрасываем исключение, чтобы вызывающая функция знала об ошибке


# --- Загрузка настроек бота из ven_bot.json ---
def load_config_settings_bot(ven_bot: str = "ven_bot.json"):
    """
    Загружает настройки бота (токен, админы) из файла ven_bot.json.
    Если файл или поля отсутствуют, создает шаблон и запрашивает ввод (в данном случае просто помечает).
    """
    file_path = os.path.join(os.getcwd(), ven_bot)

    # Шаблон данных
    ven_bot_data = {
        "BOT_TOKEN": "",  # Убрано двоеточие
        "ADMIN_IDS": [],  # Убрано двоеточие
        "BOT_USERNAME": ""  # Username бота для веб-интерфейса
    }

    def update_data(key_to_update):
        """Обновляет указанное поле в ven_bot_data и сохраняет в файл."""
        nonlocal ven_bot_data, file_path

        # Простая "заглушка" для пометки незаполненных полей
        if key_to_update == "":
            if key_to_update == "BOT_TOKEN":
                ven_bot_data[key_to_update] = "YOUR_BOT_TOKEN_HERE"
            elif key_to_update == "ADMIN_IDS":
                ven_bot_data[key_to_update] = ["YOUR_TELEGRAM_ID_HERE"]

        save_data(ven_bot_data, file_path)

    # Создаем директорию, если её нет
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Если файл не существует, создаем его с шаблоном
    if not os.path.exists(file_path):
        save_data(ven_bot_data, file_path)  # Сохраняем шаблон
        print(f"⚠️  Создан файл настроек {file_path}. Пожалуйста, заполните его.")

    # Загружаем данные из файла
    try:
        loaded_data = load_data(file_path)
        if isinstance(loaded_data, dict):
            ven_bot_data.update(loaded_data)  # Обновляем шаблон загруженными данными
        else:
            print(f"⚠️  Файл {file_path} поврежден или содержит неверный формат. Используются значения по умолчанию.")
    except Exception as e:
        print(f"⚠️  Ошибка загрузки {file_path}: {e}. Используются значения по умолчанию.")

    # Проверяем, заполнены ли обязательные поля. Если нет - помечаем.
    for key in ven_bot_data.keys():
        if ven_bot_data.get(key, "") == "" or (isinstance(ven_bot_data[key], list) and not ven_bot_data[key]):
            print(f"⚠️  Поле '{key}' в {file_path} не заполнено.")
            update_data(key)  # Помечаем незаполненное поле

    return ven_bot_data


# Загружаем настройки
ven_bot_data = load_config_settings_bot()

# Экспортируем настройки для использования в других модулях
BOT_TOKEN = ven_bot_data.get("BOT_TOKEN", "")
BOT_USERNAME = ven_bot_data.get("BOT_USERNAME", "")  # Username бота
# Убедимся, что ADMIN_IDS всегда список
ADMIN_IDS = ven_bot_data.get("ADMIN_IDS", [])
if not isinstance(ADMIN_IDS, list):
    ADMIN_IDS = [ADMIN_IDS] if ADMIN_IDS else []

# Список типов проблем
PROBLEM_TYPES = [
    "Ошибка УП и КН",
    "Замечание по базированию",
    "Замечание по обработке",
    "Запрос по КД и ТД",
    "Оснастка",
    "Маршрут",
    "Трудоемкость",
    "Рацпредложение",
    "Перевод",
    "Другое"
]

# Список рабочих центров
RC_TYPES = [
    "11102",
    "11402", 
    "11403",
    "11404"
]

# --- Дополнительные проверки ---
if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("❌ Критическая ошибка: BOT_TOKEN не установлен или не заполнен в ven_bot.json!")
    # Можно вызвать sys.exit(1) здесь, если хотите, чтобы бот не запускался без токена

if not ADMIN_IDS or (len(ADMIN_IDS) == 1 and ADMIN_IDS[0] == "YOUR_TELEGRAM_ID_HERE"):
    print("⚠️  Предупреждение: ADMIN_IDS не заполнен или содержит шаблонный ID в ven_bot.json.")

# === НАСТРОЙКИ SMTP ДЛЯ ОТПРАВКИ EMAIL ===
# Эти настройки можно вынести в ven_bot.json или создать отдельный файл для них
SMTP_SETTINGS = {
    "SMTP_SERVER": "smtp.gmail.com",  # Для Gmail
    "SMTP_PORT": 587,
    "SMTP_USER": "",  # Ваш email для отправки
    "SMTP_PASSWORD": "",  # Пароль приложения для Gmail или обычный пароль
    "FROM_NAME": "Бот учета ДСЕ"  # Имя отправителя
}

# Функция для загрузки настроек SMTP из отдельного файла (опционально)
def load_smtp_config():
    """Загружает настройки SMTP из отдельного файла (опционально)"""
    smtp_file = "smtp_config.json"
    
    if os.path.exists(smtp_file):
        try:
            smtp_data = load_data(smtp_file)
            if smtp_data:
                SMTP_SETTINGS.update(smtp_data)
                return True
        except Exception as e:
            print(f"⚠️  Ошибка загрузки SMTP настроек: {e}")
    
    return False

# Попытка загрузки SMTP настроек из файла
if not load_smtp_config():
    # Если файл не существует, создаем шаблон
    smtp_template = {
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": 587,
        "SMTP_USER": "your_email@gmail.com",
        "SMTP_PASSWORD": "your_app_password",
        "FROM_NAME": "Бот учета ДСЕ"
    }
    
    smtp_file = "smtp_config.json"
    if not os.path.exists(smtp_file):
        try:
            save_data(smtp_template, smtp_file)
            print(f"⚠️  Создан файл настроек SMTP: {smtp_file}")
            print("📧 Для отправки файлов по email настройте параметры в smtp_config.json")
        except Exception as e:
            print(f"⚠️  Не удалось создать файл SMTP настроек: {e}")

# Проверка заполненности SMTP настроек
def is_smtp_configured():
    """Проверяет, настроена ли отправка email"""
    return (SMTP_SETTINGS.get("SMTP_USER") and 
            SMTP_SETTINGS.get("SMTP_PASSWORD") and
            SMTP_SETTINGS["SMTP_USER"] != "your_email@gmail.com")


# === НАСТРОЙКИ АДМИНОВ ДЛЯ ВЕБ-ИНТЕРФЕЙСА ===
# Креденшиалы для входа через логин/пароль
# Пароли хранятся в виде SHA256 хешей
import hashlib

def generate_password_hash(password: str) -> str:
    """Генерирует SHA256 хеш для пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

# Словарь админ-кредов: {username: sha256(password)}
# По умолчанию: admin / admin123
ADMIN_CREDENTIALS = {
    'admin': generate_password_hash('admin123'),
    'admin_user_id': 'admin_web'  # ID для веб-админа
}

# Можно добавить больше админов:
# ADMIN_CREDENTIALS['superadmin'] = generate_password_hash('super_secret_password')
# ADMIN_CREDENTIALS['superadmin_user_id'] = 'admin_super'

def save_admin_credentials(username: str, password_hash: str):
    """Сохраняет учётные данные администратора в файл"""
    import json
    import os
    
    credentials_file = 'web_credentials.json'
    
    # Загрузка существующих данных
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}
    else:
        data = {}
    
    # Добавление нового пользователя
    data[username] = {
        'password_hash': password_hash,
        'user_id': f'{username}_web',
        'created_at': dt.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Сохранение
    with open(credentials_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Веб-пользователь '{username}' сохранён в {credentials_file}")

def load_admin_credentials():
    """Загружает учётные данные из файла"""
    import json
    import os
    
    credentials_file = 'web_credentials.json'
    
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Обновление ADMIN_CREDENTIALS
            for username, creds in data.items():
                ADMIN_CREDENTIALS[username] = creds['password_hash']
                ADMIN_CREDENTIALS[f'{username}_user_id'] = creds['user_id']
            
            print(f"✅ Загружено {len(data)} веб-пользователей из {credentials_file}")
        except Exception as e:
            print(f"⚠️  Ошибка загрузки веб-пользователей: {e}")

# Загрузка сохранённых учётных данных при старте
load_admin_credentials()

print(f"ℹ️  Веб-админ логин: admin / admin123 (измените пароль в config.py!)")

