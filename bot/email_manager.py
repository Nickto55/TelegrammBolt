"""
Менеджер email адресов для отправки отчетов и заявок
Сохраняет историю отправок, частоту использования
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

EMAIL_HISTORY_FILE = "email_history.json"


def load_email_history() -> Dict:
    """Загружает историю email отправок"""
    if not os.path.exists(EMAIL_HISTORY_FILE):
        return {}
    
    try:
        with open(EMAIL_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Ошибка загрузки истории email: {e}")
        return {}


def save_email_history(history: Dict) -> bool:
    """Сохраняет историю email отправок"""
    try:
        with open(EMAIL_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️  Ошибка сохранения истории email: {e}")
        return False


def add_email_to_history(user_id: str, email: str, email_type: str = "export", dse_number: Optional[str] = None) -> None:
    """
    Добавляет email в историю пользователя
    
    Args:
        user_id: ID пользователя Telegram
        email: Email адрес
        email_type: Тип отправки - "export" (выгрузка) или "application" (заявка)
        dse_number: Номер ДСЕ (только для заявок)
    """
    history = load_email_history()
    
    if user_id not in history:
        history[user_id] = {}
    
    email_lower = email.lower().strip()
    
    if email_lower not in history[user_id]:
        history[user_id][email_lower] = {
            "email": email,  # Оригинальный формат написания
            "count": 0,
            "last_used": None,
            "first_used": None,
            "types": {
                "export": 0,
                "application": 0
            },
            "dse_numbers": []  # Список номеров ДСЕ для которых отправлялись заявки
        }
    
    # Обновляем статистику
    history[user_id][email_lower]["count"] += 1
    history[user_id][email_lower]["last_used"] = datetime.now().isoformat()
    
    if history[user_id][email_lower]["first_used"] is None:
        history[user_id][email_lower]["first_used"] = datetime.now().isoformat()
    
    # Обновляем счетчик по типу отправки
    if email_type in history[user_id][email_lower]["types"]:
        history[user_id][email_lower]["types"][email_type] += 1
    
    # Добавляем номер ДСЕ если это заявка
    if email_type == "application" and dse_number:
        if dse_number not in history[user_id][email_lower]["dse_numbers"]:
            history[user_id][email_lower]["dse_numbers"].append(dse_number)
    
    save_email_history(history)


def get_user_emails(user_id: str, limit: int = 10) -> List[Dict]:
    """
    Получает список email адресов пользователя, отсортированных по количеству отправок
    
    Args:
        user_id: ID пользователя Telegram
        limit: Максимальное количество возвращаемых адресов
    
    Returns:
        Список словарей с информацией об email адресах
    """
    history = load_email_history()
    
    if user_id not in history:
        return []
    
    emails = []
    for email_key, data in history[user_id].items():
        emails.append({
            "email": data["email"],
            "count": data["count"],
            "last_used": data["last_used"],
            "first_used": data["first_used"],
            "types": data["types"],
            "dse_numbers": data.get("dse_numbers", [])
        })
    
    # Сортируем по количеству использований (убывание)
    emails.sort(key=lambda x: x["count"], reverse=True)
    
    return emails[:limit]


def get_formatted_emails_list(user_id: str, limit: int = 5) -> str:
    """
    Возвращает отформатированный текст со списком email адресов пользователя
    
    Args:
        user_id: ID пользователя Telegram
        limit: Максимальное количество адресов в списке
    
    Returns:
        Отформатированная строка со списком
    """
    emails = get_user_emails(user_id, limit)
    
    if not emails:
        return "У вас пока нет сохраненных email адресов."
    
    text = "📧 Ваши сохраненные email адреса:\n\n"
    
    for i, email_data in enumerate(emails, 1):
        email = email_data["email"]
        count = email_data["count"]
        
        # Иконки в зависимости от количества использований
        if count >= 10:
            icon = "⭐"
        elif count >= 5:
            icon = "🔥"
        else:
            icon = "📌"
        
        text += f"{icon} {i}. {email}\n"
        text += f"   └ Использован: {count} раз\n"
        
        # Показываем типы отправок
        types_info = []
        if email_data["types"]["export"] > 0:
            types_info.append(f"выгрузки: {email_data['types']['export']}")
        if email_data["types"]["application"] > 0:
            types_info.append(f"заявки: {email_data['types']['application']}")
        
        if types_info:
            text += f"   └ {', '.join(types_info)}\n"
        
        text += "\n"
    
    return text.strip()


def remove_email_from_history(user_id: str, email: str) -> bool:
    """
    Удаляет email из истории пользователя
    
    Args:
        user_id: ID пользователя Telegram
        email: Email адрес для удаления
    
    Returns:
        True если email был удален, False если не найден
    """
    history = load_email_history()
    
    if user_id not in history:
        return False
    
    email_lower = email.lower().strip()
    
    if email_lower in history[user_id]:
        del history[user_id][email_lower]
        save_email_history(history)
        return True
    
    return False


def clear_user_email_history(user_id: str) -> bool:
    """
    Очищает всю историю email адресов пользователя
    
    Args:
        user_id: ID пользователя Telegram
    
    Returns:
        True если история была очищена
    """
    history = load_email_history()
    
    if user_id in history:
        history[user_id] = {}
        save_email_history(history)
    
    return True


def get_email_suggestions(user_id: str, email_type: str = "export", limit: int = 3) -> List[str]:
    """
    Получает список предложений email адресов для конкретного типа отправки
    
    Args:
        user_id: ID пользователя Telegram
        email_type: Тип отправки - "export" или "application"
        limit: Количество предложений
    
    Returns:
        Список email адресов
    """
    history = load_email_history()
    
    if user_id not in history:
        return []
    
    # Собираем email, отфильтрованные по типу использования
    emails_with_score = []
    
    for email_key, data in history[user_id].items():
        # Вычисляем "релевантность" для данного типа
        type_count = data["types"].get(email_type, 0)
        total_count = data["count"]
        
        # Чем больше использовался для данного типа - тем выше приоритет
        score = (type_count * 2) + total_count
        
        if score > 0:
            emails_with_score.append((data["email"], score))
    
    # Сортируем по релевантности
    emails_with_score.sort(key=lambda x: x[1], reverse=True)
    
    # Возвращаем только email адреса
    return [email for email, score in emails_with_score[:limit]]


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Проверяет корректность email адреса
    
    Args:
        email: Email адрес для проверки
    
    Returns:
        Tuple (is_valid, error_message)
    """
    email = email.strip()
    
    # Базовая проверка формата
    if not email or '@' not in email:
        return False, "Email должен содержать символ @"
    
    parts = email.split('@')
    
    if len(parts) != 2:
        return False, "Некорректный формат email"
    
    local_part, domain = parts
    
    if not local_part or not domain:
        return False, "Email не может начинаться или заканчиваться на @"
    
    if '.' not in domain:
        return False, "Домен должен содержать точку"
    
    # Проверка на недопустимые символы (базовая)
    forbidden_chars = [' ', ',', ';', ':', '!', '?', '\\', '/', '[', ']', '(', ')']
    for char in forbidden_chars:
        if char in email:
            return False, f"Email содержит недопустимый символ: {char}"
    
    return True, ""


