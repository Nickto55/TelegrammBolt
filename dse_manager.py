from config import DATA_FILE, load_data


def get_all_dse_records():
    """Получить все записи ДСЕ"""
    all_data = load_data(DATA_FILE)
    records = []

    # Собираем все записи из всех пользователей
    for user_id, user_records in all_data.items():
        if isinstance(user_records, list):
            for record in user_records:
                record_with_user = record.copy()
                record_with_user['user_id'] = user_id
                records.append(record_with_user)

    return records


def get_dse_records_by_user(user_id):
    """Получить записи ДСЕ конкретного пользователя"""
    all_data = load_data(DATA_FILE)
    return all_data.get(str(user_id), [])


def search_dse_records(dse_filter=None, problem_type_filter=None):
    """Поиск записей ДСЕ по фильтрам"""
    records = get_all_dse_records()

    if dse_filter:
        records = [r for r in records if dse_filter.lower() in r.get('dse', '').lower()]

    if problem_type_filter:
        records = [r for r in records if problem_type_filter.lower() in r.get('problem_type', '').lower()]

    return records


def get_unique_dse_list():
    """Получить уникальный список всех ДСЕ"""
    records = get_all_dse_records()
    dse_list = list(set([r.get('dse', '') for r in records if r.get('dse', '')]))
    return sorted(dse_list)


def get_problem_types_list():
    """Получить список всех типов проблем"""
    records = get_all_dse_records()
    problem_types = list(set([r.get('problem_type', '') for r in records if r.get('problem_type', '')]))
    return sorted(problem_types)