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
        keyboard.append([InlineKeyboardButton("🔄 Изменить", callback_data='edit_application')])

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

    nav_buttons.append(InlineKeyboardButton("↩️ Назад", callback_data='view_dse_list'))
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
        [InlineKeyboardButton("📋 Все записи", callback_data='dse_view_all')],
        [InlineKeyboardButton("⬅️ В меню", callback_data='view_dse_list')]
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
        [InlineKeyboardButton("👥 Список пользователей", callback_data='admin_list_users')],
        [InlineKeyboardButton("✏️ Изменить роль пользователя", callback_data='admin_change_role_start')],
        [InlineKeyboardButton("🏷️ Управление кличками", callback_data='admin_manage_nicknames')],
        [InlineKeyboardButton("📊 Выгрузить данные", callback_data='admin_export_data')],
        [InlineKeyboardButton("📧 Тест SMTP", callback_data='admin_test_smtp')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main')]
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
        [InlineKeyboardButton("📧 Отправить по почте", callback_data='export_send_email')],
        [InlineKeyboardButton("⬅️ Отмена", callback_data='admin_users')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "✅ Файл с данными успешно создан!\n\n"
        "Выберите способ получения файла:",
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


async def request_email_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запросить email адрес для отправки файла"""
    user_id = str(update.callback_query.from_user.id)
    
    # Сначала проверим SMTP настройки
    from config import SMTP_SETTINGS, is_smtp_configured
    
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
    
    # Устанавливаем состояние ожидания email
    admin_states[user_id]['waiting_for_email'] = True
    
    await update.callback_query.edit_message_text(
        "📧 Введите email адрес для отправки файла:\n\n"
        "Пример: user@example.com\n\n"
        f"ℹ️ Настроен отправитель: {SMTP_SETTINGS['SMTP_USER']}"
    )


async def send_file_by_email(update: Update, context: ContextTypes.DEFAULT_TYPE, email: str) -> None:
    """Отправить файл по электронной почте"""
    user_id = str(update.effective_user.id)
    server = None
    
    try:
        from config import SMTP_SETTINGS, is_smtp_configured
        
        # Проверяем, настроен ли SMTP
        if not is_smtp_configured():
            await update.message.reply_text(
                "❌ SMTP не настроен!\n\n"
                "Для отправки файлов по email необходимо:\n"
                "1. Настроить параметры в файле smtp_config.json\n"
                "2. Указать корректный email и пароль приложения"
            )
            return
        
        file_path = admin_states.get(user_id, {}).get('export_file', 'RezultBot.xlsx')
        
        if not os.path.exists(file_path):
            await update.message.reply_text("❌ Файл не найден!")
            return
        
        # Получаем размер файла для диагностики
        file_size = os.path.getsize(file_path) / 1024 / 1024  # в MB
        
        # Настройки SMTP из конфигурации
        smtp_server = SMTP_SETTINGS["SMTP_SERVER"]
        smtp_port = SMTP_SETTINGS["SMTP_PORT"]
        smtp_user = SMTP_SETTINGS["SMTP_USER"]
        smtp_password = SMTP_SETTINGS["SMTP_PASSWORD"]
        
        await update.message.reply_text(
            f"📧 Подготовка email...\n"
            f"📄 Размер файла: {file_size:.2f} MB\n"
            f"🌐 Сервер: {smtp_server}:{smtp_port}"
        )
        
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = f"{SMTP_SETTINGS['FROM_NAME']} <{smtp_user}>"
        msg['To'] = email
        msg['Subject'] = f"Выгрузка данных ДСЕ - {dt.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Добавляем тело письма
        body = f"""Здравствуйте!

Во вложении находится файл с выгрузкой данных ДСЕ.

📊 Информация о выгрузке:
• Дата создания: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}
• Размер файла: {file_size:.2f} MB
• Формат файла: Excel (.xlsx)

С уважением,
{SMTP_SETTINGS['FROM_NAME']}"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Добавляем файл во вложение
        await update.message.reply_text("📎 Подготовка вложения...")
        
        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            part.set_payload(attachment.read())
            
        encoders.encode_base64(part)
        filename = f"Выгрузка_данных_ДСЕ_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{filename}"'
        )
        msg.attach(part)
        
        # Отправляем email с подробной диагностикой
        await update.message.reply_text("� Подключение к серверу...")
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0)  # Отключаем отладку для пользователя
        
        await update.message.reply_text("🔒 Установка защищенного соединения...")
        server.starttls()
        
        await update.message.reply_text("👤 Авторизация...")
        server.login(smtp_user, smtp_password)
        
        await update.message.reply_text("📤 Отправка письма...")
        text = msg.as_string()
        server.sendmail(smtp_user, email, text)
        
        await update.message.reply_text(f"✅ Файл успешно отправлен на {email}!")
        
    except smtplib.SMTPAuthenticationError as e:
        await update.message.reply_text(
            f"❌ Ошибка аутентификации SMTP!\n\n"
            f"Детали: {str(e)}\n\n"
            "Проверьте:\n"
            "• Правильность email и пароля\n"
            "• Включена ли двухфакторная аутентификация\n"
            "• Используете ли пароль приложения (для Gmail)\n"
            "• Включен ли доступ для менее безопасных приложений"
        )
    except smtplib.SMTPRecipientsRefused as e:
        await update.message.reply_text(
            f"❌ Ошибка получателя!\n\n"
            f"Email '{email}' отклонен сервером.\n"
            f"Детали: {str(e)}\n\n"
            "Проверьте правильность email адреса."
        )
    except smtplib.SMTPDataError as e:
        await update.message.reply_text(
            f"❌ Ошибка данных SMTP!\n\n"
            f"Детали: {str(e)}\n\n"
            "Возможно файл слишком большой или проблема с форматом."
        )
    except smtplib.SMTPConnectError as e:
        await update.message.reply_text(
            f"❌ Не удается подключиться к SMTP серверу!\n\n"
            f"Детали: {str(e)}\n\n"
            "Проверьте:\n"
            f"• Сервер: {SMTP_SETTINGS.get('SMTP_SERVER', 'не указан')}\n"
            f"• Порт: {SMTP_SETTINGS.get('SMTP_PORT', 'не указан')}\n"
            "• Подключение к интернету"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Неожиданная ошибка отправки email!\n\n"
            f"Тип ошибки: {type(e).__name__}\n"
            f"Детали: {str(e)}\n\n"
            "Проверьте настройки SMTP в файле smtp_config.json"
        )
    
    finally:
        # Закрываем SMTP соединение если оно было открыто
        if server:
            try:
                server.quit()
            except:
                pass
        
        # Очищаем состояние
        if user_id in admin_states:
            admin_states[user_id].pop('exporting_data', None)
            admin_states[user_id].pop('export_completed', None)
            admin_states[user_id].pop('export_file', None)
            admin_states[user_id].pop('waiting_for_email', None)


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