def get_statistics(user_id: str) -> Dict:
    """
    Получает статистику использования email для пользователя
    
    Args:
        user_id: ID пользователя Telegram
    
    Returns:
        Словарь со статистикой
    """
    history = load_email_history()
    
    if user_id not in history:
        return {
            "total_emails": 0,
            "total_sends": 0,
            "export_sends": 0,
            "application_sends": 0,
            "most_used_email": None,
            "most_used_count": 0
        }
    
    total_emails = len(history[user_id])
    total_sends = 0
    export_sends = 0
    application_sends = 0
    most_used_email = None
    most_used_count = 0
    
    for email_key, data in history[user_id].items():
        total_sends += data["count"]
        export_sends += data["types"].get("export", 0)
        application_sends += data["types"].get("application", 0)
        
        if data["count"] > most_used_count:
            most_used_count = data["count"]
            most_used_email = data["email"]
    
    return {
        "total_emails": total_emails,
        "total_sends": total_sends,
        "export_sends": export_sends,
        "application_sends": application_sends,
        "most_used_email": most_used_email,
        "most_used_count": most_used_count
    }


def parse_multiple_emails(email_string: str) -> List[str]:
    """
    Парсит строку с несколькими email адресами
    Поддерживает разделители: запятая, точка с запятой, пробел
    
    Args:
        email_string: Строка с одним или несколькими email адресами
    
    Returns:
        Список отдельных email адресов
    """
    # Заменяем точку с запятой и переводы строк на запятую
    email_string = email_string.replace(';', ',').replace('\n', ',')
    
    # Разбиваем по запятым
    emails = []
    for email in email_string.split(','):
        email = email.strip()
        if email:
            emails.append(email)
    
    return emails


