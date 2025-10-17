import time
from datetime import datetime as dt
import subprocess
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import mimetypes

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import load_data, save_data, PROBLEM_TYPES, RC_TYPES, DATA_FILE, PHOTOS_DIR
from dse_manager import get_all_dse_records, search_dse_records, get_unique_dse_values
from user_manager import (register_user, get_user_role, has_permission, set_user_role, ROLES, get_all_users,
                         set_user_nickname, remove_user_nickname, get_user_nickname, get_user_display_name,
                         check_nickname_exists, get_all_nicknames)
import os
print(str(os.urandom(32)))
# Глобальные переменные
user_states = {}
admin_states = {}  # Для отслеживания состояния админских операций
dse_view_states = {}  # Для отслеживания состояния просмотра ДСЕ


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    user = update.effective_user
    user_id = str(user.id)

    # Регистрируем пользователя
    user_data = register_user(
        user_id,
        user.username,
        user.first_name,
        user.last_name
    )

    print(f"📥 {user.first_name} ({get_user_role(user_id)}): /start")

    # Проверяем права доступа
    if has_permission(user_id, 'view_main_menu'):
        # Инициализируем данные пользователя для формы, включая фото
        user_states[user_id] = {
            'application': '',  # Будет содержать "started" когда заявка начата
            'dse': '',
            'problem_type': '',
            'description': '',
            'rc': '',  # Рабочий центр
            'photo_file_id': None  # Новое поле для фото
        }
        await show_main_menu(update, user_id)
    else:
        # Пользователь без прав
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ У вас нет прав для использования бота.\nОбратитесь к администратору."
            )
        else:
            await update.message.reply_text(
                "❌ У вас нет прав для использования бота.\nОбратитесь к администратору."
            )


async def show_application_menu(update: Update, user_id: str) -> None:
    """Показать меню заполнения заявки"""
    # Убедимся, что поле photo_file_id существует у уже существующих пользователей
    if user_id not in user_states:
        user_states[user_id] = {
            'application': '',
            'dse': '',
            'problem_type': '',
            'description': '',
            'rc': '',
            'photo_file_id': None
        }
    else:
        if 'photo_file_id' not in user_states[user_id]:
            user_states[user_id]['photo_file_id'] = None
        if 'rc' not in user_states[user_id]:
            user_states[user_id]['rc'] = ''

    user_data = user_states.get(user_id, {
        'application': '',
        'dse': '',
        'problem_type': '',
        'description': '',
        'time': str(dt.now()),
        'photo_file_id': None
    })

    # Создаем кнопки с индикаторами заполненности для каждого поля
    dse_text = f"ДСЕ ✅" if user_data['dse'] else "ДСЕ"
    problem_text = f"Вид проблемы ✅" if user_data['problem_type'] else "Вид проблемы"
    rc_text = f"РЦ ✅" if user_data['rc'] else "РЦ"
    desc_text = f"Описание вопроса ✅" if user_data['description'] else "Описание вопроса"
    photo_text = f"Фото ✅" if user_data['photo_file_id'] else "Фото (необязательно)"

    # Кнопки для заполнения полей
    keyboard = [
        [InlineKeyboardButton(dse_text, callback_data='set_dse')],
        [InlineKeyboardButton(problem_text, callback_data='set_problem')],
        [InlineKeyboardButton(rc_text, callback_data='set_rc')],
        [InlineKeyboardButton(desc_text, callback_data='set_description')],
        [InlineKeyboardButton(photo_text, callback_data='set_photo')],  # Новая кнопка
    ]

    # Кнопки отправки и возврата, если основные поля заполнены (теперь включая RC)
    if user_data['dse'] and user_data['problem_type'] and user_data['rc'] and user_data['description']:
        keyboard.append([InlineKeyboardButton("📤 Отправить", callback_data='send')])
        keyboard.append([InlineKeyboardButton("� Отправить по почте", callback_data='send_application_email')])
        keyboard.append([InlineKeyboardButton("�🔄 Изменить", callback_data='edit_application')])

    # Кнопка возврата в главное меню
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = "📝 Заполните заявку:\n\n"
    welcome_text += (
        f"• {dse_text}\n"
        f"• {problem_text}\n"
        f"• {rc_text}\n"
        f"• {desc_text}\n"
        f"• {photo_text}\n\n"
    )
    if user_data['dse'] and user_data['problem_type'] and user_data['rc'] and user_data['description']:
        welcome_text += "После заполнения появятся кнопки отправки."

    if update.callback_query:
        await update.callback_query.edit_message_text(text=welcome_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)


