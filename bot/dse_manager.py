import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import DATA_FILE, load_data


def get_all_dse_records(include_hidden: bool = False):
    """Получить все записи ДСЕ"""
    all_data = load_data(DATA_FILE)
    records = []

    for user_id, user_records in all_data.items():
        if isinstance(user_records, list):
            for idx, record in enumerate(user_records):
                if record.get('hidden') and not include_hidden:
                    continue
                record_with_user = record.copy()
                record_with_user['user_id'] = user_id
                # Генерируем уникальный ID если его нет
                # Используем формат: user_id_index для надёжности
                if 'id' not in record_with_user:
                    record_with_user['id'] = f"{user_id}_{idx}"
                records.append(record_with_user)

    return records


def get_dse_records_by_user(user_id):
    """Получить записи ДСЕ конкретного пользователя"""
    all_data = load_data(DATA_FILE)
    return all_data.get(str(user_id), [])


def search_dse_records(dse_filter=None, problem_type_filter=None, include_hidden: bool = False):
    """Поиск записей ДСЕ по фильтрам"""
    records = get_all_dse_records(include_hidden=include_hidden)

    if dse_filter:
        records = [r for r in records if dse_filter.lower() in r.get('dse', '').lower()]

    if problem_type_filter:
        records = [r for r in records if problem_type_filter.lower() in r.get('problem_type', '').lower()]

    return records


def get_unique_dse_values(include_hidden: bool = False):
    """Получить список уникальных значений ДСЕ из всех записей."""
    records = get_all_dse_records(include_hidden=include_hidden)
    dse_values = list(
        set([record.get('dse', '').strip().lower() for record in records if record.get('dse', '').strip()]))
    return sorted(dse_values)


def get_problem_types_list():
    """Получить список всех типов проблем"""
    records = get_all_dse_records()
    problem_types = list(set([r.get('problem_type', '') for r in records if r.get('problem_type', '')]))
    return sorted(problem_types)