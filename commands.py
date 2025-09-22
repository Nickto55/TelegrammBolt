# commands.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import load_data, save_data, PROBLEM_TYPES, DATA_FILE
from dse_manager import get_all_dse_records, search_dse_records
from user_manager import register_user, get_user_role, has_permission, set_user_role, ROLES, get_all_users

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
        # Инициализируем данные пользователя для формы
        user_states[user_id] = {
            'application': '',  # Будет содержать "started" когда заявка начата
            'dse': '',
            'problem_type': '',
            'description': ''
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
    user_data = user_states.get(user_id, {'application': '', 'dse': '', 'problem_type': '', 'description': ''})

    # Создаем кнопки с индикаторами заполненности для каждого поля
    dse_text = f"ДСЕ ✅" if user_data['dse'] else "ДСЕ"
    problem_text = f"Вид проблемы ✅" if user_data['problem_type'] else "Вид проблемы"
    desc_text = f"Описание вопроса ✅" if user_data['description'] else "Описание вопроса"

    # Кнопки для заполнения полей
    keyboard = [
        [InlineKeyboardButton(dse_text, callback_data='set_dse')],
        [InlineKeyboardButton(problem_text, callback_data='set_problem')],
        [InlineKeyboardButton(desc_text, callback_data='set_description')],
    ]

    # Кнопки отправки и возврата, если все поля заполнены
    if all([user_data['dse'], user_data['problem_type'], user_data['description']]):
        keyboard.append([InlineKeyboardButton("📤 Отправить", callback_data='send')])
        keyboard.append([InlineKeyboardButton("🔄 Изменить", callback_data='edit_application')])

    # Кнопка возврата в главное меню
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = "📝 Заполните заявку:\n\n"
    welcome_text += (
        f"• {dse_text}\n"
        f"• {problem_text}\n"
        f"• {desc_text}\n\n"
    )
    if all([user_data['dse'], user_data['problem_type'], user_data['description']]):
        welcome_text += "После заполнения появятся кнопки отправки."

    if update.callback_query:
        await update.callback_query.edit_message_text(text=welcome_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)


async def show_main_menu(update: Update, user_id: str) -> None:
    """Показать главное меню с кнопками"""
    user_data = user_states.get(user_id, {'application': '', 'dse': '', 'problem_type': '', 'description': ''})
    role = get_user_role(user_id)

    keyboard = []

    # Заменяем отдельные кнопки полей на одну кнопку "Заявка"
    if has_permission(user_id, 'use_form'):
        # Показываем кнопку "Заявка" с индикатором, если заявка частично или полностью заполнена
        app_status = user_data.get('application', '')
        dse_filled = user_data.get('dse', '')
        problem_filled = user_data.get('problem_type', '')
        desc_filled = user_data.get('description', '')

        if app_status == 'started' or any([dse_filled, problem_filled, desc_filled]):
            app_text = "📝 Заявка ⚠️"  # ⚠️ если начата, но не завершена
            if all([dse_filled, problem_filled, desc_filled]):
                app_text = "📝 Заявка ✅"  # ✅ если полностью заполнена
        else:
            app_text = "📝 Заявка"

        keyboard.append([InlineKeyboardButton(app_text, callback_data='open_application')])

    # === КНОПКА 6: "📋 Список ДСЕ" ===
    if has_permission(user_id, 'view_dse_list'):
        keyboard.append([InlineKeyboardButton("📋 Список ДСЕ", callback_data='view_dse_list')])

    # === КНОПКА 7: "👀 Отслеживание ДСЕ" ===
    if has_permission(user_id, 'view_dse_list'):  # Используем то же право
        keyboard.append([InlineKeyboardButton("👀 Отслеживание ДСЕ", callback_data='watch_dse_menu')])

    # === КНОПКА 8: "💬 Чат по ДСЕ" ===
    if has_permission(user_id, 'chat_dse'):
        keyboard.append([InlineKeyboardButton("💬 Чат по ДСЕ", callback_data='chat_dse_menu')])

    # === КНОПКА 9: "🔧 Управление пользователями" ===
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
        [InlineKeyboardButton("📋 Все записи", callback_data='dse_view_all')],
        [InlineKeyboardButton("🔍 Поиск по ДСЕ", callback_data='dse_search_dse')],
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
        text += f"   Описание: {record.get('description', 'Не указано')[:50]}...\n"
        text += f"   Пользователь ID: {record.get('user_id', 'Неизвестно')}\n\n"

    # Создаем кнопки навигации
    nav_buttons = []

    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'dse_view_all_{page - 1}'))

    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f'dse_view_all_{page + 1}'))

    # Кнопка возврата в меню
    nav_buttons.append(InlineKeyboardButton("↩️ Меню", callback_data='view_dse_list'))

    keyboard = []
    if nav_buttons:
        keyboard.append(nav_buttons)

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
            text += f"   Описание: {record.get('description', 'Не указано')[:50]}...\n\n"

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
            text += f"   Описание: {record.get('description', 'Не указано')[:50]}...\n\n"

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
    for record in records:
        problem_type = record.get('problem_type', 'Не указано')
        problem_counts[problem_type] = problem_counts.get(problem_type, 0) + 1

    # Подсчет уникальных ДСЕ
    unique_dse = len(set([r.get('dse', '') for r in records if r.get('dse', '')]))

    text = "📊 Статистика по ДСЕ:\n\n"
    text += f"Всего записей: {total_records}\n"
    text += f"Уникальных ДСЕ: {unique_dse}\n\n"
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


