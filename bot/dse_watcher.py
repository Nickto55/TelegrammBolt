import json
import os
import asyncio
import sys
from typing import Dict, List, Set

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем load_data из config
from config.config import WATCHED_DSE_FILE, DATA_FILE, load_data as config_load_data

# Глобальная переменная для хранения отслеживаемых ДСЕ в памяти
# Формат: {user_id: set(dse_values)}. Храним в нижнем регистре для сравнения.
watched_dse_data: Dict[str, Set[str]] = {}

# Храним последние известные ID записей, чтобы не дублировать уведомления
# Формат: {dse_value_lower: set(record_ids)}
last_known_records: Dict[str, Set[str]] = {}


def load_watched_dse_data():
    """Загружает данные об отслеживаемых ДСЕ из файла в память."""
    global watched_dse_data
    if os.path.exists(WATCHED_DSE_FILE):
        try:
            data = config_load_data(WATCHED_DSE_FILE)
            # Преобразуем списки обратно в множества и приводим к нижнему регистру для внутренней логики
            watched_dse_data = {user_id: {dse.strip().lower() for dse in dse_list} for user_id, dse_list in
                                data.items()}
            print("✅ Данные отслеживаемых ДСЕ загружены.")
        except Exception as e:
            print(f"❌ Ошибка загрузки {WATCHED_DSE_FILE}: {e}")
            watched_dse_data = {}
    else:
        watched_dse_data = {}
    return watched_dse_data