async def show_main_menu(update: Update, user_id: str) -> None:
    """Показать главное меню с кнопками"""
    # Инициализируем данные пользователя для формы, включая фото
    if user_id not in user_states:
        user_states[user_id] = {
            'application': '',
            'dse': '',
            'problem_type': '',
            'description': '',
            'rc': '',
            'photo_file_id': None  # Инициализируем поле для фото
        }
    else:
        # Убедимся, что поле photo_file_id и rc существует у уже существующих пользователей
        if 'photo_file_id' not in user_states[user_id]:
            user_states[user_id]['photo_file_id'] = None
        if 'rc' not in user_states[user_id]:
            user_states[user_id]['rc'] = ''


    user_data = user_states.get(user_id, {'application': '', 'dse': '', 'problem_type': '', 'description': '',
                                          'rc': '', 'photo_file_id': None})
    role = get_user_role(user_id)

    keyboard = []

    # Заменяем отдельные кнопки полей на одну кнопку "Заявка"
    if has_permission(user_id, 'use_form'):
        # Показываем кнопку "Заявка" с индикатором, если заявка частично или полностью заполнена
        app_status = user_data.get('application', '')
        dse_filled = user_data.get('dse', '')
        problem_filled = user_data.get('problem_type', '')
        rc_filled = user_data.get('rc', '')
        desc_filled = user_data.get('description', '')
        photo_filled = user_data.get('photo_file_id', None)

        if app_status == 'started' or any([dse_filled, problem_filled, rc_filled, desc_filled, photo_filled]):
            app_text = "📝 Заявка ⚠️"  # ⚠️ если начата, но не завершена
            if dse_filled and problem_filled and rc_filled and desc_filled:
                app_text = "📝 Заявка ✅"  # ✅ если полностью заполнена
        else:
            app_text = "📝 Заявка"

        keyboard.append([InlineKeyboardButton(app_text, callback_data='open_application')])

    # === КНОПКА 6: "📋 Список ДСЕ" ===
    if has_permission(user_id, 'view_dse_list'):
        keyboard.append([InlineKeyboardButton("📋 Список ДСЕ", callback_data='view_dse_list')])

    # === КНОПКА 7: "👀 Отслеживание ДСЕ" ===
    if has_permission(user_id, 'watch_dse'):  # Используем новое право
        keyboard.append([InlineKeyboardButton("👀 Отслеживание ДСЕ", callback_data='watch_dse_menu')])

    # === КНОПКА 8: "💬 Чат по ДСЕ" ===
    if has_permission(user_id, 'chat_dse'):
        keyboard.append([InlineKeyboardButton("💬 Чат по ДСЕ", callback_data='chat_dse_menu')])

    # === КНОПКА 9: "� PDF Отчет" ===
    if has_permission(user_id, 'pdf_export'):
        keyboard.append([InlineKeyboardButton("📄 PDF Отчет", callback_data='pdf_export_menu')])

    # === КНОПКА 10: "�🔧 Управление пользователями" ===
    if role == 'admin':
        keyboard.append([InlineKeyboardButton("🔧 Управление пользователями", callback_data='admin_users')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    role_text = ROLES.get(role, 'Пользователь')
    welcome_text = f"👤 Роль: {role_text}\n\n"

    if has_permission(user_id, 'use_form'):
        welcome_text += "Выберите действие:\n"
    else:
        welcome_text += "У вас ограниченный доступ к функциям бота."

    if update.callback_query:
        await update.callback_query.edit_message_text(text=welcome_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)


# === ФУНКЦИИ ПРОСМОТРА ДСЕ ===

async def show_dse_list_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать меню просмотра ДСЕ"""
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск по ДСЕ", callback_data='dse_search_interactive')],
        [InlineKeyboardButton("📋 Все записи", callback_data='dse_view_all')],
        [InlineKeyboardButton("🔎 Поиск по типу проблемы", callback_data='dse_search_type')],
        [InlineKeyboardButton("📊 Статистика", callback_data='dse_statistics')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="📋 Меню просмотра ДСЕ:",
        reply_markup=reply_markup
    )


async def show_all_dse_records(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0) -> None:
    """Показать все записи ДСЕ с пагинацией"""
    records = get_all_dse_records()
    records_per_page = 5
    total_pages = (len(records) + records_per_page - 1) // records_per_page if records else 1

    if not records:
        await update.callback_query.edit_message_text("📋 Нет записей ДСЕ.")
        return

    # Получаем записи для текущей страницы
    start_idx = page * records_per_page
    end_idx = start_idx + records_per_page
    page_records = records[start_idx:end_idx]

    text = f"📋 Все записи ДСЕ (страница {page + 1}/{total_pages}):\n\n"

    for i, record in enumerate(page_records, start=start_idx + 1):
        text += f"{i}. ДСЕ: {record.get('dse', 'Не указано')}\n"
        text += f"   Тип: {record.get('problem_type', 'Не указано')}\n"
        text += f"   РЦ: {record.get('rc', 'Не указано')}\n"
        text += f"   Описание: {record.get('description', 'Не указано')[:50]}...\n"
        # Проверяем, есть ли фото
        if record.get('photo_file_id'):
            text += f"   📸 Фото: Прикреплено\n"
        text += f"   📅 Дата: {record.get('datetime', 'Не указано')}\n"
        user_id = record.get('user_id', 'Неизвестно')
        user_display = get_user_display_name(user_id) if user_id != 'Неизвестно' else 'Неизвестно'
        text += f"   👤 Пользователь: {user_display}\n\n"

    # Создаем кнопки навигации
    nav_buttons = []

    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'dse_view_all_{page - 1}'))

    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f'dse_view_all_{page + 1}'))

    # --- ИСПРАВЛЕННЫЙ БЛОК ---
    # Кнопка возврата в меню
    menu_button = InlineKeyboardButton("↩️ Меню", callback_data='view_dse_list')
    # Добавляем кнопку меню к навигационным кнопкам, если они есть, или создаем новую строку
    if nav_buttons:
        nav_buttons.append(menu_button) # Добавляем кнопку меню в ту же строку, что и Назад/Далее
    else:
        nav_buttons = [menu_button] # Если Назад/Далее нет, создаем отдельную строку для меню

    # Формируем итоговую клавиатуру
    keyboard = []
    # Добавляем кнопки записей (если есть)
    # (предполагается, что они уже добавлены в keyboard выше в функции)
    # Например:
    # for record_buttons_row in record_buttons: # record_buttons - это список списков кнопок для записей
    #     keyboard.append(record_buttons_row)

    # Добавляем строку с навигационными кнопками (и кнопкой меню)
    if nav_buttons: # Проверяем, есть ли что-то в nav_buttons
        keyboard.append(nav_buttons) # Добавляем целую строку кнопок

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


async def start_interactive_dse_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать интерактивный поиск по ДСЕ"""
    user_id = str(update.callback_query.from_user.id)

    # Инициализируем состояние поиска
    dse_view_states[user_id] = {
        'searching_dse': True,
        'current_search': '',
        'search_results': []
    }

    # Получаем все уникальные ДСЕ для начального списка
    all_dse = get_unique_dse_values()
    dse_view_states[user_id]['all_dse'] = all_dse

    await show_dse_search_results(update, context, user_id)


async def show_dse_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Показать результаты поиска ДСЕ"""
    search_state = dse_view_states.get(user_id, {})
    current_search = search_state.get('current_search', '')
    all_dse = search_state.get('all_dse', [])

    # Фильтруем ДСЕ по текущему поисковому запросу
    if current_search:
        filtered_dse = [dse for dse in all_dse if current_search.lower() in dse.lower()]
    else:
        filtered_dse = all_dse

    # Сохраняем результаты
    search_state['search_results'] = filtered_dse

    # Создаем текст сообщения
    if current_search:
        text = f"🔍 Поиск по ДСЕ: '{current_search}'\n\n"
    else:
        text = "🔍 Поиск по ДСЕ (введите текст для фильтрации):\n\n"

    if filtered_dse:
        text += f"Найдено: {len(filtered_dse)}\n\n"
        # Показываем первые 20 результатов
        for i, dse in enumerate(filtered_dse[:20]):
            text += f"{i + 1}. {dse.upper()}\n"

        if len(filtered_dse) > 20:
            text += f"\n... и еще {len(filtered_dse) - 20} записей"
    else:
        text += "❌ Ничего не найдено"

    # Создаем кнопки
    keyboard = []

    # Кнопки для первых 10 ДСЕ (если есть результаты)
    for i, dse in enumerate(filtered_dse[:10]):
        callback_data = f"dse_select_{i}"
        keyboard.append([InlineKeyboardButton(dse.upper(), callback_data=callback_data)])

    # Кнопки управления
    nav_buttons = []
    if current_search:
        nav_buttons.append(InlineKeyboardButton("⌫ Очистить", callback_data='dse_search_clear'))

    nav_buttons.append(InlineKeyboardButton("↩️ Назад   ", callback_data='view_dse_list'))
    keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup)


async def handle_dse_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать ввод текста для поиска ДСЕ"""
    user_id = str(update.message.from_user.id)
    search_text = update.message.text

    # Обновляем поисковый запрос
    if user_id in dse_view_states:
        dse_view_states[user_id]['current_search'] = search_text
        await show_dse_search_results(update, context, user_id)


async def select_dse_from_search(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int) -> None:
    """Выбрать ДСЕ из результатов поиска"""
    user_id = str(update.callback_query.from_user.id)

    if user_id in dse_view_states:
        search_results = dse_view_states[user_id].get('search_results', [])
        if 0 <= index < len(search_results):
            selected_dse = search_results[index]

            # Очищаем состояние поиска
            del dse_view_states[user_id]

            # Показываем все записи по выбранному ДСЕ
            await show_records_for_dse(update, context, selected_dse)


async def show_records_for_dse(update: Update, context: ContextTypes.DEFAULT_TYPE, dse_value: str) -> None:
    """Показать все записи для конкретного ДСЕ"""
    # Ищем все записи с этим ДСЕ
    records = search_dse_records(dse_filter=dse_value)

    if not records:
        await update.callback_query.edit_message_text(f"❌ Нет записей для ДСЕ: {dse_value.upper()}")
        return

    # Создаем текст с деталями первой записи (или всех записей)
    text = f"📄 Записи для ДСЕ: {dse_value.upper()}\n\n"

    for i, record in enumerate(records[:5]):  # Показываем максимум 5 записей
        text += f"Запись #{i + 1}:\n"
        text += f"Тип проблемы: {record.get('problem_type', 'Не указано')}\n"
        text += f"РЦ: {record.get('rc', 'Не указано')}\n"
        text += f"Описание: {record.get('description', 'Нет описания')}\n"
        text += f"📅 Дата: {record.get('datetime', 'Не указано')}\n"
        # Добавляем информацию о пользователе
        user_id = record.get('user_id', 'Неизвестно')
        if user_id != 'Неизвестно':
            user_display = get_user_display_name(user_id)
            text += f"👤 Пользователь: {user_display}\n"

        # Проверяем, есть ли фото
        photo_file_id = record.get('photo_file_id')
        if photo_file_id:
            text += f"📸 Фото: Прикреплено\n"

            # Отправляем фото отдельным сообщением
            try:
                await context.bot.send_photo(
                    chat_id=update.callback_query.message.chat_id,
                    photo=photo_file_id,
                    caption=f"Фото для ДСЕ {dse_value.upper()}"
                )
            except Exception as e:
                print(f"Ошибка отправки фото: {e}")
                text += "❌ Ошибка при загрузке фото\n"

        text += "\n" + "=" * 30 + "\n\n"

    if len(records) > 5:
        text += f"\n... и еще {len(records) - 5} записей"

    # Кнопки управления
    keyboard = [
        [InlineKeyboardButton("↩️ Назад к поиску", callback_data='dse_search_interactive')],
        [InlineKeyboardButton("📋 Все записи    ", callback_data='dse_view_all')],
        [InlineKeyboardButton("⬅️ В меню        ", callback_data='view_dse_list')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


async def start_dse_search(update: Update, context: ContextTypes.DEFAULT_TYPE, search_type: str) -> None:
    """Начать поиск ДСЕ"""
    user_id = str(update.callback_query.from_user.id)

    if search_type == 'dse':
        dse_view_states[user_id] = {'searching_dse': True}
        await update.callback_query.edit_message_text("🔍 Введите ДСЕ для поиска:")
    elif search_type == 'type':
        dse_view_states[user_id] = {'searching_type': True}
        await update.callback_query.edit_message_text("🔎 Введите тип проблемы для поиска:")


async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, search_term: str,
                              search_type: str) -> None:
    """Показать результаты поиска"""
    if search_type == 'dse':
        records = search_dse_records(dse_filter=search_term)
        search_title = f"по ДСЕ '{search_term}'"
    else:  # type
        records = search_dse_records(problem_type_filter=search_term)
        search_title = f"по типу проблемы '{search_term}'"

    # Проверяем тип update для корректного ответа
    if update.callback_query:
        # Ответ через callback_query
        if not records:
            await update.callback_query.edit_message_text(f"❌ Ничего не найдено {search_title}.")
            return

        text = f"🔍 Результаты поиска {search_title}:\n\n"

        for i, record in enumerate(records[:10], 1):  # Ограничиваем 10 результатами
            text += f"{i}. ДСЕ: {record.get('dse', 'Не указано')}\n"
            text += f"   Тип: {record.get('problem_type', 'Не указано')}\n"
            text += f"   РЦ: {record.get('rc', 'Не указано')}\n"
            text += f"   Описание: {record.get('description', 'Не указано')[:50]}...\n"
            # Проверяем, есть ли фото
            if record.get('photo_file_id'):
                text += f"   📸 Фото: Прикреплено\n"
            text += f"   📅 Дата: {record.get('datetime', 'Не указано')}\n"
            text += "\n"

        if len(records) > 10:
            text += f"... и еще {len(records) - 10} записей"

        keyboard = [[InlineKeyboardButton("↩️ Назад", callback_data='view_dse_list')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    elif update.message:
        # Ответ через обычное сообщение
        if not records:
            await update.message.reply_text(f"❌ Ничего не найдено {search_title}.")
            return

        text = f"🔍 Результаты поиска {search_title}:\n\n"

        for i, record in enumerate(records[:10], 1):  # Ограничиваем 10 результатами
            text += f"{i}. ДСЕ: {record.get('dse', 'Не указано')}\n"
            text += f"   Тип: {record.get('problem_type', 'Не указано')}\n"
            text += f"   РЦ: {record.get('rc', 'Не указано')}\n"
            text += f"   Описание: {record.get('description', 'Не указано')[:50]}...\n"
            # Проверяем, есть ли фото
            if record.get('photo_file_id'):
                text += f"   📸 Фото: Прикреплено\n"
            text += f"   📅 Дата: {record.get('datetime', 'Не указано')}\n"
            text += "\n"

        if len(records) > 10:
            text += f"... и еще {len(records) - 10} записей"

        keyboard = [[InlineKeyboardButton("↩️ Назад", callback_data='view_dse_list')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text=text, reply_markup=reply_markup)


async def show_dse_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статистику по ДСЕ"""
    records = get_all_dse_records()

    if not records:
        await update.callback_query.edit_message_text("📊 Нет данных для статистики.")
        return

    # Статистика
    total_records = len(records)

    # Подсчет по типам проблем
    problem_counts = {}
    photo_count = 0
    for record in records:
        problem_type = record.get('problem_type', 'Не указано')
        problem_counts[problem_type] = problem_counts.get(problem_type, 0) + 1
        # Подсчет записей с фото
        if record.get('photo_file_id'):
            photo_count += 1

    # Подсчет уникальных ДСЕ
    unique_dse = len(set([r.get('dse', '') for r in records if r.get('dse', '')]))

    text = "📊 Статистика по ДСЕ:\n\n"
    text += f"Всего записей: {total_records}\n"
    text += f"Уникальных ДСЕ: {unique_dse}\n"
    text += f"Записей с фото: {photo_count}\n\n"
    text += "По типам проблем:\n"

    # Сортируем по количеству
    sorted_problems = sorted(problem_counts.items(), key=lambda x: x[1], reverse=True)

    for problem_type, count in sorted_problems[:10]:  # Показываем топ-10
        text += f"• {problem_type}: {count}\n"

    keyboard = [[InlineKeyboardButton("↩️ Назад", callback_data='view_dse_list')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


async def show_problem_types(update: Update, user_id: str) -> None:
    """Показать список типов проблем"""
    # Создаем кнопки
    keyboard = []
    for i in range(0, len(PROBLEM_TYPES), 3):  # 3 кнопки в строке
        row = []
        for j in range(i, min(i + 3, len(PROBLEM_TYPES))):
            row.append(InlineKeyboardButton(PROBLEM_TYPES[j], callback_data=f'problem_{j}'))
        keyboard.append(row)

    # Добавляем кнопку "Назад" (возвращаемся в меню заявки)
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_to_application')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="Выберите вид проблемы:",
        reply_markup=reply_markup
    )


async def show_rc_types(update: Update, user_id: str) -> None:
    """Показать список рабочих центров (РЦ)"""
    # Создаем кнопки
    keyboard = []
    for i in range(0, len(RC_TYPES), 2):  # 2 кнопки в строке
        row = []
        for j in range(i, min(i + 2, len(RC_TYPES))):
            row.append(InlineKeyboardButton(RC_TYPES[j], callback_data=f'rc_{j}'))
        keyboard.append(row)

    # Добавляем кнопку "Назад" (возвращаемся в меню заявки)
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_to_application')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="Выберите рабочий центр (РЦ):",
        reply_markup=reply_markup
    )


# === АДМИН ФУНКЦИИ ===

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать админское меню"""
    keyboard = [
        [InlineKeyboardButton("👥 Список пользователей      ", callback_data='admin_list_users')],
        [InlineKeyboardButton("✏️ Изменить роль пользователя", callback_data='admin_change_role_start')],
        [InlineKeyboardButton("🏷️ Управление кличками       ", callback_data='admin_manage_nicknames')],
        [InlineKeyboardButton("📊 Выгрузить данные          ", callback_data='admin_export_data')],
        [InlineKeyboardButton("📧 Тест SMTP                 ", callback_data='admin_test_smtp')],
        [InlineKeyboardButton("⬅️ Назад                     ", callback_data='back_to_main')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="🔧 Административное меню:",
        reply_markup=reply_markup
    )


async def show_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список пользователей"""
    users = get_all_users()

    if not users:
        await update.callback_query.edit_message_text("Пользователей нет.")
        return

    text = "👥 Список пользователей:\n\n"
    for user_id, user_data in users.items():
        role = user_data.get('role', 'user')
        role_text = ROLES.get(role, 'Пользователь')
        
        # Используем отображаемое имя (кличку или имя)
        display_name = get_user_display_name(user_id)
        username = user_data.get('username', '')
        
        if username:
            text += f"• {display_name} (@{username}) - {role_text}\n"
        else:
            text += f"• {display_name} - {role_text}\n"

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='admin_users')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


async def start_change_role_process(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: str) -> None:
    """Начать процесс изменения роли"""
    admin_states[admin_id] = {'changing_role': True}
    await update.callback_query.edit_message_text(
        "Введите ID пользователя, которому хотите изменить роль:"
    )


async def show_role_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: str) -> None:
    """Показать меню выбора ролей"""
    users = get_all_users()
    target_user = users.get(target_user_id, {})
    user_name = target_user.get('first_name', 'Пользователь')

    keyboard = []
    current_role = target_user.get('role', 'user')

    # Создаем кнопки для каждой роли
    for role_key, role_name in ROLES.items():
        if role_key == current_role:
            button_text = f"✅ {role_name}"
        else:
            button_text = role_name
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'set_role_{target_user_id}_{role_key}')])

    keyboard.append([InlineKeyboardButton("⬅️ Отмена", callback_data='admin_users')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Проверяем тип update
    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"Выберите новую роль для {user_name} (ID: {target_user_id}):",
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            f"Выберите новую роль для {user_name} (ID: {target_user_id}):",
            reply_markup=reply_markup
        )


# === ФУНКЦИИ ОТСЛЕЖИВАНИЯ ДСЕ ===

async def show_dse_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, action_callback_data_prefix: str,
                                  title: str = "Выберите ДСЕ") -> None:
    """
    Показывает меню выбора ДСЕ из списка кнопок.

    Args:
        update: Объект Update.
        context: Объект Context.
        action_callback_data_prefix: Префикс для callback_data кнопок (например, 'watch_select_dse_').
        title: Заголовок меню.
    """
    dse_list = get_unique_dse_values()

    if not dse_list:
        if update.callback_query:
            await update.callback_query.edit_message_text("📭 Нет доступных ДСЕ для выбора.")
        elif update.message:
            await update.message.reply_text("📭 Нет доступных ДСЕ для выбора.")
        return

    # Создаем кнопки для выбора ДСЕ
    keyboard = []
    for i, dse_value in enumerate(dse_list):
        # Создаем уникальный callback_data с индексом
        callback_data = f"{action_callback_data_prefix}{i}"
        # Ограничиваем длину текста кнопки
        button_text = dse_value.upper() if len(dse_value) <= 20 else dse_value[:17].upper() + "..."
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # Добавляем кнопку "Ввести вручную" и "Отмена"
    keyboard.append([InlineKeyboardButton("✍️ Ввести вручную", callback_data=f"{action_callback_data_prefix}manual")])
    keyboard.append(
        [InlineKeyboardButton("⬅️ Отмена", callback_data='back_to_main')])  # Или другой общий callback для отмены

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Сохраняем список для последующего использования по индексу
    user = update.effective_user
    user_id = str(user.id)
    user_states[user_id] = user_states.get(user_id, {})
    user_states[user_id]['temp_dse_list'] = dse_list

    if update.callback_query:
        await update.callback_query.edit_message_text(text=title, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text=title, reply_markup=reply_markup)


async def show_watched_dse_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать меню отслеживания ДСЕ."""
    user = update.effective_user
    user_id = str(user.id)

    # Проверяем права доступа
    if not has_permission(user_id, 'watch_dse'):
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
        elif update.message:
            await update.message.reply_text("❌ У вас нет прав для отслеживания ДСЕ.")
        return

    from dse_watcher import get_watched_dse_list
    watched_list = get_watched_dse_list(user_id)

    keyboard = [
        [InlineKeyboardButton("➕ Добавить ДСЕ", callback_data='watch_add_dse')],
        [InlineKeyboardButton("➖ Удалить ДСЕ", callback_data='watch_remove_dse')],
        [InlineKeyboardButton("📋 Список отслеживаемых", callback_data='watch_list_dse')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    menu_text = "👀 Меню отслеживания ДСЕ\n\n"
    menu_text += "Здесь вы можете настроить уведомления о появлении новых записей по определённым ДСЕ.\n"

    if update.callback_query:
        await update.callback_query.edit_message_text(text=menu_text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text=menu_text, reply_markup=reply_markup)


async def start_add_watched_dse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс добавления ДСЕ в список отслеживания."""
    user_id = str(update.callback_query.from_user.id)

    # Вместо прямого запроса ввода, показываем меню выбора
    await show_dse_selection_menu(
        update,
        context,
        action_callback_data_prefix='watch_select_dse_',
        title="➕ Выберите ДСЕ для отслеживания или введите вручную:"
    )
    # Устанавливаем состояние, если пользователь выберет "Ввести вручную"
    user_states[user_id]['adding_watched_dse_state'] = 'selecting_or_manual'


async def start_dse_chat_search_with_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс поиска чата по ДСЕ с выбором из списка."""
    # Проверяем права доступа
    user = update.callback_query.from_user
    user_id = str(user.id)
    # if has_permission(user_id, 'chat_dse'):
    #     await update.callback_query.edit_message_text("❌ У вас нет прав для чата по ДСЕ.")
    #     return

    await show_dse_selection_menu(
        update,
        context,
        action_callback_data_prefix='chat_select_dse_',
        title="🔍 Выберите ДСЕ для начала чата или введите вручную:"
    )
    # Устанавливаем состояние для обработки выбора
    user_states[user_id] = user_states.get(user_id, {})
    user_states[user_id]['dse_chat_state'] = 'selecting_or_manual'


async def start_remove_watched_dse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс удаления ДСЕ из списка отслеживания."""
    user = update.callback_query.from_user
    user_id = str(user.id)

    from dse_watcher import get_watched_dse_list
    watched_list = get_watched_dse_list(user_id)

    if not watched_list:
        await update.callback_query.edit_message_text("📭 Ваш список отслеживаемых ДСЕ пуст.")
        return

    # Создаем кнопки для выбора ДСЕ для удаления
    keyboard = []
    for i, dse_value in enumerate(watched_list):
        # Создаем уникальный callback_data с индексом
        callback_data = f"watch_rm_idx_{i}"
        keyboard.append([InlineKeyboardButton(dse_value.upper(), callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("⬅️ Отмена", callback_data='watch_dse_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Сохраняем список для последующего использования по индексу
    user_states[user_id] = user_states.get(user_id, {})
    user_states[user_id]['temp_watched_list'] = watched_list

    await update.callback_query.edit_message_text("➖ Выберите ДСЕ для удаления из списка отслеживания:",
                                                  reply_markup=reply_markup)


async def show_watched_dse_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список отслеживаемых ДСЕ пользователя."""
    user = update.callback_query.from_user
    user_id = str(user.id)

    from dse_watcher import get_watched_dse_list
    watched_list = get_watched_dse_list(user_id)  # Получаем список нормализованных значений

    if not watched_list:
        text = "📭 Ваш список отслеживаемых ДСЕ пуст.\n\n"
        text += "Нажмите '➕ Добавить ДСЕ' в меню отслеживания, чтобы начать."
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='watch_dse_menu')]]
    else:
        text = "📋 Список отслеживаемых ДСЕ:\n\n"
        # Отображаем в верхнем регистре для удобства чтения
        for i, dse_value in enumerate(watched_list, 1):
            text += f"{i}. {dse_value.upper()}\n"
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='watch_dse_menu')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


# === ФУНКЦИИ ЭКСПОРТА ДАННЫХ ===

async def start_data_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать процесс экспорта данных"""
    user_id = str(update.callback_query.from_user.id)
    
    # Сохраняем состояние экспорта
    if user_id not in admin_states:
        admin_states[user_id] = {}
    admin_states[user_id]['exporting_data'] = True
    
    await update.callback_query.edit_message_text(
        "📊 Начинается генерация файла с данными...\n"
        "Пожалуйста, подождите."
    )
    
    try:
        # Запускаем скрипт genereteTabl.py
        process = await asyncio.create_subprocess_exec(
            'python', 'genereteTabl.py',
            cwd=os.getcwd(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Скрипт выполнился успешно
            admin_states[user_id]['export_completed'] = True
            admin_states[user_id]['export_file'] = 'RezultBot.xlsx'
            await show_export_delivery_options(update, context)
        else:
            # Ошибка выполнения
            error_msg = stderr.decode() if stderr else "Неизвестная ошибка"
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при генерации файла:\n{error_msg}\n\n"
                f"Код возврата: {process.returncode}"
            )
            # Очищаем состояние
            if user_id in admin_states:
                admin_states[user_id].pop('exporting_data', None)
                
    except Exception as e:
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при выполнении скрипта: {str(e)}"
        )
        # Очищаем состояние
        if user_id in admin_states:
            admin_states[user_id].pop('exporting_data', None)


async def show_export_delivery_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать варианты доставки экспортированного файла"""
    keyboard = [
        [InlineKeyboardButton("💬 Отправить в чат", callback_data='export_send_chat')],
        [InlineKeyboardButton("📧 Отправить Excel по почте", callback_data='export_send_email_excel')],
        [InlineKeyboardButton("📧 Отправить текстом по почте", callback_data='export_send_email_text')],
        [InlineKeyboardButton("⬅️ Отмена", callback_data='admin_users')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "✅ Файл с данными успешно создан!\n\n"
        "Выберите способ получения отчёта:",
        reply_markup=reply_markup
    )


async def send_file_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправить файл в чат"""
    user_id = str(update.callback_query.from_user.id)
    
    try:
        file_path = admin_states.get(user_id, {}).get('export_file', 'RezultBot.xlsx')
        
        if os.path.exists(file_path):
            # Отправляем файл
            with open(file_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=update.callback_query.message.chat_id,
                    document=file,
                    filename=f"Выгрузка_данных_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    caption=f"📊 Выгрузка данных ДСЕ\n"
                           f"📅 Дата создания: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            await update.callback_query.edit_message_text("✅ Файл успешно отправлен в чат!")
        else:
            await update.callback_query.edit_message_text("❌ Файл не найден!")
            
    except Exception as e:
        await update.callback_query.edit_message_text(f"❌ Ошибка отправки файла: {str(e)}")
    
    finally:
        # Очищаем состояние
        if user_id in admin_states:
            admin_states[user_id].pop('exporting_data', None)
            admin_states[user_id].pop('export_completed', None)
            admin_states[user_id].pop('export_file', None)


async def request_email_address(update: Update, context: ContextTypes.DEFAULT_TYPE, format_type: str = "excel") -> None:
    """Запросить email адрес для отправки отчёта в выбранном формате"""
    user_id = str(update.callback_query.from_user.id)
    from config import SMTP_SETTINGS, is_smtp_configured
    from email_manager import get_email_suggestions, get_formatted_emails_list
    
    if not is_smtp_configured():
        await update.callback_query.edit_message_text(
            "❌ SMTP не настроен!\n\n"
            "Для отправки файлов по email необходимо:\n"
            "1. Настроить параметры в файле smtp_config.json\n"
            "2. Указать корректный email и пароль приложения\n\n"
            "Текущие настройки:\n"
            f"• Сервер: {SMTP_SETTINGS.get('SMTP_SERVER', 'не указан')}\n"
            f"• Порт: {SMTP_SETTINGS.get('SMTP_PORT', 'не указан')}\n"
            f"• Email: {SMTP_SETTINGS.get('SMTP_USER', 'не указан')}"
        )
        return
    
    # Устанавливаем состояние ожидания email и формат
    admin_states[user_id]['waiting_for_email'] = True
    admin_states[user_id]['email_format'] = format_type
    
    # Получаем предложения email адресов
    suggestions = get_email_suggestions(user_id, email_type="export", limit=5)
    
    message = f"📧 Введите email адрес для отправки отчёта (формат: {format_type}):\n\n"
    
    # Показываем историю использованных email
    if suggestions:
        message += "💡 Ваши часто используемые адреса:\n"
        for i, email in enumerate(suggestions, 1):
            message += f"{i}. {email}\n"
        message += "\n"
    
    message += "Введите email адрес или выберите из списка выше.\n"
    message += "💡 Можно указать несколько адресов через запятую.\n\n"
    message += f"ℹ️ Настроен отправитель: {SMTP_SETTINGS['SMTP_USER']}"
    
    await update.callback_query.edit_message_text(message)


async def send_file_by_email(update: Update, context: ContextTypes.DEFAULT_TYPE, email: str) -> None:
    """Отправить отчёт по электронной почте в выбранном формате (поддержка нескольких адресов)"""
    user_id = str(update.effective_user.id)
    server = None
    from config import SMTP_SETTINGS, is_smtp_configured
    from email_manager import add_email_to_history, validate_multiple_emails, format_email_list_for_display
    
    try:
        # Валидация email (поддержка нескольких адресов)
        is_valid, error_msg, valid_emails = validate_multiple_emails(email)
        
        if not is_valid:
            await update.message.reply_text(f"❌ Некорректный email адрес!\n\n{error_msg}")
            return
        
        # Показываем предупреждение если какие-то адреса были пропущены
        if error_msg:
            await update.message.reply_text(error_msg)
        
        if not is_smtp_configured():
            await update.message.reply_text(
                "❌ SMTP не настроен!\n\n"
                "Для отправки файлов по email необходимо:\n"
                "1. Настроить параметры в файле smtp_config.json\n"
                "2. Указать корректный email и пароль приложения"
            )
            return
        
        file_path = admin_states.get(user_id, {}).get('export_file', 'RezultBot.xlsx')
        format_type = admin_states.get(user_id, {}).get('email_format', 'excel')
        
        smtp_server = SMTP_SETTINGS["SMTP_SERVER"]
        smtp_port = SMTP_SETTINGS["SMTP_PORT"]
        smtp_user = SMTP_SETTINGS["SMTP_USER"]
        smtp_password = SMTP_SETTINGS["SMTP_PASSWORD"]
        
        # Показываем на какие адреса отправляем
        recipients_text = format_email_list_for_display(valid_emails)
        await update.message.reply_text(
            f"📧 Отправка на {len(valid_emails)} адрес(ов):\n{recipients_text}"
        )
        
        # Готовим сообщение
        msg = MIMEMultipart()
        msg['From'] = f"{SMTP_SETTINGS['FROM_NAME']} <{smtp_user}>"
        msg['To'] = ', '.join(valid_emails)  # Все адреса в поле To
        
        # Тема письма для выгрузки данных
        msg['Subject'] = "ЖП Бот"
        
        if format_type == "excel":
            if not os.path.exists(file_path):
                await update.message.reply_text("❌ Файл не найден!")
                return
            
            file_size = os.path.getsize(file_path) / 1024 / 1024
            body = f"Здравствуйте!\n\nВо вложении находится файл с выгрузкой данных ДСЕ.\n\n📊 Информация о выгрузке:\n• Дата создания: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n• Размер файла: {file_size:.2f} MB\n• Формат файла: Excel (.xlsx)\n\nС уважением,\n{SMTP_SETTINGS['FROM_NAME']}"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            await update.message.reply_text("📎 Подготовка вложения...")
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            filename = f"Выгрузка_данных_ДСЕ_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            part.add_header('Content-Disposition', f'attachment; filename=\"{filename}\"')
            msg.attach(part)
            
        elif format_type == "text":
            report_text = await generate_text_report()
            body = f"Здравствуйте!\n\nВыгрузка данных ДСЕ в виде текста:\n\n{report_text}\n\nС уважением,\n{SMTP_SETTINGS['FROM_NAME']}"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
        else:
            await update.message.reply_text("❌ Неизвестный формат отчёта!")
            return
        
        await update.message.reply_text("📧 Подключение к серверу...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0)
        
        await update.message.reply_text("🔒 Установка защищенного соединения...")
        server.starttls()
        
        await update.message.reply_text("👤 Авторизация...")
        server.login(smtp_user, smtp_password)
        
        await update.message.reply_text("📤 Отправка письма...")
        text = msg.as_string()
        server.sendmail(smtp_user, valid_emails, text)  # Отправка на все адреса
        
        # Сохраняем каждый email в историю
        for recipient_email in valid_emails:
            add_email_to_history(user_id, recipient_email, email_type="export")
        
        await update.message.reply_text(
            f"✅ Отчёт успешно отправлен на {len(valid_emails)} адрес(ов)!\n\n"
            f"📧 Все адреса сохранены в вашу историю для быстрого выбора."
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка отправки email!\n\n"
            f"Тип ошибки: {type(e).__name__}\n"
            f"Детали: {str(e)}\n\n"
            "Проверьте настройки SMTP в файле smtp_config.json"
        )
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
        if user_id in admin_states:
            admin_states[user_id].pop('exporting_data', None)
            admin_states[user_id].pop('export_completed', None)
            admin_states[user_id].pop('export_file', None)
            admin_states[user_id].pop('waiting_for_email', None)
            admin_states[user_id].pop('email_format', None)


async def test_smtp_connection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Тестировать SMTP подключение"""
    try:
        from config import SMTP_SETTINGS, is_smtp_configured
        
        if not is_smtp_configured():
            await update.callback_query.edit_message_text(
                "❌ SMTP не настроен!\n\n"
                "Настройте параметры в файле smtp_config.json"
            )
            return
        
        await update.callback_query.edit_message_text("🔍 Тестирование SMTP соединения...")
        
        # Тестируем подключение
        server = None
        try:
            server = smtplib.SMTP(SMTP_SETTINGS["SMTP_SERVER"], SMTP_SETTINGS["SMTP_PORT"])
            server.starttls()
            server.login(SMTP_SETTINGS["SMTP_USER"], SMTP_SETTINGS["SMTP_PASSWORD"])
            
            await update.callback_query.edit_message_text(
                f"✅ SMTP соединение успешно!\n\n"
                f"📧 Сервер: {SMTP_SETTINGS['SMTP_SERVER']}\n"
                f"🔌 Порт: {SMTP_SETTINGS['SMTP_PORT']}\n"
                f"👤 Пользователь: {SMTP_SETTINGS['SMTP_USER']}\n"
                f"📝 Отправитель: {SMTP_SETTINGS['FROM_NAME']}\n\n"
                f"Готов к отправке файлов по email!"
            )
            
        except smtplib.SMTPAuthenticationError:
            await update.callback_query.edit_message_text(
                "❌ Ошибка аутентификации!\n\n"
                "Проверьте email и пароль в smtp_config.json"
            )
        except Exception as e:
            await update.callback_query.edit_message_text(
                f"❌ Ошибка подключения!\n\n"
                f"Детали: {str(e)}"
            )
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
                    
    except Exception as e:
        await update.callback_query.edit_message_text(
            f"❌ Ошибка теста SMTP: {str(e)}"
        )


async def request_application_email_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запросить email адрес для отправки заявки"""
    user_id = str(update.callback_query.from_user.id)
    from config import SMTP_SETTINGS, is_smtp_configured
    from email_manager import get_email_suggestions
    
    if not is_smtp_configured():
        await update.callback_query.edit_message_text(
            "❌ SMTP не настроен!\n\n"
            "Для отправки заявок по email необходимо:\n"
            "1. Настроить параметры в файле smtp_config.json\n"
            "2. Указать корректный email и пароль приложения\n\n"
            "Текущие настройки:\n"
            f"• Сервер: {SMTP_SETTINGS.get('SMTP_SERVER', 'не указан')}\n"
            f"• Порт: {SMTP_SETTINGS.get('SMTP_PORT', 'не указан')}\n"
            f"• Email: {SMTP_SETTINGS.get('SMTP_USER', 'не указан')}"
        )
        return
    
    # Устанавливаем состояние ожидания email для заявки
    user_states[user_id]['waiting_for_application_email'] = True
    
    # Получаем предложения email адресов для заявок
    suggestions = get_email_suggestions(user_id, email_type="application", limit=5)
    
    message = "📧 Введите email адрес для отправки заявки:\n\n"
    
    # Показываем историю использованных email
    if suggestions:
        message += "💡 Ваши часто используемые адреса для заявок:\n"
        for i, email in enumerate(suggestions, 1):
            message += f"{i}. {email}\n"
        message += "\n"
    
    message += "Введите email адрес или выберите из списка выше.\n"
    message += "💡 Можно указать несколько адресов через запятую.\n\n"
    message += f"ℹ️ Настроен отправитель: {SMTP_SETTINGS['SMTP_USER']}"
    
    await update.callback_query.edit_message_text(message)


async def send_application_by_email(update: Update, context: ContextTypes.DEFAULT_TYPE, email: str) -> None:
    """Отправить заявку по электронной почте (поддержка нескольких адресов)"""
    user_id = str(update.effective_user.id)
    server = None
    from config import SMTP_SETTINGS, is_smtp_configured
    from email_manager import add_email_to_history, validate_multiple_emails, format_email_list_for_display
    
    try:
        # Валидация email (поддержка нескольких адресов)
        is_valid, error_msg, valid_emails = validate_multiple_emails(email)
        
        if not is_valid:
            await update.message.reply_text(f"❌ Некорректный email адрес!\n\n{error_msg}")
            return
        
        # Показываем предупреждение если какие-то адреса были пропущены
        if error_msg:
            await update.message.reply_text(error_msg)
        
        if not is_smtp_configured():
            await update.message.reply_text(
                "❌ SMTP не настроен!\n\n"
                "Для отправки заявок по email необходимо:\n"
                "1. Настроить параметры в файле smtp_config.json\n"
                "2. Указать корректный email и пароль приложения"
            )
            return
        
        # Получаем данные заявки
        user_data = user_states[user_id]
        dse_number = user_data.get('dse', 'Н/Д')
        problem_type = user_data.get('problem_type', 'Не указан')
        rc = user_data.get('rc', 'Не указан')
        description = user_data.get('description', 'Нет описания')
        photo_file_id = user_data.get('photo_file_id')
        
        smtp_server = SMTP_SETTINGS["SMTP_SERVER"]
        smtp_port = SMTP_SETTINGS["SMTP_PORT"]
        smtp_user = SMTP_SETTINGS["SMTP_USER"]
        smtp_password = SMTP_SETTINGS["SMTP_PASSWORD"]
        
        # Показываем на какие адреса отправляем
        recipients_text = format_email_list_for_display(valid_emails)
        await update.message.reply_text(
            f"📧 Отправка заявки на {len(valid_emails)} адрес(ов):\n{recipients_text}"
        )
        
        msg = MIMEMultipart()
        msg['From'] = f"{SMTP_SETTINGS['FROM_NAME']} <{smtp_user}>"
        msg['To'] = ', '.join(valid_emails)  # Все адреса в поле To
        
        # Тема письма для заявки с номером ДСЕ
        msg['Subject'] = f"Заявка ЖП Бот: {dse_number}"
        
        # Тело письма с деталями заявки
        body = f"""Здравствуйте!

Получена новая заявка через ЖП Бот.

📋 ДЕТАЛИ ЗАЯВКИ:
━━━━━━━━━━━━━━━━━━━━━━━━━━

🏢 ДСЕ: {dse_number}
📝 Тип проблемы: {problem_type}
🏭 РЦ: {rc}
📅 Дата создания: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}

📄 ОПИСАНИЕ:
{description}

━━━━━━━━━━━━━━━━━━━━━━━━━━

С уважением,
{SMTP_SETTINGS['FROM_NAME']}
"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Добавляем фото если есть
        if photo_file_id:
            await update.message.reply_text("📎 Подготовка вложения с фото...")
            try:
                # Скачиваем фото
                photo_file = await context.bot.get_file(photo_file_id)
                photo_path = f"{PHOTOS_DIR}/temp_{user_id}_{dt.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                await photo_file.download_to_drive(photo_path)
                
                # Прикрепляем к письму
                with open(photo_path, 'rb') as f:
                    img_data = f.read()
                
                # Определяем MIME тип
                mime_type, _ = mimetypes.guess_type(photo_path)
                if not mime_type:
                    mime_type = 'image/jpeg'
                
                maintype, subtype = mime_type.split('/', 1)
                img_part = MIMEBase(maintype, subtype)
                img_part.set_payload(img_data)
                encoders.encode_base64(img_part)
                img_part.add_header('Content-Disposition', f'attachment; filename="photo_{dse_number}.jpg"')
                msg.attach(img_part)
                
                # Удаляем временный файл
                try:
                    os.remove(photo_path)
                except:
                    pass
                    
            except Exception as e:
                await update.message.reply_text(f"⚠️ Не удалось прикрепить фото: {str(e)}")
        
        await update.message.reply_text("📧 Подключение к серверу...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0)
        
        await update.message.reply_text("🔒 Установка защищенного соединения...")
        server.starttls()
        
        await update.message.reply_text("👤 Авторизация...")
        server.login(smtp_user, smtp_password)
        
        await update.message.reply_text("📤 Отправка заявки...")
        text = msg.as_string()
        server.sendmail(smtp_user, valid_emails, text)  # Отправка на все адреса
        
        # Сохраняем заявку в базу данных
        record = {
            'dse': dse_number,
            'problem_type': problem_type,
            'rc': rc,
            'description': description,
            'datetime': dt.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'photo_file_id': photo_file_id,
            'sent_to_emails': ', '.join(valid_emails)  # Сохраняем все адреса
        }
        
        data_list = load_data()
        data_list.append(record)
        save_data(data_list)
        
        # Сохраняем каждый email в историю с номером ДСЕ
        for recipient_email in valid_emails:
            add_email_to_history(user_id, recipient_email, email_type="application", dse_number=dse_number)
        
        # Очищаем данные пользователя
        user_states[user_id] = {
            'application': '',
            'dse': '',
            'problem_type': '',
            'description': '',
            'rc': '',
            'photo_file_id': None
        }
        
        await update.message.reply_text(
            f"✅ Заявка успешно отправлена на {len(valid_emails)} адрес(ов)!\n\n"
            f"📋 ДСЕ: {dse_number}\n"
            f"📝 Тип проблемы: {problem_type}\n"
            f"🏭 РЦ: {rc}\n"
            f"📧 Все адреса сохранены в вашу историю для быстрого выбора."
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка отправки заявки!\n\n"
            f"Тип ошибки: {type(e).__name__}\n"
            f"Детали: {str(e)}\n\n"
            "Проверьте настройки SMTP в файле smtp_config.json"
        )
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
        if user_id in user_states:
            user_states[user_id].pop('waiting_for_application_email', None)


# === ФУНКЦИИ УПРАВЛЕНИЯ КЛИЧКАМИ ===

async def show_nicknames_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать меню управления кличками"""
    keyboard = [
        [InlineKeyboardButton("➕ Установить кличку", callback_data='nickname_set')],
        [InlineKeyboardButton("➖ Удалить кличку", callback_data='nickname_remove')],
        [InlineKeyboardButton("📋 Список кличек", callback_data='nickname_list')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='admin_users')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "🏷️ Управление кличками:\n\n"
        "Клички позволяют заменить ID пользователей на понятные имена.\n"
        "Устанавливать клички может только администратор.",
        reply_markup=reply_markup
    )


async def show_users_for_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """Показать список пользователей для установки/удаления кличек"""
    users = get_all_users()
    
    if not users:
        await update.callback_query.edit_message_text("Пользователей нет.")
        return
    
    keyboard = []
    
    for user_id, user_data in users.items():
        name = user_data.get('first_name', 'Неизвестно')
        username = user_data.get('username', '')
        current_nickname = get_user_nickname(user_id)
        
        if action == 'set':
            if current_nickname:
                button_text = f"{name} ({current_nickname}) ✏️"
            else:
                button_text = f"{name} (без клички)"
            callback_data = f'nickname_set_user_{user_id}'
        else:  # remove
            if current_nickname:
                button_text = f"{name} ({current_nickname}) ❌"
                callback_data = f'nickname_remove_user_{user_id}'
            else:
                continue  # Пропускаем пользователей без кличек при удалении
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    if action == 'remove' and not keyboard:
        await update.callback_query.edit_message_text("❌ Нет пользователей с кличками.")
        return
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='admin_manage_nicknames')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    action_text = "установки" if action == 'set' else "удаления"
    await update.callback_query.edit_message_text(
        f"👥 Выберите пользователя для {action_text} клички:",
        reply_markup=reply_markup
    )


async def start_nickname_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Начать ввод клички для пользователя"""
    admin_id = str(update.callback_query.from_user.id)
    users = get_all_users()
    
    if user_id not in users:
        await update.callback_query.edit_message_text("❌ Пользователь не найден.")
        return
    
    user_data = users[user_id]
    user_name = user_data.get('first_name', 'Неизвестно')
    current_nickname = get_user_nickname(user_id)
    
    # Устанавливаем состояние
    admin_states[admin_id] = {
        'setting_nickname_for': user_id,
        'setting_nickname': True
    }
    
    text = f"🏷️ Установка клички для {user_name}\n\n"
    if current_nickname:
        text += f"Текущая кличка: {current_nickname}\n\n"
    text += "Введите новую кличку (до 20 символов):"
    
    await update.callback_query.edit_message_text(text)


async def remove_nickname_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Подтвердить удаление клички"""
    users = get_all_users()
    
    if user_id not in users:
        await update.callback_query.edit_message_text("❌ Пользователь не найден.")
        return
    
    user_data = users[user_id]
    user_name = user_data.get('first_name', 'Неизвестно')
    current_nickname = get_user_nickname(user_id)
    
    if not current_nickname:
        await update.callback_query.edit_message_text("❌ У пользователя нет клички.")
        return
    
    if remove_user_nickname(user_id):
        await update.callback_query.edit_message_text(
            f"✅ Кличка '{current_nickname}' удалена у пользователя {user_name}."
        )
    else:
        await update.callback_query.edit_message_text("❌ Ошибка при удалении клички.")


async def show_nicknames_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список всех кличек"""
    nicknames = get_all_nicknames()
    
    if not nicknames:
        text = "📋 Список кличек пуст.\n\nНи у одного пользователя нет установленной клички."
    else:
        text = "📋 Список всех кличек:\n\n"
        users = get_all_users()
        
        for user_id, nickname in nicknames.items():
            user_data = users.get(user_id, {})
            real_name = user_data.get('first_name', 'Неизвестно')
            text += f"• {nickname} → {real_name} (ID: {user_id})\n"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='admin_manage_nicknames')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


# === ГЕНЕРАЦИЯ ТЕКСТОВОГО ОТЧЁТА ===
async def generate_text_report():
    """Генерирует текстовый отчёт по данным из RezultBot.xlsx"""
    import pandas as pd
    try:
        df = pd.read_excel('RezultBot.xlsx')
        lines = []
        for idx, row in df.iterrows():
            line = (
                f"{row.get('Деталь','')} | "
                f"{row.get('РЦ','')} | "
                f"{row.get('Тип проблемы','')} | "
                f"{row.get('Описание','')} | "
                f"{row.get('Дата','')} | "
                f"{row.get('Время','')} | "
                f"{row.get('Пользователь','')}"
            )
            lines.append(line)
        return '\n'.join(lines)
    except Exception as e:
        return f"Ошибка генерации текстового отчёта: {e}"


# === ОБРАБОТЧИКИ КНОПОК И СООБЩЕНИЙ ===

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    user_id = str(user.id)
    
    # === ГЛАВНОЕ МЕНЮ ===
    if data == 'back_to_main':
        await show_main_menu(update, user_id)
    
    elif data == 'open_application':
        user_states[user_id]['application'] = 'started'
        await show_application_menu(update, user_id)
    
    # === ЗАПОЛНЕНИЕ ЗАЯВКИ ===
    elif data == 'back_to_application':
        await show_application_menu(update, user_id)
    
    elif data == 'set_dse':
        user_states[user_id]['waiting_for'] = 'dse'
        await query.edit_message_text("Введите номер ДСЕ:")
    
    elif data == 'set_problem':
        await show_problem_types(update, user_id)
    
    elif data.startswith('problem_'):
        idx = int(data.split('_')[1])
        user_states[user_id]['problem_type'] = PROBLEM_TYPES[idx]
        await show_application_menu(update, user_id)
    
    elif data == 'set_rc':
        await show_rc_types(update, user_id)
    
    elif data.startswith('rc_'):
        idx = int(data.split('_')[1])
        user_states[user_id]['rc'] = RC_TYPES[idx]
        await show_application_menu(update, user_id)
    
    elif data == 'set_description':
        user_states[user_id]['waiting_for'] = 'description'
        await query.edit_message_text("Введите описание проблемы:")
    
    elif data == 'set_photo':
        user_states[user_id]['waiting_for'] = 'photo'
        await query.edit_message_text(
            "📸 Отправьте фото или используйте /cancel_photo для пропуска.\n\n"
            "Вы можете отправить одно фото."
        )
    
    elif data == 'send':
        # Отправка заявки
        user_data = user_states[user_id]
        record = {
            'dse': user_data['dse'],
            'problem_type': user_data['problem_type'],
            'rc': user_data['rc'],
            'description': user_data['description'],
            'datetime': dt.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'photo_file_id': user_data.get('photo_file_id')
        }
        
        data_list = load_data()
        data_list.append(record)
        save_data(data_list)
        
        # Очищаем данные пользователя
        user_states[user_id] = {
            'application': '',
            'dse': '',
            'problem_type': '',
            'description': '',
            'rc': '',
            'photo_file_id': None
        }
        
        await query.edit_message_text(
            "✅ Заявка успешно отправлена!\n\n"
            f"ДСЕ: {record['dse']}\n"
            f"Тип проблемы: {record['problem_type']}\n"
            f"РЦ: {record['rc']}\n"
            f"Описание: {record['description']}\n"
            f"📅 Дата: {record['datetime']}"
        )
        await show_main_menu(update, user_id)
    
    elif data == 'send_application_email':
        # Отправка заявки по email
        await request_application_email_address(update, context)
    
    elif data == 'edit_application':
        await show_application_menu(update, user_id)
    
    # === ПРОСМОТР ДСЕ ===
    elif data == 'view_dse_list':
        if has_permission(user_id, 'view_dse_list'):
            await show_dse_list_menu(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав для просмотра списка ДСЕ.")
    
    elif data == 'view_all_dse':
        await show_all_dse_records(update, context, page=0)
    
    elif data.startswith('page_'):
        page = int(data.split('_')[1])
        await show_all_dse_records(update, context, page=page)
    
    elif data == 'interactive_dse_search':
        await start_interactive_dse_search(update, context)
    
    elif data.startswith('dse_search_select_'):
        idx = int(data.split('_')[-1])
        await select_dse_from_search(update, context, idx)
    
    elif data == 'search_dse':
        await start_dse_search(update, context, 'dse')
    
    elif data == 'search_type':
        await start_dse_search(update, context, 'type')
    
    elif data == 'dse_statistics':
        await show_dse_statistics(update, context)
    
    # === АДМИН МЕНЮ ===
    elif data == 'admin_users':
        if get_user_role(user_id) == 'admin':
            await show_admin_menu(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'admin_list_users':
        if get_user_role(user_id) == 'admin':
            await show_users_list(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'admin_change_role_start':
        if get_user_role(user_id) == 'admin':
            await start_change_role_process(update, context, user_id)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data.startswith('role_'):
        if get_user_role(user_id) == 'admin':
            role_name = data.split('_', 1)[1]
            if user_id in admin_states and 'changing_role_for' in admin_states[user_id]:
                target_user_id = admin_states[user_id]['changing_role_for']
                set_user_role(target_user_id, role_name)
                admin_states[user_id].pop('changing_role_for', None)
                admin_states[user_id].pop('changing_role', None)
                await query.edit_message_text(f"✅ Роль изменена на: {ROLES[role_name]}")
                await show_admin_menu(update, context)
    
    elif data == 'admin_export_data':
        if get_user_role(user_id) == 'admin':
            await start_data_export(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    # === ОБРАБОТЧИКИ ЭКСПОРТА ===
    elif data == 'export_send_chat':
        if get_user_role(user_id) == 'admin':
            await send_file_to_chat(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'export_send_email_excel':
        if get_user_role(user_id) == 'admin':
            await request_email_address(update, context, format_type="excel")
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'export_send_email_text':
        if get_user_role(user_id) == 'admin':
            await request_email_address(update, context, format_type="text")
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'admin_test_smtp':
        if get_user_role(user_id) == 'admin':
            await test_smtp_connection(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'admin_manage_nicknames':
        if get_user_role(user_id) == 'admin':
            await show_nicknames_menu(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'nickname_set':
        if get_user_role(user_id) == 'admin':
            await show_users_for_nickname(update, context, 'set')
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'nickname_remove':
        if get_user_role(user_id) == 'admin':
            await show_users_for_nickname(update, context, 'remove')
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'nickname_list':
        if get_user_role(user_id) == 'admin':
            await show_nicknames_list(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data.startswith('nickname_set_user_'):
        if get_user_role(user_id) == 'admin':
            target_user_id = data.split('_')[-1]
            await start_nickname_input(update, context, target_user_id)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data.startswith('nickname_remove_user_'):
        if get_user_role(user_id) == 'admin':
            target_user_id = data.split('_')[-1]
            await remove_nickname_confirm(update, context, target_user_id)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    # === ОТСЛЕЖИВАНИЕ ДСЕ ===
    elif data == 'watch_dse_menu':
        await show_watched_dse_menu(update, context)
    
    elif data == 'watch_add_dse':
        await start_add_watched_dse(update, context)
    
    elif data == 'watch_remove_dse':
        await start_remove_watched_dse(update, context)
    
    elif data.startswith('watch_rm_idx_'):
        idx = int(data.split('_')[-1])
        from dse_watcher import get_watched_dse_list, remove_watched_dse
        watched_list = get_watched_dse_list(user_id)
        if 0 <= idx < len(watched_list):
            dse_to_remove = watched_list[idx]
            remove_watched_dse(user_id, dse_to_remove)
            await query.edit_message_text(f"✅ ДСЕ {dse_to_remove} удалён из отслеживания.")
            await show_watched_dse_menu(update, context)
    
    elif data == 'watch_list':
        await show_watched_dse_list(update, context)
    
    elif data.startswith('watch_select_dse_'):
        idx_str = data.split('_')[-1]
        if idx_str == 'manual':
            user_states[user_id] = user_states.get(user_id, {})
            user_states[user_id]['watch_dse_state'] = 'awaiting_manual_input'
            await query.edit_message_text("📝 Введите номер ДСЕ для отслеживания:")
        else:
            from dse_watcher import add_watched_dse
            dse_list = get_unique_dse_values()
            idx = int(idx_str)
            if 0 <= idx < len(dse_list):
                dse_value = dse_list[idx]
                add_watched_dse(user_id, dse_value)
                await query.edit_message_text(f"✅ ДСЕ {dse_value} добавлен в отслеживание!")
                await show_watched_dse_menu(update, context)
    
    # === ЧАТ ПО ДСЕ ===
    elif data == 'chat_dse_menu':
        from chat_manager import show_chat_menu
        await show_chat_menu(update, context)
    
    elif data == 'chat_start_search':
        await start_dse_chat_search_with_selection(update, context)
    
    elif data.startswith('chat_select_dse_'):
        idx_str = data.split('_')[-1]
        if idx_str == 'manual':
            user_states[user_id] = user_states.get(user_id, {})
            user_states[user_id]['dse_chat_state'] = 'awaiting_manual_input'
            await query.edit_message_text("📝 Введите номер ДСЕ для начала чата:")
        else:
            from chat_manager import handle_dse_input
            dse_list = get_unique_dse_values()
            idx = int(idx_str)
            if 0 <= idx < len(dse_list):
                dse_value = dse_list[idx]
                # Имитируем текстовое сообщение
                user_states[user_id] = user_states.get(user_id, {})
                user_states[user_id]['dse_chat_state'] = 'selecting_or_manual'
                # Вызываем handle_dse_input с выбранным ДСЕ
                from chat_manager import initiate_dse_chat_search
                user_states[user_id]['dse_chat_dse_value'] = dse_value
                await handle_dse_input(update, context)
    
    # === ОБРАБОТЧИКИ ЧАТА (из chat_manager) ===
    elif data.startswith('chat_confirm_target_') or data.startswith('chat_decline_target_'):
        from chat_manager import handle_initiator_confirmation
        await handle_initiator_confirmation(update, context)
    
    elif data.startswith('chat_accept_') or data.startswith('chat_decline_'):
        from chat_manager import handle_responder_confirmation
        await handle_responder_confirmation(update, context)
    
    elif data in ['chat_end', 'chat_back']:
        from chat_manager import handle_chat_control
        await handle_chat_control(update, context)
    
    # === PDF ЭКСПОРТ ===
    elif data == 'pdf_export_menu':
        if has_permission(user_id, 'pdf_export'):
            from pdf_generator import show_pdf_export_menu
            await show_pdf_export_menu(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав для экспорта PDF.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений и фото"""
    user = update.effective_user
    user_id = str(user.id)
    
    # Проверяем, ожидается ли ввод данных
    if user_id in user_states:
        user_data = user_states[user_id]
        
        # Обработка фото
        if update.message.photo:
            if user_data.get('waiting_for') == 'photo':
                # Сохраняем file_id самого большого фото
                photo_file_id = update.message.photo[-1].file_id
                user_states[user_id]['photo_file_id'] = photo_file_id
                user_states[user_id].pop('waiting_for', None)
                await update.message.reply_text("✅ Фото сохранено!")
                await show_application_menu(update, user_id)
                return
            # Обработка сообщений в чате
            elif 'dse_chat_state' in user_data:
                from chat_manager import handle_chat_message
                await handle_chat_message(update, context)
                return
        
        # Обработка текстовых сообщений
        if update.message.text:
            text = update.message.text.strip()
            
            # === ЗАПОЛНЕНИЕ ЗАЯВКИ ===
            if user_data.get('waiting_for') == 'dse':
                user_states[user_id]['dse'] = text
                user_states[user_id].pop('waiting_for', None)
                await update.message.reply_text(f"✅ ДСЕ сохранён: {text}")
                await show_application_menu(update, user_id)
                return
            
            elif user_data.get('waiting_for') == 'description':
                user_states[user_id]['description'] = text
                user_states[user_id].pop('waiting_for', None)
                await update.message.reply_text(f"✅ Описание сохранено")
                await show_application_menu(update, user_id)
                return
            
            # === ПОИСК ДСЕ ===
            elif user_id in dse_view_states:
                dse_state = dse_view_states[user_id]
                if dse_state.get('searching_dse'):
                    await show_search_results(update, context, text, 'dse')
                    dse_view_states[user_id].pop('searching_dse', None)
                    return
                elif dse_state.get('searching_type'):
                    await show_search_results(update, context, text, 'type')
                    dse_view_states[user_id].pop('searching_type', None)
                    return
                elif dse_state.get('interactive_search'):
                    await handle_dse_search_input(update, context)
                    return
            
            # === ОТСЛЕЖИВАНИЕ ДСЕ ===
            elif user_data.get('watch_dse_state') == 'awaiting_manual_input':
                from dse_watcher import add_watched_dse
                dse_value = text.strip().upper()
                add_watched_dse(user_id, dse_value)
                user_states[user_id].pop('watch_dse_state', None)
                await update.message.reply_text(f"✅ ДСЕ {dse_value} добавлен в отслеживание!")
                await show_watched_dse_menu(update, context)
                return
            
            # === ЧАТ ПО ДСЕ ===
            elif user_data.get('dse_chat_state') == 'awaiting_manual_input':
                from chat_manager import handle_dse_input
                user_states[user_id]['dse_chat_dse_value'] = text.strip().upper()
                user_states[user_id]['dse_chat_state'] = 'selecting_or_manual'
                await handle_dse_input(update, context)
                return
            elif user_data.get('dse_chat_state') in ['waiting_for_initiator_confirmation', 'in_chat']:
                from chat_manager import handle_chat_message
                await handle_chat_message(update, context)
                return
            
            # === АДМИН: ИЗМЕНЕНИЕ РОЛИ ===
            elif user_id in admin_states and admin_states[user_id].get('changing_role'):
                target_user_id = text.strip()
                users = get_all_users()
                if target_user_id in users:
                    admin_states[user_id]['changing_role_for'] = target_user_id
                    admin_states[user_id].pop('changing_role', None)
                    await show_role_selection_menu(update, context, target_user_id)
                else:
                    await update.message.reply_text(
                        f"❌ Пользователь с ID {target_user_id} не найден.\n\n"
                        "Введите корректный ID:"
                    )
                return
            
            # === АДМИН: УСТАНОВКА КЛИЧКИ ===
            elif user_id in admin_states and admin_states[user_id].get('setting_nickname'):
                nickname = text.strip()
                if len(nickname) > 20:
                    await update.message.reply_text("❌ Кличка слишком длинная (максимум 20 символов).\n\nВведите другую кличку:")
                    return
                
                if check_nickname_exists(nickname):
                    await update.message.reply_text(f"❌ Кличка '{nickname}' уже используется.\n\nВведите другую кличку:")
                    return
                
                target_user_id = admin_states[user_id].get('setting_nickname_for')
                if target_user_id:
                    set_user_nickname(target_user_id, nickname)
                    admin_states[user_id].pop('setting_nickname', None)
                    admin_states[user_id].pop('setting_nickname_for', None)
                    
                    users = get_all_users()
                    user_name = users.get(target_user_id, {}).get('first_name', 'Неизвестно')
                    await update.message.reply_text(f"✅ Кличка '{nickname}' установлена для {user_name}")
                    await show_nicknames_menu(update, context)
                return
            
            # === АДМИН: EMAIL АДРЕС ===
            elif user_id in admin_states and admin_states[user_id].get('waiting_for_email'):
                email = text.strip()
                # Простая проверка email
                if '@' in email and '.' in email:
                    admin_states[user_id].pop('waiting_for_email', None)
                    await send_file_by_email(update, context, email)
                else:
                    await update.message.reply_text(
                        "❌ Некорректный email адрес.\n\n"
                        "Введите корректный email:"
                    )
                return
            
            # === ПОЛЬЗОВАТЕЛЬ: EMAIL ДЛЯ ЗАЯВКИ ===
            elif user_id in user_states and user_states[user_id].get('waiting_for_application_email'):
                email = text.strip()
                # Простая проверка email
                if '@' in email and '.' in email:
                    user_states[user_id].pop('waiting_for_application_email', None)
                    await send_application_by_email(update, context, email)
                else:
                    await update.message.reply_text(
                        "❌ Некорректный email адрес.\n\n"
                        "Введите корректный email:"
                    )
                return
    
    # Если ничего не обработано, просто игнорируем сообщение
    await update.message.reply_text(
        "Используйте /start для открытия главного меню."
    )


async def cancel_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /cancel_photo - отменить загрузку фото"""
    user_id = str(update.effective_user.id)
    
    if user_id in user_states:
        user_data = user_states[user_id]
        if user_data.get('waiting_for') == 'photo':
            user_states[user_id].pop('waiting_for', None)
            user_states[user_id]['photo_file_id'] = None
            await update.message.reply_text("❌ Загрузка фото отменена.")
            await show_application_menu(update, user_id)
            return
    
    await update.message.reply_text("Нечего отменять.")