# === ФУНКЦИИ РАБОТЫ С ФОТО ===

async def request_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запрашивает фото у пользователя"""
    user_id = str(update.callback_query.from_user.id)

    # Устанавливаем состояние ожидания фото
    user_states[user_id]['waiting_for_photo'] = True

    # Отправляем новое сообщение, а не редактируем старое
    # Это позволяет боту получать следующее сообщение от пользователя
    await update.callback_query.answer()  # Отвечаем на callback, чтобы убрать "крутилку"
    await context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text="📸 Пожалуйста, отправьте фото.\n\n"
             "Используйте /cancel_photo для отмены.",
        # Убираем inline кнопки, чтобы не мешали
    )


# === КОМАНДА ОТМЕНЫ ФОТО ===

async def cancel_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /cancel_photo для отмены ожидания фото"""
    user_id = str(update.effective_user.id)

    # Отменяем ожидание фото
    if 'waiting_for_photo' in user_states.get(user_id, {}):
        del user_states[user_id]['waiting_for_photo']
        await update.message.reply_text("❌ Отправка фото отменена.")
        # Возвращаемся в меню заявки
        await show_application_menu(update, user_id)
    else:
        await update.message.reply_text("❌ Вы не отправляете фото.")


# === ОСНОВНОЙ ОБРАБОТЧИК КНОПОК ===

