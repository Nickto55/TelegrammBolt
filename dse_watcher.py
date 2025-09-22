# dse_watcher.py

import json
import os
import asyncio
from typing import Dict, List, Set
from config import WATCHED_DSE_FILE, DATA_FILE, load_data as config_load_data

# Глобальная переменная для хранения отслеживаемых ДСЕ в памяти
# Формат: {user_id: set(dse_values)}
watched_dse_data: Dict[str, Set[str]] = {}

# Храним последние известные ID записей, чтобы не дублировать уведомления
# Формат: {dse_value: set(record_ids)}
last_known_records: Dict[str, Set[str]] = {}


def load_watched_dse_data():
    """Загружает данные об отслеживаемых ДСЕ из файла в память."""
    global watched_dse_data
    if os.path.exists(WATCHED_DSE_FILE):
        try:
            data = config_load_data(WATCHED_DSE_FILE)
            # Преобразуем списки обратно в множества
            watched_dse_data = {user_id: set(dse_list) for user_id, dse_list in data.items()}
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
    if user_id not in watched_dse_data:
        watched_dse_data[user_id] = set()
    watched_dse_data[user_id].add(dse_value.strip().lower())
    save_watched_dse_data()


def remove_watched_dse(user_id: str, dse_value: str):
    """Удаляет ДСЕ из списка отслеживаемых для пользователя."""
    global watched_dse_data
    if user_id in watched_dse_data:
        watched_dse_data[user_id].discard(dse_value.strip().lower())
        # Если список для пользователя опустел, можно его удалить
        if not watched_dse_data[user_id]:
            del watched_dse_data[user_id]
        save_watched_dse_data()


def get_watched_dse_list(user_id: str) -> List[str]:
    """Возвращает список ДСЕ, отслеживаемых пользователем."""
    global watched_dse_data
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
    return f"{user_id}_{dse}_{hash(desc)}"


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
    current_watched = get_all_watched_dse()

    if not current_watched:
        print("📭 Нет отслеживаемых ДСЕ.")
        return

    # 3. Для каждого отслеживаемого ДСЕ проверяем новые записи
    for user_id, dse_set in current_watched.items():
        for dse_value in dse_set:
            # Найдем все записи с этим ДСЕ
            matching_records = []
            record_ids_in_current_check = set()

            for data_user_id, user_records in all_bot_data.items():
                if isinstance(user_records, list):
                    for record in user_records:
                        if record.get('dse', '').strip().lower() == dse_value:
                            matching_records.append((data_user_id, record))
                            record_id = _get_record_id(record, data_user_id)
                            record_ids_in_current_check.add(record_id)

            # Проверим, какие записи новые
            previously_known_ids = last_known_records.get(dse_value, set())
            new_record_ids = record_ids_in_current_check - previously_known_ids

            if new_record_ids:
                print(f"🔔 Найдены новые записи для ДСЕ '{dse_value}' у пользователя {user_id}")
                # Уведомляем пользователя
                try:
                    notification_text = f"🔔 Новая запись по отслеживаемому ДСЕ '{dse_value.upper()}':\n"
                    # Соберем информацию о новых записях
                    new_records_info = []
                    for data_user_id, record in matching_records:
                        record_id = _get_record_id(record, data_user_id)
                        if record_id in new_record_ids:
                            problem = record.get('problem_type', 'Не указано')
                            desc = record.get('description', 'Нет описания')[:50] + "..." if len(
                                record.get('description', '')) > 50 else record.get('description', 'Нет описания')
                            new_records_info.append(f"• Тип: {problem}\n  Описание: {desc}")

                    if new_records_info:
                        notification_text += "\n".join(new_records_info)
                        await context.bot.send_message(chat_id=user_id, text=notification_text)
                        print(f"📤 Уведомление отправлено пользователю {user_id}")
                    else:
                        # На случай, если произошла ошибка сопоставления ID
                        await context.bot.send_message(chat_id=user_id,
                                                       text=f"🔔 Появились новые данные по отслеживаемому ДСЕ '{dse_value.upper()}'. Проверьте список ДСЕ.")

                except Exception as e:
                    print(f"❌ Ошибка уведомления пользователя {user_id}: {e}")

            # Обновляем список известных записей для этого ДСЕ
            last_known_records[dse_value] = record_ids_in_current_check

    print("✅ Проверка новых ДСЕ завершена.")


# Функция для запуска периодической проверки
async def start_watcher_job(application):
    """Запускает периодическую задачу проверки ДСЕ."""

    async def periodic_check():
        while True:
            try:
                await check_for_new_dse_and_notify(application)
            except Exception as e:
                print(f"❌ Ошибка в периодической проверке DSE Watcher: {e}")
            await asyncio.sleep(60)  # Проверяем каждую минуту

    # Запускаем задачу в фоне
    application.create_task(periodic_check())
    print("⏱️  Задача DSE Watcher запущена (проверка каждые 60 секунд).")
