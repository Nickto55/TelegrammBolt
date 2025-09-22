import json
import logging
import os

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
WATCHED_DSE_FILE = "watched_dse.json"


def load_data(filename):
    """Загрузка данных из файла"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_data(data, filename):
    """Сохранение данных в файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Токен бота
def load_config_settings_bot(ven_bot: str = "ven_bot.json"):
    file_path = os.path.join(os.getcwd(), ven_bot)

    ven_bot_data = {
        "BOT_TOKEN:": "",
        "ADMIN_IDS:": []
    }

    def update_data(chose_update):
        nonlocal ven_bot_data, file_path

        ven_bot_data[chose_update] = "bns"
        save_data(ven_bot_data, file_path)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(ven_bot_data, f, indent=4)

    ven_bot_data = load_data(ven_bot)

    for i in ven_bot_data.keys():
        if ven_bot_data.get(i, "") == "":
            update_data(i)

    return ven_bot_data


ven_bot_data = load_config_settings_bot()
BOT_TOKEN = ven_bot_data.get("BOT_TOKEN:")
ADMIN_IDS = ven_bot_data.get("ADMIN_IDS:")



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