# commands.py (обновлённый и проверенный фрагмент button_handler)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий кнопок"""

    query = update.callback_query
    # ВАЖНО: Отвечаем на callback сразу же, чтобы избежать ошибки "Query is too old"
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    data = query.data

    print(f"🖱️ {user.first_name}: нажал кнопку '{data}'")

    # Проверяем права доступа
    if not has_permission(user_id, 'view_main_menu'):
        # Так как query.answer() уже был вызван, редактируем сообщение напрямую
        try:
            await query.edit_message_text("❌ У вас нет прав для использования этой функции.")
        except telegram.error.BadRequest:
            # Если сообщение уже нельзя редактировать, отправляем новое
            await context.bot.send_message(chat_id=query.message.chat_id,
                                           text="❌ У вас нет прав для использования этой функции.")
        return

    # === ОБРАБОТКА КНОПОК ЗАЯВКИ ===
    # Обработка новой кнопки "Заявка"
    if data == 'open_application':
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для заполнения формы.")
            return
        # Отмечаем, что заявка начата
        if user_id in user_states:
            user_states[user_id]['application'] = 'started'
        await show_application_menu(update, user_id)

    # Обработка кнопки возврата из меню заявки
    elif data == 'back_to_main':
        await show_main_menu(update, user_id)

    # Обработка кнопки "Назад" из меню выбора проблемы
    elif data == 'back_to_application':
        await show_application_menu(update, user_id)

    # Обработка кнопки "Изменить" в меню заявки
    elif data == 'edit_application':
        # В данном случае просто возвращаем к меню заявки для повторного редактирования
        await show_application_menu(update, user_id)

    # Обработка кнопки отправки в меню заявки
    elif data == 'send':
        if not has_permission(user_id, 'initiator'):
            await query.edit_message_text("❌ У вас нет прав для отправки формы.")
            return
        user_data = user_states.get(user_id, {})
        if all([user_data.get('dse'), user_data.get('problem_type'), user_data.get('rc'), user_data.get('description')]):
            # Загружаем существующие данные
            all_data = load_data(DATA_FILE)

            # Подготавливаем запись для сохранения
            record_to_save = {
                'dse': user_data['dse'],
                'problem_type': user_data['problem_type'],
                'rc': user_data['rc'],
                'description': user_data['description'],
                'datetime': dt.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': user_id
            }

            # Если есть фото, добавляем его file_id
            if user_data.get('photo_file_id'):
                record_to_save['photo_file_id'] = user_data['photo_file_id']

            # Добавляем новые данные
            if user_id not in all_data:
                all_data[user_id] = []

            all_data[user_id].append(record_to_save)

            # Сохраняем в файл
            save_data(all_data, DATA_FILE)

            # Очищаем временные данные ЗАЯВКИ, но оставляем application = 'started'
            if user_id in user_states:
                user_states[user_id] = {
                    'application': 'started',  # Оставляем признак начатой заявки
                    'dse': '',
                    'problem_type': '',
                    'description': '',
                    'rc': '',
                    'photo_file_id': None  # Очищаем фото тоже
                }

            response = f"✅ Данные успешно отправлены и сохранены!\n📅 Дата отправки: {record_to_save['datetime']}"
            await query.edit_message_text(text=response)
            print(f"📤 Бот: {response}")

            # После отправки возвращаем в главное меню
            await show_main_menu(update, user_id)
        else:
            await query.edit_message_text(text="❌ Ошибка: не все обязательные поля заполнены! Требуется: ДСЕ, Тип проблемы, РЦ и Описание.")

    # === ОБРАБОТКА КНОПОК ПРОСМОТРА ДСЕ ===
    # Обработка кнопок просмотра ДСЕ
    elif data == 'view_dse_list':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для просмотра списка ДСЕ.")
            return
        await show_dse_list_menu(update, context)

    elif data == 'dse_view_all':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для просмотра списка ДСЕ.")
            return
        await show_all_dse_records(update, context, page=0)

    elif data.startswith('dse_view_all_'):
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для просмотра списка ДСЕ.")
            return
        page = int(data.split('_')[-1])
        await show_all_dse_records(update, context, page=page)

    elif data == 'dse_search_interactive':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для поиска по ДСЕ.")
            return
        await start_interactive_dse_search(update, context)

    elif data.startswith('dse_select_'):
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для поиска по ДСЕ.")
            return
        try:
            index = int(data.split('_')[-1])
            await select_dse_from_search(update, context, index)
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка обработки выбора.")

    elif data == 'dse_search_clear':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для поиска по ДСЕ.")
            return
        user_id = str(query.from_user.id)
        if user_id in dse_view_states:
            dse_view_states[user_id]['current_search'] = ''
        await show_dse_search_results(update, context, user_id)

    elif data == 'dse_search_dse':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для поиска по ДСЕ.")
            return
        await start_dse_search(update, context, 'dse')

    elif data == 'dse_search_type':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для поиска по типу проблемы.")
            return
        await start_dse_search(update, context, 'type')

    elif data == 'dse_statistics':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для просмотра статистики.")
            return
        await show_dse_statistics(update, context)

    # === ОБРАБОТКА КНОПОК ОТСЛЕЖИВАНИЯ ДСЕ ===
    elif data == 'watch_dse_menu':
        if not has_permission(user_id, 'watch_dse'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        from dse_watcher import load_watched_dse_data  # Убедимся, что данные загружены
        load_watched_dse_data()
        await show_watched_dse_menu(update, context)

    elif data == 'watch_add_dse':
        if not has_permission(user_id, 'watch_dse'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        await start_add_watched_dse(update, context)

    elif data == 'watch_remove_dse':
        if not has_permission(user_id, 'watch_dse'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        await start_remove_watched_dse(update, context)

    elif data == 'watch_list_dse':
        if not has_permission(user_id, 'watch_dse'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        await show_watched_dse_list(update, context)

    elif data.startswith('watch_rm_idx_'):
        if not has_permission(user_id, 'watch_dse'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        try:
            index = int(data.split('_')[-1])
            temp_list = user_states.get(user_id, {}).get('temp_watched_list', [])
            if 0 <= index < len(temp_list):
                dse_to_remove = temp_list[index]
                from dse_watcher import remove_watched_dse
                remove_watched_dse(user_id, dse_to_remove)

                # Очищаем временные данные
                if user_id in user_states and 'temp_watched_list' in user_states[user_id]:
                    del user_states[user_id]['temp_watched_list']

                await query.edit_message_text(f"✅ ДСЕ '{dse_to_remove.upper()}' удалено из списка отслеживания.")
                # Можно сразу показать обновленный список или вернуть в меню
                # await show_watched_dse_menu(update, context)
            else:
                await query.edit_message_text("❌ Неверный выбор. Попробуйте снова.")
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка обработки выбора. Попробуйте снова.")

    # === ОБРАБОТКА ВЫБОРА ДСЕ ИЗ СПИСКА ДЛЯ ОТСЛЕЖИВАНИЯ ===
    elif data.startswith('watch_select_dse_'):
        if not has_permission(user_id, 'watch_dse'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        suffix = data[len('watch_select_dse_'):]

        if suffix == 'manual':
            # Пользователь хочет ввести вручную
            user_states[user_id]['adding_watched_dse'] = True
            if 'adding_watched_dse_state' in user_states[user_id]:
                del user_states[user_id]['adding_watched_dse_state']
            if 'temp_dse_list' in user_states[user_id]:
                del user_states[user_id]['temp_dse_list']
            await query.edit_message_text("➕ Введите номер ДСЕ для отслеживания:")
        else:
            try:
                index = int(suffix)
                temp_list = user_states.get(user_id, {}).get('temp_dse_list', [])
                if 0 <= index < len(temp_list):
                    dse_to_watch = temp_list[index]
                    from dse_watcher import add_watched_dse
                    add_watched_dse(user_id, dse_to_watch)

                    # Очищаем временные данные
                    temp_keys = ['temp_dse_list', 'adding_watched_dse_state']
                    for key in temp_keys:
                        if user_id in user_states and key in user_states[user_id]:
                            del user_states[user_id][key]

                    await query.edit_message_text(f"✅ ДСЕ '{dse_to_watch.upper()}' добавлено в список отслеживания.")
                    # Можно сразу показать меню отслеживания
                    await show_watched_dse_menu(update, context)
                else:
                    await query.edit_message_text("❌ Неверный выбор. Попробуйте снова.")
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Ошибка обработки выбора. Попробуйте снова.")

    # === ОБРАБОТКА ПОДТВЕРЖДЕНИЯ/ОТМЕНЫ ОТ ИНИЦИАТОРА ЧАТА ПО ДСЕ ===
    elif data in ['dse_chat_confirm_initiator', 'dse_chat_cancel_initiator']:
        # ВАЖНО: Отвечаем на callback сразу
        # await query.answer() # Уже вызван в самом начале button_handler
        print(f"🔍 Button handler: Received '{data}' from {user.first_name} ({user_id})")
        from chat_manager import handle_initiator_confirmation
        # Передаём управление в chat_manager
        await handle_initiator_confirmation(update, context)
        print(f"🔍 Button handler: Finished handling '{data}' for {user.first_name} ({user_id})")

    # === ОБРАБОТКА ВЫБОРА ДСЕ ИЗ СПИСКА ДЛЯ ЧАТА ===
    elif data.startswith('chat_select_dse_'):
        # if  has_permission(user_id, 'initiator'):
        #     await query.edit_message_text("❌ У вас нет прав для чата по ДСЕ.")
        #     return
        suffix = data[len('chat_select_dse_'):]

        if suffix == 'manual':
            # Пользователь хочет ввести вручную
            user_states[user_id]['dse_chat_state'] = 'waiting_for_dse_input'
            if 'temp_dse_list' in user_states[user_id]:
                del user_states[user_id]['temp_dse_list']
            await query.edit_message_text("🔍 Пожалуйста, введите номер ДСЕ для поиска:")
        else:
            try:
                index = int(suffix)
                temp_list = user_states.get(user_id, {}).get('temp_dse_list', [])
                if 0 <= index < len(temp_list):
                    dse_value = temp_list[index]

                    # Очищаем временные данные
                    temp_keys = ['temp_dse_list', 'dse_chat_state']
                    for key in temp_keys:
                        if user_id in user_states and key in user_states[user_id]:
                            del user_states[user_id][key]

                    # Передаем выбранное ДСЕ в chat_manager для продолжения процесса
                    # Нам нужно имитировать ввод текста. Создадим фейковое сообщение.
                    from chat_manager import handle_dse_input

                    class FakeMessage:
                        def __init__(self, from_user, text):
                            self.from_user = from_user
                            self.text = text

                    class FakeUpdate:
                        def __init__(self, from_user, message_text):
                            self.effective_user = from_user
                            self.message = FakeMessage(from_user, message_text)
                            self.callback_query = None

                    fake_update = FakeUpdate(user, dse_value)
                    await handle_dse_input(fake_update, context)

                else:
                    await query.edit_message_text("❌ Неверный выбор. Попробуйте снова.")
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Ошибка обработки выбора. Попробуйте снова.")

    # === ОБРАБОТКА PDF КНОПОК ===
    elif data == 'pdf_export_menu':
        if not has_permission(user_id, 'pdf_export'):
            await query.edit_message_text("❌ У вас нет прав для создания PDF отчетов.")
            return
        await show_pdf_export_menu(update, context)

    elif data == 'pdf_search_dse':
        if not has_permission(user_id, 'pdf_export'):
            await query.edit_message_text("❌ У вас нет прав для создания PDF отчетов.")
            return
        await start_pdf_dse_search(update, context)

    elif data == 'pdf_recent_records':
        if not has_permission(user_id, 'pdf_export'):
            await query.edit_message_text("❌ У вас нет прав для создания PDF отчетов.")
            return
        await show_recent_records_for_pdf(update, context)

    elif data.startswith('pdf_select_'):
        if not has_permission(user_id, 'pdf_export'):
            await query.edit_message_text("❌ У вас нет прав для создания PDF отчетов.")
            return
        try:
            index = int(data.split('_')[-1])
            records = pdf_session_records.get(user_id, [])
            if 0 <= index < len(records):
                record = records[index]
                await show_pdf_confirm_record(update, context, record, index)
            else:
                await query.edit_message_text("❌ Запись не найдена.")
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка обработки выбора.")

    elif data.startswith('pdf_generate_'):
        if not has_permission(user_id, 'pdf_export'):
            await query.edit_message_text("❌ У вас нет прав для создания PDF отчетов.")
            return
        try:
            index = int(data.split('_')[-1])
            records = pdf_session_records.get(user_id, [])
            if 0 <= index < len(records):
                record = records[index]
                await generate_pdf_report(update, context, record)
            else:
                await query.edit_message_text("❌ Запись не найдена.")
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка генерации PDF.")

    # === ОБРАБОТКА АДМИНСКИХ КНОПОК ===
    elif data == 'admin_users':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await show_admin_menu(update, context)

    elif data == 'admin_list_users':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await show_users_list(update, context)

    elif data == 'admin_change_role_start':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await start_change_role_process(update, context, user_id)

    elif data.startswith('set_role_'):
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        # Формат: set_role_USERID_ROLE
        parts = data.split('_')
        if len(parts) >= 4:
            target_user_id = parts[2]
            new_role = parts[3]

            if set_user_role(target_user_id, new_role):
                users = get_all_users()
                target_user = users.get(target_user_id, {})
                user_name = target_user.get('first_name', 'Пользователь')
                role_name = ROLES.get(new_role, new_role)
                await query.edit_message_text(f"✅ Роль пользователя {user_name} изменена на {role_name}")
                print(f"🔧 Админ {user.first_name} изменил роль {user_name} на {new_role}")
            else:
                await query.edit_message_text("❌ Ошибка при изменении роли")
        else:
            await query.edit_message_text("❌ Ошибка в данных")

    # === ОБРАБОТКА КНОПОК ЭКСПОРТА ДАННЫХ ===
    elif data == 'admin_export_data':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await start_data_export(update, context)

    elif data == 'export_send_chat':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await send_file_to_chat(update, context)

    elif data == 'export_send_email':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await request_email_address(update, context)

    elif data == 'admin_test_smtp':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await test_smtp_connection(update, context)

    # === ОБРАБОТКА КНОПОК УПРАВЛЕНИЯ КЛИЧКАМИ ===
    elif data == 'admin_manage_nicknames':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await show_nicknames_menu(update, context)

    elif data == 'nickname_set':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await show_users_for_nickname(update, context, 'set')

    elif data == 'nickname_remove':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await show_users_for_nickname(update, context, 'remove')

    elif data == 'nickname_list':
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        await show_nicknames_list(update, context)

    elif data.startswith('nickname_set_user_'):
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        target_user_id = data.split('_')[-1]
        await start_nickname_input(update, context, target_user_id)

    elif data.startswith('nickname_remove_user_'):
        if get_user_role(user_id) != 'admin':
            await query.edit_message_text("❌ Только администраторы могут использовать эту функцию.")
            return
        target_user_id = data.split('_')[-1]
        await remove_nickname_confirm(update, context, target_user_id)

    # === ОБРАБОТКА КНОПОК ЗАПОЛНЕНИЯ ФОРМЫ ===
    # Обычные кнопки для заполнения полей (в меню заявки)
    elif data == 'set_dse':
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для заполнения формы.")
            return
        # Запрашиваем ДСЕ
        await query.edit_message_text(text="Введите ДСЕ:")
        user_states[user_id]['current_input'] = 'dse'

    elif data == 'set_problem':
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для заполнения формы.")
            return
        # Показываем список типов проблем
        await show_problem_types(update, user_id)

    elif data == 'set_rc':
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для заполнения формы.")
            return
        # Показываем список рабочих центров
        await show_rc_types(update, user_id)

    elif data == 'set_description':
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для заполнения формы.")
            return
        # Запрашиваем описание
        await query.edit_message_text(text="Введите описание вопроса:")
        user_states[user_id]['current_input'] = 'description'

    # === ОБРАБОТКА КНОПКИ ФОТО ===
    elif data == 'set_photo':
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для заполнения формы.")
            return
        await request_photo(update, context)

    elif data == 'cancel_photo':
        user_id = str(query.from_user.id)
        # Отменяем ожидание фото
        if 'waiting_for_photo' in user_states[user_id]:
            del user_states[user_id]['waiting_for_photo']
        # Возвращаемся в меню заявки
        await show_application_menu(update, user_id)

    elif data.startswith('problem_'):
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для заполнения формы.")
            return
        # Сохраняем выбранный тип проблемы
        problem_index = int(data.split('_')[1])
        selected_problem = PROBLEM_TYPES[problem_index]
        user_states[user_id]['problem_type'] = selected_problem

        # Возвращаемся к меню заявки
        await show_application_menu(update, user_id)
        print(f"💾 Сохранен вид проблемы: {selected_problem}")

    elif data.startswith('rc_'):
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для заполнения формы.")
            return
        # Сохраняем выбранный рабочий центр
        rc_index = int(data.split('_')[1])
        selected_rc = RC_TYPES[rc_index]
        user_states[user_id]['rc'] = selected_rc

        # Возвращаемся к меню заявки
        await show_application_menu(update, user_id)
        print(f"💾 Сохранен рабочий центр (РЦ): {selected_rc}")


    # === ОБРАБОТКА КНОПКИ ЧАТА ===
    elif data == 'chat_dse_menu':
        if not has_permission(user_id, 'chat_dse'):
            await query.edit_message_text("❌ У вас нет прав для чата по ДСЕ.")
            return
        # Открываем меню чата С ВЫБОРОМ ИЗ СПИСКА
        await start_dse_chat_search_with_selection(update, context)

        # === ОБРАБОТКА КНОПОК УПРАВЛЕНИЯ ЧАТОМ (из chat_manager) ===
    elif data in ['chat_pause', 'chat_resume', 'chat_end']:
        from chat_manager import handle_chat_control
        await handle_chat_control(update, context)

        # === ОБРАБОТКА ПОДТВЕРЖДЕНИЯ ЧАТА ПО ДСЕ (из chat_manager) ===
    elif data in ['dse_chat_confirm', 'dse_chat_cancel_final']:
        from chat_manager import handle_dse_chat_confirmation
        await handle_dse_chat_confirmation(update, context)

        # === ОБРАБОТКА ВЫБОРА ПОЛЬЗОВАТЕЛЯ ДЛЯ ЧАТА ПО ДСЕ (из chat_manager) ===
    elif data.startswith('dse_chat_select_'):
        from chat_manager import handle_dse_user_selection
        await handle_dse_user_selection(update, context)

        # === НОВАЯ ОБРАБОТКА: ПОДТВЕРЖДЕНИЕ/ОТМЕНА ОТ ИНИЦИАТОРА ===
    elif data in ['dse_chat_confirm_initiator', 'dse_chat_cancel_initiator']:
        # callback_data для инициатора
        from chat_manager import handle_initiator_confirmation
        await handle_initiator_confirmation(update, context)

        # === НОВАЯ ОБРАБОТКА: ПОДТВЕРЖДЕНИЕ/ОТМЕНА ОТ ОТВЕТЧИКА ===
        # Предполагаем, что callback_data имеет формат:
        # 'dse_chat_confirm_responder_INITIATOR_ID' или 'dse_chat_cancel_responder_INITIATOR_ID'
    elif '_responder_' in data:
        # callback_data для ответчика
        from chat_manager import handle_responder_confirmation
        await handle_responder_confirmation(update, context)




# === ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений и фото"""

    user = update.effective_user
    user_id = str(user.id)

    # Проверяем, есть ли текст в сообщении
    text = ""
    if update.message.text:
        text = update.message.text
    elif update.message.caption:  # Если это фото с подписью
        text = update.message.caption

    print(f"👨 @{user.username}: {text if text else '[ФОТО/ДРУГОЕ]'}")

    # === ПРОВЕРКА НА ФОТО ===
    # Проверяем, ожидаем ли мы фото от пользователя
    if user_id in user_states and user_states[user_id].get('waiting_for_photo'):
        if update.message.photo:
            # Получаем file_id самого большого фото (последнего в массиве)
            photo_file_id = update.message.photo[-1].file_id

            # Сохраняем file_id фото в состоянии пользователя
            user_states[user_id]['photo_file_id'] = photo_file_id
            # Убираем флаг ожидания фото
            del user_states[user_id]['waiting_for_photo']

            await update.message.reply_text("✅ Фото сохранено!")
            await show_application_menu(update, context)  # Возвращаем в меню заявки
            return  # Важно: выходим
        elif update.message.text and update.message.text.startswith('/'):
            # Если пользователь отправил команду, не обрабатываем как фото
            pass  # Позволим другим обработчикам команд заняться этим
        else:
            # Если пользователь отправил текст, а не фото
            await update.message.reply_text(
                "📸 Пожалуйста, отправьте фото.\n"
                "Используйте /cancel_photo для отмены."
            )
            return  # Важно: выходим, чтобы не попасть в другие обработчики

    # === ПРОВЕРКА НА АКТИВНЫЙ ЧАТ ===
    # Проверяем, находится ли пользователь в активном чате или чате с управлением
    from chat_manager import active_chats, handle_chat_message
    if user_id in active_chats and active_chats[user_id].get('status') in ['active', 'paused']:
        await handle_chat_message(update, context)
        return

    # === ПРОВЕРКА НА АДМИНСКИЕ И ПОИСКОВЫЕ СОСТОЯНИЯ ===
    # Проверяем, ожидаем ли мы ID пользователя для изменения роли (админ)
    if user_id in admin_states and admin_states[user_id].get('changing_role'):
        target_user_id = text.strip()
        users = get_all_users()

        if target_user_id in users:
            del admin_states[user_id]  # Очищаем состояние

            # Создаем фейковый update для корректной работы
            class FakeUpdate:
                def __init__(self, message):
                    self.message = message
                    self.callback_query = None
                    self.effective_user = message.from_user

            fake_update = FakeUpdate(update.message)
            await show_role_selection_menu(fake_update, context, target_user_id)
        else:
            await update.message.reply_text(
                "❌ Пользователь с таким ID не найден. Попробуйте еще раз или нажмите /start")
        return

    # Проверяем, ожидаем ли мы email для отправки файла экспорта (админ)
    if user_id in admin_states and admin_states[user_id].get('waiting_for_email'):
        email = text.strip()
        
        # Простая проверка формата email
        if '@' in email and '.' in email:
            # Очищаем флаг ожидания email
            admin_states[user_id].pop('waiting_for_email', None)
            await send_file_by_email(update, context, email)
        else:
            await update.message.reply_text(
                "❌ Неверный формат email. Пожалуйста, введите корректный email адрес.\n"
                "Пример: user@example.com"
            )
        return

    # Проверяем, ожидаем ли мы ввод клички (админ)
    if user_id in admin_states and admin_states[user_id].get('setting_nickname'):
        nickname = text.strip()
        target_user_id = admin_states[user_id].get('setting_nickname_for')
        
        # Проверяем длину клички
        if len(nickname) > 20:
            await update.message.reply_text("❌ Кличка слишком длинная (максимум 20 символов).")
            return
        
        # Проверяем, что кличка не пустая
        if not nickname:
            await update.message.reply_text("❌ Кличка не может быть пустой.")
            return
        
        # Проверяем, что такой клички нет у другого пользователя
        if check_nickname_exists(nickname):
            current_owner_id = None
            for uid, udata in get_all_users().items():
                if udata.get('nickname', '').lower() == nickname.lower():
                    current_owner_id = uid
                    break
            
            if current_owner_id != target_user_id:
                await update.message.reply_text(f"❌ Кличка '{nickname}' уже занята другим пользователем.")
                return
        
        # Устанавливаем кличку
        if set_user_nickname(target_user_id, nickname):
            users = get_all_users()
            target_user = users.get(target_user_id, {})
            user_name = target_user.get('first_name', 'Пользователь')
            
            await update.message.reply_text(f"✅ Кличка '{nickname}' установлена пользователю {user_name}.")
        else:
            await update.message.reply_text("❌ Ошибка при установке клички.")
        
        # Очищаем состояние
        admin_states[user_id].pop('setting_nickname', None)
        admin_states[user_id].pop('setting_nickname_for', None)
        return

    # Проверяем, ожидаем ли мы поисковый запрос для ДСЕ (интерактивный поиск)
    if user_id in dse_view_states and dse_view_states[user_id].get('searching_dse'):
        await handle_dse_search_input(update, context)
        return

    # Проверяем, ожидаем ли мы поисковый запрос для ДСЕ (обычный поиск)
    if user_id in dse_view_states:
        if dse_view_states[user_id].get('searching_dse'):
            del dse_view_states[user_id]

            # Создаем фейковый update для корректной работы
            class FakeUpdate:
                def __init__(self, message):
                    self.message = message
                    self.callback_query = None
                    self.effective_user = message.from_user

            fake_update = FakeUpdate(update.message)
            await show_search_results(fake_update, context, text, 'dse')
            return
        elif dse_view_states[user_id].get('searching_type'):
            del dse_view_states[user_id]

            # Создаем фейковый update для корректной работы
            class FakeUpdate:
                def __init__(self, message):
                    self.message = message
                    self.callback_query = None
                    self.effective_user = message.from_user

            fake_update = FakeUpdate(update.message)
            await show_search_results(fake_update, context, text, 'type')
            return

    # === ПРОВЕРКА НА ВВОД ДАННЫХ ДЛЯ ОТСЛЕЖИВАНИЯ ДСЕ ===
    # Проверяем, ожидаем ли мы ввод ДСЕ для добавления в список отслеживания
    # Обновляем условие, чтобы оно срабатывало только если явно установлен флаг ввода
    if (user_id in user_states and
            user_states[user_id].get('adding_watched_dse') and
            user_states[user_id].get('adding_watched_dse_state') != 'selecting_or_manual'):

        dse_to_watch = text.strip()
        if dse_to_watch:
            from dse_watcher import add_watched_dse
            add_watched_dse(user_id, dse_to_watch)

            # Очищаем состояние
            if 'adding_watched_dse' in user_states[user_id]:
                del user_states[user_id]['adding_watched_dse']
            if 'adding_watched_dse_state' in user_states[user_id]:
                del user_states[user_id]['adding_watched_dse_state']

            response = f"✅ ДСЕ '{dse_to_watch.upper()}' добавлено в список отслеживания."
            await update.message.reply_text(text=response)
            # Показываем меню отслеживания
            await show_watched_dse_menu(update, context)
        else:
            await update.message.reply_text("❌ Пожалуйста, введите корректный номер ДСЕ.")
        return  # Важно: выходим, чтобы не попасть в следующие условия

    # === ПРОВЕРКА НА ВВОД ДСЕ ДЛЯ ЧАТА ===
    elif (user_id in user_states and
          user_states[user_id].get('dse_chat_state') == 'waiting_for_dse_input'):

        # Очищаем состояние
        if 'dse_chat_state' in user_states[user_id]:
            del user_states[user_id]['dse_chat_state']

        # Передаем ввод в chat_manager
        from chat_manager import handle_dse_input
        await handle_dse_input(update, context)
        return  # Важно: выходим, чтобы не попасть в следующие условия

    # === ПРОВЕРКА НА ВВОД ДАННЫХ ДЛЯ ФОРМЫ ===
    # Проверяем, ожидаем ли мы ввод от пользователя (для формы)
    if user_id in user_states and 'current_input' in user_states[user_id]:
        current_input = user_states[user_id]['current_input']

        if current_input == 'dse':
            user_states[user_id]['dse'] = text
            print(f"💾 Сохранено ДСЕ: {text}")
        elif current_input == 'description':
            user_states[user_id]['description'] = text
            print(f"💾 Сохранено описание: {text}")

        # Удаляем флаг ожидания ввода
        del user_states[user_id]['current_input']

        # Показываем меню заявки снова
        response = f"✅ Сохранено: {text}"
        await update.message.reply_text(text=response)
        await show_application_menu(update, user_id)  # Возвращаем в меню заявки
        return  # Важно: выходим, чтобы не попасть в "Обычный ответ"

    # Обработка поиска ДСЕ для PDF
    elif user_states.get(user_id, {}).get('pdf_search_dse'):
        user_states[user_id]['pdf_search_dse'] = False
        await handle_pdf_dse_search(update, context)
        return

    else:
        # Обычный ответ на сообщение
        response = "Нажмите /start для начала работы с ботом"
        # response = f"{user_states[user_id].get('dse_chat_state')} {'waiting_for_dse_input'}"
        await update.message.reply_text(text=response)


# === PDF EXPORT FUNCTIONS ===

async def show_pdf_export_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать меню экспорта в PDF"""
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск по ДСЕ", callback_data='pdf_search_dse')],
        [InlineKeyboardButton("📋 Последние заявки", callback_data='pdf_recent_records')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📄 PDF Экспорт заявки\n\n"
    text += "Выберите способ поиска заявки:"
    
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


async def show_recent_records_for_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать последние записи для выбора PDF экспорта"""
    data = load_data(DATA_FILE)
    
    # Собираем все записи в один список
    all_records = []
    for user_id, user_records in data.items():
        for record in user_records:
            record['user_id'] = user_id  # Добавляем ID пользователя к записи
            all_records.append(record)
    
    # Сортируем по дате (новые сначала)
    all_records.sort(key=lambda x: x.get('datetime', ''), reverse=True)
    
    # Берем последние 10 записей
    recent_records = all_records[:10]
    
    if not recent_records:
        await update.callback_query.edit_message_text(
            "❌ Нет записей для экспорта в PDF",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]])
        )
        return
    
    # Сохраняем записи в сессию
    user_id = str(update.callback_query.from_user.id)
    pdf_session_records[user_id] = recent_records
    
    # Создаем кнопки
    keyboard = []
    for i, record in enumerate(recent_records):
        dse = record.get('dse', 'Нет ДСЕ')
        problem_type = record.get('problem_type', 'Нет типа')[:20]
        datetime_str = record.get('datetime', 'Нет даты')[:10]
        
        button_text = f"{dse} - {problem_type} ({datetime_str})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'pdf_select_{i}')])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📋 Выберите заявку для создания PDF:\n\n"
    
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


# Глобальная переменная для хранения записей PDF сессии
pdf_session_records = {}


async def start_pdf_dse_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать поиск ДСЕ для PDF экспорта"""
    user_id = str(update.callback_query.from_user.id)
    
    # Сохраняем состояние
    user_states[user_id] = user_states.get(user_id, {})
    user_states[user_id]['pdf_search_dse'] = True
    
    await update.callback_query.edit_message_text(
        "🔍 Введите ДСЕ для поиска заявки:"
    )


async def show_pdf_confirm_record(update: Update, context: ContextTypes.DEFAULT_TYPE, record: dict, index: int) -> None:
    """Показать подтверждение создания PDF для записи"""
    user_display = get_user_display_name(record.get('user_id', ''))
    
    text = f"📄 Создать PDF для заявки?\n\n"
    text += f"📋 ДСЕ: {record.get('dse', 'Не указано')}\n"
    text += f"🔧 РЦ: {record.get('rc', 'Не указано')}\n"
    text += f"⚠️ Тип проблемы: {record.get('problem_type', 'Не указано')}\n"
    text += f"📝 Описание: {record.get('description', 'Не указано')[:100]}...\n"
    text += f"📅 Дата: {record.get('datetime', 'Не указано')}\n"
    text += f"👤 Пользователь: {user_display}\n"
    
    keyboard = [
        [InlineKeyboardButton("✅ Создать PDF", callback_data=f'pdf_generate_{index}')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup)


async def handle_pdf_dse_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать поиск ДСЕ для PDF"""
    user_id = str(update.message.from_user.id)
    search_dse = update.message.text.strip().upper()
    
    # Ищем записи с данным ДСЕ
    data = load_data(DATA_FILE)
    found_records = []
    
    for user_id_data, user_records in data.items():
        for i, record in enumerate(user_records):
            if record.get('dse', '').upper() == search_dse:
                record['user_id'] = user_id_data
                record['record_index'] = f"{user_id_data}_{i}"
                found_records.append(record)
    
    if not found_records:
        await update.message.reply_text(
            f"❌ Заявки с ДСЕ '{search_dse}' не найдены.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]])
        )
        return
    
    # Сохраняем найденные записи
    pdf_session_records[user_id] = found_records
    
    if len(found_records) == 1:
        # Если только одна запись, сразу предлагаем создать PDF
        record = found_records[0]
        await show_pdf_confirm_record(update, context, record, 0)
    else:
        # Если несколько записей, показываем выбор
        await show_pdf_search_results(update, context, found_records)


async def show_pdf_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, records: list) -> None:
    """Показать результаты поиска для выбора PDF"""
    keyboard = []
    
    for i, record in enumerate(records):
        problem_type = record.get('problem_type', 'Нет типа')[:25]
        datetime_str = record.get('datetime', 'Нет даты')[:16]
        user_display = get_user_display_name(record.get('user_id', ''))
        
        button_text = f"{problem_type} - {datetime_str} ({user_display})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'pdf_select_{i}')])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🔍 Найдено {len(records)} заявок с ДСЕ '{records[0].get('dse', '')}':\n\n"
    text += "Выберите заявку для создания PDF:"
    
    await update.message.reply_text(text=text, reply_markup=reply_markup)


async def generate_pdf_report(update: Update, context: ContextTypes.DEFAULT_TYPE, record: dict) -> None:
    """Генерировать PDF отчет для заявки"""
    await update.callback_query.edit_message_text("📄 Создание PDF отчета...")
    
    try:
        # Импортируем наш PDF генератор
        from pdf_generator import create_dse_pdf_report
        
        # Подготавливаем данные для PDF
        pdf_data = {
            'dse': record.get('dse', 'Не указано'),
            'rc': record.get('rc', 'Не указано'),
            'problem_type': record.get('problem_type', 'Не указано'),
            'description': record.get('description', 'Не указано'),
            'datetime': record.get('datetime', 'Не указано'),
            'user_display': get_user_display_name(record.get('user_id', ''))
        }
        
        # Создаем имя файла
        dse_safe = record.get('dse', 'unknown').replace('/', '_').replace('\\', '_')
        date_str = record.get('datetime', 'unknown')[:10].replace('-', '') if record.get('datetime') else 'unknown'
        pdf_filename = f"dse_report_{dse_safe}_{date_str}.pdf"
        
        # Генерируем PDF
        created_filename = create_dse_pdf_report(pdf_data, pdf_filename)
        
        if created_filename and os.path.exists(created_filename):
            # Отправляем файл пользователю
            with open(created_filename, 'rb') as f:
                await context.bot.send_document(
                    chat_id=update.callback_query.from_user.id,
                    document=f,
                    filename=created_filename,
                    caption=f"📄 PDF отчет для ДСЕ: {record.get('dse', 'unknown')}"
                )
            
            # Удаляем временный файл
            os.remove(created_filename)
            
            await update.callback_query.edit_message_text(
                f"✅ PDF отчет успешно создан и отправлен!\n\n"
                f"📋 ДСЕ: {record.get('dse', 'Не указано')}\n"
                f"📄 Файл: {created_filename}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В главное меню", callback_data='back_to_main')]])
            )
        else:
            raise Exception("Не удалось создать PDF файл")
        
    except Exception as e:
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при создании PDF отчета: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]])
        )
