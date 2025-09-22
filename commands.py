from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import load_data, save_data, PROBLEM_TYPES, DATA_FILE
from user_manager import register_user, get_user_role, has_permission, set_user_role, ROLES, get_all_users
from dse_manager import get_all_dse_records, get_dse_records_by_user, search_dse_records, get_unique_dse_list

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


async def show_main_menu(update: Update, user_id: str) -> None:
    """Показать главное меню с кнопками"""
    user_data = user_states.get(user_id, {'dse': '', 'problem_type': '', 'description': ''})
    role = get_user_role(user_id)

    keyboard = []

    # Только инициаторы могут использовать форму
    if has_permission(user_id, 'use_form'):
        # Создаем кнопки с индикаторами заполненности
        dse_text = f"ДСЕ ✅" if user_data['dse'] else "ДСЕ"
        problem_text = f"Вид проблемы ✅" if user_data['problem_type'] else "Вид проблемы"
        desc_text = f"Описание вопроса ✅" if user_data['description'] else "Описание вопроса"

        keyboard = [
            [InlineKeyboardButton(dse_text, callback_data='set_dse')],
            [InlineKeyboardButton(problem_text, callback_data='set_problem')],
            [InlineKeyboardButton(desc_text, callback_data='set_description')]
        ]

        # Добавляем кнопки отправить/изменить, если все заполнено
        if all([user_data['dse'], user_data['problem_type'], user_data['description']]):
            keyboard.append([InlineKeyboardButton("📤 Отправить", callback_data='send')])
            keyboard.append([InlineKeyboardButton("🔄 Изменить", callback_data='edit')])

    # Добавляем кнопку просмотра ДСЕ для ответчиков и выше
    if has_permission(user_id, 'view_dse_list'):
        keyboard.append([InlineKeyboardButton("📋 Список ДСЕ", callback_data='view_dse_list')])

    # Добавляем кнопку чата для ответчиков и админов
    if has_permission(user_id, 'chat_dse'):
        keyboard.append([InlineKeyboardButton("💬 Чат по ДСЕ", callback_data='chat_dse_menu')])

    # Админские функции
    if role == 'admin':
        keyboard.append([InlineKeyboardButton("🔧 Управление пользователями", callback_data='admin_users')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    role_text = ROLES.get(role, 'Пользователь')
    welcome_text = f"👤 Роль: {role_text}\n\n"

    if has_permission(user_id, 'use_form'):
        welcome_text += (
            "📝 Заполните все поля:\n"
            f"• {dse_text}\n"
            f"• {problem_text}\n"
            f"• {desc_text}\n\n"
        )
        if all([user_data['dse'], user_data['problem_type'], user_data['description']]):
            welcome_text += "После заполнения появятся кнопки отправки."
    else:
        welcome_text += "У вас ограниченный доступ к функциям бота."

    if update.callback_query:
        await update.callback_query.edit_message_text(text=welcome_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)


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

    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="Выберите вид проблемы:",
        reply_markup=reply_markup
    )


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

    # Обработка кнопок просмотра ДСЕ
    if data == 'view_dse_list':
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

    # Обработка админских кнопок
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

    # Обычные кнопки (оставляем как есть)
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

        # Возвращаемся к главному меню
        await show_main_menu(update, user_id)
        print(f"💾 Сохранен вид проблемы: {selected_problem}")

    elif data == 'back_to_main':
        # Возврат к главному меню
        await show_main_menu(update, user_id)

    elif data == 'send':
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для отправки формы.")
            return
        # Отправка данных
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

            # Очищаем временные данные
            user_states[user_id] = {'dse': '', 'problem_type': '', 'description': ''}

            response = "✅ Данные успешно отправлены и сохранены!"
            await query.edit_message_text(text=response)
            print(f"📤 Бот: {response}")
        else:
            await query.edit_message_text(text="❌ Ошибка: не все поля заполнены!")

    elif data == 'edit':
        if not has_permission(user_id, 'use_form'):
            await query.edit_message_text("❌ У вас нет прав для редактирования формы.")
            return
        # Возвращаем к редактированию
        await show_main_menu(update, user_id)
        print(f"📤 Бот: возврат к редактированию")

    elif data == 'chat_dse_menu':
        if not has_permission(user_id, 'chat_dse'):
            await query.edit_message_text("❌ У вас нет прав для чата по ДСЕ.")
            return
        # Открываем меню чата



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""

    user = update.effective_user
    user_id = str(user.id)
    text = update.message.text

    print(f"👨 @{user.username}: {text}")

    # Проверяем, находится ли пользователь в чате
    from chat_manager import active_chats, waiting_users
    if user_id in active_chats or user_id in waiting_users:
        return

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

        # Показываем меню снова
        response = f"✅ Сохранено: {text}"
        await update.message.reply_text(text=response)
        await show_main_menu(update, user_id)
    else:
        # Обычный ответ на сообщение
        response = "Нажмите /start для начала работы с ботом"
        await update.message.reply_text(text=response)