# === АДМИН ФУНКЦИИ ===

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать админское меню"""
    keyboard = [
        [InlineKeyboardButton("👥 Список пользователей", callback_data='admin_list_users')],
        [InlineKeyboardButton("✏️ Изменить роль пользователя", callback_data='admin_change_role_start')],
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
        name = user_data.get('first_name', 'Неизвестно')
        username = user_data.get('username', '')
        if username:
            text += f"• {name} (@{username}) - {role_text} (ID: {user_id})\n"
        else:
            text += f"• {name} - {role_text} (ID: {user_id})\n"

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

async def show_watched_dse_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать меню отслеживания ДСЕ."""
    user = update.effective_user
    user_id = str(user.id)

    # Проверяем права доступа
    if not has_permission(user_id, 'view_dse_list'):
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

    # Устанавливаем состояние ожидания ввода ДСЕ для добавления
    user_states[user_id] = user_states.get(user_id, {})
    user_states[user_id]['adding_watched_dse'] = True

    await update.callback_query.edit_message_text("➕ Введите номер ДСЕ для отслеживания:")


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
    watched_list = get_watched_dse_list(user_id)

    if not watched_list:
        text = "📭 Ваш список отслеживаемых ДСЕ пуст.\n\n"
        text += "Нажмите '➕ Добавить ДСЕ' в меню отслеживания, чтобы начать."
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='watch_dse_menu')]]
    else:
        text = "📋 Список отслеживаемых ДСЕ:\n\n"
        for i, dse_value in enumerate(watched_list, 1):
            text += f"{i}. {dse_value.upper()}\n"
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='watch_dse_menu')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


# === ОСНОВНОЙ ОБРАБОТЧИК КНОПОК ===

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий кнопок"""

    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    data = query.data

    print(f"🖱️ {user.first_name}: нажал кнопку '{data}'")

    # Проверяем права доступа
    if not has_permission(user_id, 'view_main_menu'):
        await query.edit_message_text("❌ У вас нет прав для использования этой функции.")
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
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для отправки формы.")
            return
        user_data = user_states.get(user_id, {})
        if all([user_data.get('dse'), user_data.get('problem_type'), user_data.get('description')]):
            # Загружаем существующие данные
            all_data = load_data(DATA_FILE)

            # Добавляем новые данные
            if user_id not in all_data:
                all_data[user_id] = []

            all_data[user_id].append({
                'dse': user_data['dse'],
                'problem_type': user_data['problem_type'],
                'description': user_data['description']
            })

            # Сохраняем в файл
            save_data(all_data, DATA_FILE)

            # Очищаем временные данные ЗАЯВКИ, но оставляем application = 'started'
            if user_id in user_states:
                user_states[user_id] = {
                    'application': 'started',  # Оставляем признак начатой заявки
                    'dse': '',
                    'problem_type': '',
                    'description': ''
                }

            response = "✅ Данные успешно отправлены и сохранены!"
            await query.edit_message_text(text=response)
            print(f"📤 Бот: {response}")

            # После отправки возвращаем в главное меню
            await show_main_menu(update, user_id)
        else:
            await query.edit_message_text(text="❌ Ошибка: не все поля заполнены!")

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
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        from dse_watcher import load_watched_dse_data  # Убедимся, что данные загружены
        load_watched_dse_data()
        await show_watched_dse_menu(update, context)

    elif data == 'watch_add_dse':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        await start_add_watched_dse(update, context)

    elif data == 'watch_remove_dse':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        await start_remove_watched_dse(update, context)

    elif data == 'watch_list_dse':
        if not has_permission(user_id, 'view_dse_list'):
            await query.edit_message_text("❌ У вас нет прав для отслеживания ДСЕ.")
            return
        await show_watched_dse_list(update, context)

    elif data.startswith('watch_rm_idx_'):
        if not has_permission(user_id, 'view_dse_list'):
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

    elif data == 'set_description':
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для заполнения формы.")
            return
        # Запрашиваем описание
        await query.edit_message_text(text="Введите описание вопроса:")
        user_states[user_id]['current_input'] = 'description'

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

    # === ОБРАБОТКА КНОПКИ ЧАТА ===
    elif data == 'chat_dse_menu':
        if not has_permission(user_id, 'chat_dse'):
            await query.edit_message_text("❌ У вас нет прав для чата по ДСЕ.")
            return
        # Открываем меню чата
        from chat_manager import show_chat_menu
        await show_chat_menu(update, context)

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


# === ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""

    user = update.effective_user
    user_id = str(user.id)
    text = update.message.text

    print(f"👨 @{user.username}: {text}")

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

    # Проверяем, ожидаем ли мы поисковый запрос для ДСЕ
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
    if user_id in user_states and user_states[user_id].get('adding_watched_dse'):
        dse_to_watch = text.strip()
        if dse_to_watch:
            from dse_watcher import add_watched_dse
            add_watched_dse(user_id, dse_to_watch)
            del user_states[user_id]['adding_watched_dse']  # Очищаем состояние
            response = f"✅ ДСЕ '{dse_to_watch.upper()}' добавлено в список отслеживания."
            await update.message.reply_text(text=response)
            # Показываем меню отслеживания
            await show_watched_dse_menu(update, context)
        else:
            await update.message.reply_text("❌ Пожалуйста, введите корректный номер ДСЕ.")
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

    else:
        # Обычный ответ на сообщение
        response = "Нажмите /start для начала работы с ботом"
        await update.message.reply_text(text=response)