def save_watched_dse_data():
    """Сохраняет данные об отслеживаемых ДСЕ из памяти в файл."""
    global watched_dse_data
    # Преобразуем множества в списки для сериализации JSON
    data_to_save = {user_id: list(dse_set) for user_id, dse_set in watched_dse_data.items()}
    try:
        with open(WATCHED_DSE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        print("💾 Данные отслеживаемых ДСЕ сохранены.")
    except Exception as e:
        print(f"❌ Ошибка сохранения {WATCHED_DSE_FILE}: {e}")


def add_watched_dse(user_id: str, dse_value: str):
    """Добавляет ДСЕ в список отслеживаемых для пользователя."""
    global watched_dse_data
    dse_normalized = dse_value.strip().lower()  # Нормализуем для внутренней логики
    if user_id not in watched_dse_data:
        watched_dse_data[user_id] = set()
    watched_dse_data[user_id].add(dse_normalized)
    save_watched_dse_data()


def remove_watched_dse(user_id: str, dse_value: str):
    """Удаляет ДСЕ из списка отслеживаемых для пользователя."""
    global watched_dse_data
    dse_normalized = dse_value.strip().lower()  # Нормализуем для внутренней логики
    if user_id in watched_dse_data:
        watched_dse_data[user_id].discard(dse_normalized)
        # Если список для пользователя опустел, можно его удалить
        if not watched_dse_data[user_id]:
            del watched_dse_data[user_id]
        save_watched_dse_data()


def get_watched_dse_list(user_id: str) -> List[str]:
    """Возвращает список ДСЕ, отслеживаемых пользователем."""
    global watched_dse_data
    # Возвращаем список нормализованных значений
    return list(watched_dse_data.get(user_id, set()))


def get_all_watched_dse() -> Dict[str, Set[str]]:
    """Возвращает полные данные об отслеживаемых ДСЕ."""
    global watched_dse_data
    return watched_dse_data


def _get_record_id(record: dict, user_id: str) -> str:
    """Генерирует уникальный ID для записи."""
    # Комбинируем пользовательский ID, ДСЕ и хэш описания для уникальности
    dse = record.get('dse', '')
    desc = record.get('description', '')
    # Простой способ создать ID, можно усложнить при необходимости
    # ВАЖНО: используем нормализованное значение ДСЕ
    dse_normalized = dse.strip().lower()
    return f"{user_id}_{dse_normalized}_{hash(desc)}"


async def check_for_new_dse_and_notify(context):
    """
    Проверяет новые записи ДСЕ и уведомляет пользователей.
    Эта функция будет вызываться периодически.
    """
    global last_known_records

    print("🔍 Проверка новых ДСЕ для уведомлений...")

    # 1. Загружаем все текущие данные бота
    all_bot_data = config_load_data(DATA_FILE)

    # 2. Загружаем данные об отслеживании
    current_watched = get_all_watched_dse()  # {user_id: set(dse_normalized)}

    if not current_watched:
        print("📭 Нет отслеживаемых ДСЕ.")
        return

    # 3. Для каждого отслеживаемого ДСЕ проверяем новые записи
    # Сначала соберем все отслеживаемые DSE в один набор для эффективного поиска
    all_watched_dse_normalized = set()
    for dse_set in current_watched.values():
        all_watched_dse_normalized.update(dse_set)

    if not all_watched_dse_normalized:
        print("📭 Нет отслеживаемых ДСЕ.")
        return

    print(f"👁️ Отслеживаемые ДСЕ: {all_watched_dse_normalized}")

    # Теперь пройдемся по всем записям и проверим, относятся ли они к отслеживаемым ДСЕ
    # И соберем информацию о записях для каждого отслеживаемого ДСЕ
    records_per_dse = {dse: [] for dse in all_watched_dse_normalized}
    record_ids_current = {dse: set() for dse in all_watched_dse_normalized}

    for data_user_id, user_records in all_bot_data.items():
        if isinstance(user_records, list):
            for record in user_records:
                # Уведомляем только по утверждённым заявкам
                if not record.get('approved_at'):
                    continue
                record_dse_original = record.get('dse', '')
                if record_dse_original:
                    record_dse_normalized = record_dse_original.strip().lower()
                    # Проверяем, отслеживается ли это ДСЕ
                    if record_dse_normalized in all_watched_dse_normalized:
                        records_per_dse[record_dse_normalized].append((data_user_id, record))
                        record_id = _get_record_id(record, data_user_id)
                        record_ids_current[record_dse_normalized].add(record_id)

    # Теперь проверим каждое отслеживаемое ДСЕ на наличие новых записей
    for dse_normalized, current_record_ids in record_ids_current.items():
        previously_known_ids = last_known_records.get(dse_normalized, set())
        new_record_ids = current_record_ids - previously_known_ids

        if new_record_ids:
            print(f"🔔 Найдены новые записи для отслеживаемого ДСЕ '{dse_normalized}'")

            # Найдем пользователей, которые отслеживают это ДСЕ
            users_to_notify = []
            for user_id, watched_set in current_watched.items():
                if dse_normalized in watched_set:
                    users_to_notify.append(user_id)

            # Соберем информацию о новых записях для уведомления
            new_records_info = []
            for data_user_id, record in records_per_dse[dse_normalized]:
                record_id = _get_record_id(record, data_user_id)
                if record_id in new_record_ids:
                    problem = record.get('problem_type', 'Не указано')
                    desc = record.get('description', 'Нет описания')[:100] + "..." if len(
                        record.get('description', '')) > 100 else record.get('description', 'Нет описания')
                    from .user_manager import get_users_data
                    users_data = get_users_data()
                    user_info = users_data.get(data_user_id, {})
                    user_name = user_info.get('first_name', f"Пользователь {data_user_id}")
                    new_records_info.append(f"• От: {user_name}\n  Тип: {problem}\n  Описание: {desc}\n---")

            if new_records_info and users_to_notify:
                notification_text = f"🔔 Новые записи по отслеживаемому ДСЕ '{dse_normalized.upper()}':\n\n" + "\n".join(
                    new_records_info)

                # Уведомляем всех заинтересованных пользователей
                for user_id in users_to_notify:
                    try:
                        await context.bot.send_message(chat_id=user_id, text=notification_text)
                        print(f"📤 Уведомление отправлено пользователю {user_id} по ДСЕ '{dse_normalized}'")
                    except Exception as e:
                        print(f"❌ Ошибка уведомления пользователя {user_id} по ДСЕ '{dse_normalized}': {e}")
            elif users_to_notify:
                # На случай, если по какой-то причине информация о записях не собралась
                for user_id in users_to_notify:
                    try:
                        await context.bot.send_message(chat_id=user_id,
                                                       text=f"🔔 Появились новые данные по отслеживаемому ДСЕ '{dse_normalized.upper()}'. Проверьте список ДСЕ.")
                        print(f"📤 Уведомление (резервное) отправлено пользователю {user_id} по ДСЕ '{dse_normalized}'")
                    except Exception as e:
                        print(f"❌ Ошибка резервного уведомления пользователя {user_id} по ДСЕ '{dse_normalized}': {e}")

        # Обновляем список известных записей для этого ДСЕ
        last_known_records[dse_normalized] = current_record_ids

    print("✅ Проверка новых ДСЕ завершена.")


# Функция для запуска периодической проверки
async def start_watcher_job(application):
    """Запускает периодическую задачу проверки ДСЕ."""
    print("⏱️  Задача DSE Watcher запущена.")
    async def periodic_check():
        while True:
            try:
                await check_for_new_dse_and_notify(application)
            except asyncio.CancelledError:
                # Задача была отменена, выходим из цикла
                print("⏹️ Задача DSE Watcher остановлена.")
                break
            except Exception as e:
                import traceback
                print(f"❌ Ошибка в периодической проверке DSE Watcher: {e}")
                print(traceback.format_exc())
            await asyncio.sleep(300) # Проверяем каждую минуту

    # Запускаем задачу в фоне
    await periodic_check() # Просто запускаем корутину, Application управляет ею