def validate_multiple_emails(email_string: str) -> Tuple[bool, str, List[str]]:
    """
    Проверяет строку с несколькими email адресами
    
    Args:
        email_string: Строка с email адресами
    
    Returns:
        Tuple (is_valid, error_message, valid_emails)
    """
    emails = parse_multiple_emails(email_string)
    
    if not emails:
        return False, "Не указано ни одного email адреса", []
    
    valid_emails = []
    invalid_emails = []
    
    for email in emails:
        is_valid, error_msg = validate_email(email)
        if is_valid:
            valid_emails.append(email)
        else:
            invalid_emails.append(f"{email} ({error_msg})")
    
    if not valid_emails:
        return False, f"Все адреса некорректны:\n" + "\n".join(invalid_emails), []
    
    if invalid_emails:
        warning = f"⚠️ Некоторые адреса пропущены:\n" + "\n".join(invalid_emails)
        return True, warning, valid_emails
    
    return True, "", valid_emails


def format_email_list_for_display(emails: List[str]) -> str:
    """
    Форматирует список email для отображения пользователю
    
    Args:
        emails: Список email адресов
    
    Returns:
        Отформатированная строка
    """
    if not emails:
        return "Нет адресов"
    
    if len(emails) == 1:
        return emails[0]
    
    return "\n".join([f"  {i+1}. {email}" for i, email in enumerate(emails)])


def send_dse_report_email(recipient_email: str, dse_data: List[Dict], subject: str = "Новая заявка ДСЕ") -> bool:
    """
    Отправить PDF отчёт ДСЕ на email
    
    Args:
        recipient_email: Email получателя
        dse_data: Список данных ДСЕ
        subject: Тема письма
    
    Returns:
        True если успешно, False при ошибке
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    import tempfile
    import os
    from datetime import datetime
    
    try:
        from config.config import SMTP_SETTINGS, is_smtp_configured
        from bot.pdf_generator import create_dse_pdf_report
        
        if not is_smtp_configured():
            print("❌ SMTP не настроен")
            return False
        
        # Создаём PDF
        if not dse_data or len(dse_data) == 0:
            print("❌ Нет данных для создания PDF")
            return False
        
        record = dse_data[0]
        pdf_filename = create_dse_pdf_report(record)
        
        if not pdf_filename or not os.path.exists(pdf_filename):
            print("❌ Ошибка создания PDF для email")
            return False
        
        # Настройки SMTP
        smtp_server = SMTP_SETTINGS["SMTP_SERVER"]
        smtp_port = SMTP_SETTINGS["SMTP_PORT"]
        smtp_user = SMTP_SETTINGS["SMTP_USER"]
        smtp_password = SMTP_SETTINGS["SMTP_PASSWORD"]
        
        # Создаём сообщение
        msg = MIMEMultipart()
        msg['From'] = f"{SMTP_SETTINGS['FROM_NAME']} <{smtp_user}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Тело письма
        body = (
            f"Здравствуйте!\n\n"
            f"Создана новая заявка ДСЕ:\n\n"
            f"ДСЕ: {record.get('dse', 'N/A')}\n"
            f"Тип проблемы: {record.get('problem_type', 'N/A')}\n"
            f"РЦ: {record.get('rc', 'N/A')}\n"
            f"Дата: {record.get('datetime', 'N/A')}\n\n"
            f"PDF отчёт прикреплён к письму.\n\n"
            f"С уважением,\n{SMTP_SETTINGS['FROM_NAME']}"
        )
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Прикрепляем PDF
        with open(pdf_filename, "rb") as attachment:
            part = MIMEBase('application', 'pdf')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        pdf_name = f"DSE_{record.get('dse', 'report')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        part.add_header('Content-Disposition', f'attachment; filename="{pdf_name}"')
        msg.attach(part)
        
        # Отправляем
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        server.quit()
        
        # Удаляем временный PDF
        try:
            os.remove(pdf_filename)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")
        import traceback
        traceback.print_exc()
        return False
