import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta

from config.config import DATA_FILE, load_data, save_data


PENDING_DSE_REQUESTS_KEY = 'pending_dse_requests'
ARCHIVED_DSE_REQUESTS_KEY = 'archived_dse_requests'
ARCHIVE_RETENTION_DAYS = 30


def _normalize_text(value: str) -> str:
    return (value or '').strip().lower()


def _ensure_dict(value):
    return value if isinstance(value, dict) else {}


def _parse_datetime(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        pass
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    return None


def _cleanup_archived_requests(data):
    archived = _ensure_dict(data.get(ARCHIVED_DSE_REQUESTS_KEY))
    if not archived:
        return False, archived
    now = datetime.now()
    cleaned = {}
    for req_id, record in archived.items():
        timestamp = record.get('archived_at') or record.get('created_at') or record.get('datetime')
        parsed = _parse_datetime(timestamp)
        if not parsed:
            cleaned[req_id] = record
            continue
        if now - parsed <= timedelta(days=ARCHIVE_RETENTION_DAYS):
            cleaned[req_id] = record
    changed = cleaned != archived
    if changed:
        data[ARCHIVED_DSE_REQUESTS_KEY] = cleaned
    return changed, cleaned


def add_pending_dse_request(record: dict, user_id: str) -> int:
    """Добавить новую заявку ДСЕ в очередь на проверку"""
    data = load_data(DATA_FILE)
    if not isinstance(data, dict):
        data = {}

    pending = _ensure_dict(data.get(PENDING_DSE_REQUESTS_KEY))
    next_id = max([int(k) for k in pending.keys() if str(k).isdigit()] or [0]) + 1

    record_copy = record.copy()
    record_copy['user_id'] = str(user_id)
    record_copy['status'] = 'pending'
    record_copy['created_at'] = datetime.now().isoformat()

    pending[str(next_id)] = record_copy
    data[PENDING_DSE_REQUESTS_KEY] = pending
    save_data(data, DATA_FILE)

    return next_id


def get_pending_dse_requests():
    """Получить список заявок ДСЕ на проверку"""
    data = load_data(DATA_FILE)
    if not isinstance(data, dict):
        return []

    changed, _ = _cleanup_archived_requests(data)
    if changed:
        save_data(data, DATA_FILE)

    pending = _ensure_dict(data.get(PENDING_DSE_REQUESTS_KEY))
    requests = []
    for req_id, record in pending.items():
        item = record.copy()
        item['id'] = int(req_id) if str(req_id).isdigit() else req_id
        requests.append(item)

    requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return requests


def approve_pending_dse_request(request_id: int, approver_id: str = None):
    """Утвердить заявку ДСЕ и перенести в основную базу"""
    data = load_data(DATA_FILE)
    if not isinstance(data, dict):
        return None

    pending = _ensure_dict(data.get(PENDING_DSE_REQUESTS_KEY))
    req_key = str(request_id)
    if req_key not in pending:
        return None

    record = pending.pop(req_key)
    user_id = str(record.get('user_id', ''))
    if user_id not in data or not isinstance(data.get(user_id), list):
        data[user_id] = []

    record_copy = record.copy()
    record_copy.pop('status', None)
    record_copy.pop('created_at', None)
    record_copy.pop('archived_at', None)
    record_copy.pop('rejected_by', None)
    record_copy['approved_at'] = datetime.now().isoformat()
    if approver_id is not None:
        record_copy['approved_by'] = str(approver_id)

    if not record_copy.get('datetime'):
        record_copy['datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    data[user_id].append(record_copy)
    data[PENDING_DSE_REQUESTS_KEY] = pending
    save_data(data, DATA_FILE)

    return record_copy


def reject_pending_dse_request(request_id: int, approver_id: str = None):
    """Отклонить заявку ДСЕ и переместить в архив"""
    data = load_data(DATA_FILE)
    if not isinstance(data, dict):
        return None

    pending = _ensure_dict(data.get(PENDING_DSE_REQUESTS_KEY))
    req_key = str(request_id)
    if req_key not in pending:
        return None

    record = pending.pop(req_key)
    archived = _ensure_dict(data.get(ARCHIVED_DSE_REQUESTS_KEY))

    record_copy = record.copy()
    record_copy['status'] = 'rejected'
    record_copy['archived_at'] = datetime.now().isoformat()
    if approver_id is not None:
        record_copy['rejected_by'] = str(approver_id)

    archived[req_key] = record_copy
    data[PENDING_DSE_REQUESTS_KEY] = pending
    data[ARCHIVED_DSE_REQUESTS_KEY] = archived

    _cleanup_archived_requests(data)
    save_data(data, DATA_FILE)

    return record_copy


def find_archived_dse_matches(dse: str, dse_name: str):
    """Найти архивные отклонённые заявки по совпадению ДСЕ и наименования"""
    data = load_data(DATA_FILE)
    if not isinstance(data, dict):
        return []

    changed, archived = _cleanup_archived_requests(data)
    if changed:
        save_data(data, DATA_FILE)

    target_dse = _normalize_text(dse)
    target_name = _normalize_text(dse_name)
    if not target_dse and not target_name:
        return []

    matches = []
    for req_id, record in archived.items():
        if _normalize_text(record.get('dse')) == target_dse and _normalize_text(record.get('dse_name')) == target_name:
            item = record.copy()
            item['id'] = int(req_id) if str(req_id).isdigit() else req_id
            matches.append(item)

    matches.sort(key=lambda x: x.get('archived_at', ''), reverse=True)
    return matches


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