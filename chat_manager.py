# chat_manager.py

import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import load_data, DATA_FILE, USERS_FILE

# Глобальные переменные для управления состоянием чата по ДСЕ
# {admin_user_id: {'state': 'waiting_for_dse'/'waiting_for_user_selection'/'waiting_for_confirmation', 'dse': '...', 'candidates': [], 'selected_candidate': {...}}}
dse_chat_states = {}
# active_chats теперь будет словарем словарей для хранения дополнительной информации
# {user1_id: {'partner_id': user2_id, 'status': 'active'/'paused'}, user2_id: {'partner_id': user1_id, 'status': 'active'/'paused'}}
active_chats = {}


def get_users_data():
    """Получить данные пользователей из файла."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке данных пользователей: {e}")
            return {}
    return {}


def get_dse_records_by_dse_value(dse_value: str):
    """
    Получить список записей (с информацией о пользователях) по значению ДСЕ.
    Возвращает список словарей вида:
    [{'user_id': '...', 'dse': '...', 'problem_type': '...', 'description': '...'}, ...]
    """
    all_bot_data = load_data(DATA_FILE)
    matching_records = []

    # all_bot_data - это словарь {user_id: [record1, record2, ...]}
    for user_id, user_records in all_bot_data.items():
        if isinstance(user_records, list):
            for record in user_records:
                # Сравниваем, игнорируя регистр и пробелы по краям
                if record.get('dse', '').strip().lower() == dse_value.strip().lower():
                    record_copy = record.copy()
                    record_copy['user_id'] = user_id  # Добавляем ID пользователя в запись
                    matching_records.append(record_copy)

    return matching_records


async def initiate_dse_chat_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс поиска чата по ДСЕ. Запрашивает у пользователя номер ДСЕ."""
    user = update.effective_user
    user_id = str(user.id)

    # Инициализируем состояние пользователя для процесса чата по ДСЕ
    dse_chat_states[user_id] = {'state': 'waiting_for_dse', 'dse': None, 'candidates': []}

    # Отправляем запрос на ввод ДСЕ
    # Проверяем, откуда пришел запрос (из callback_query или обычного сообщения)
    if update.callback_query:
        await update.callback_query.edit_message_text("🔍 Пожалуйста, введите номер ДСЕ для поиска:")
    elif update.message:
        await update.message.reply_text("🔍 Пожалуйста, введите номер ДСЕ для поиска:")

    print(f"💬 {user.first_name} начал поиск чата по ДСЕ.")


async def handle_dse_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ввод номера ДСЕ пользователем."""
    user = update.effective_user
    user_id = str(user.id)
    dse_value = update.message.text.strip()

    # Проверяем, находится ли пользователь в процессе поиска ДСЕ
    if user_id not in dse_chat_states or dse_chat_states[user_id]['state'] != 'waiting_for_dse':
        # Если нет, проверяем, не в активном ли он чате
        if user_id in active_chats and active_chats[user_id].get('status') == 'active':
            await handle_chat_message(update, context)
        return

    # Сохраняем введённый ДСЕ
    dse_chat_states[user_id]['dse'] = dse_value
    dse_chat_states[user_id]['state'] = 'processing'

    # Ищем записи с этим ДСЕ
    records = get_dse_records_by_dse_value(dse_value)

    if not records:
        del dse_chat_states[user_id]  # Очищаем состояние
        await update.message.reply_text(f"❌ По запросу ДСЕ '{dse_value}' ничего не найдено.")
        print(f"💬 Для {user.first_name} ничего не найдено по ДСЕ '{dse_value}'.")
        return

    # Фильтруем, чтобы не предлагать чат с самим собой
    candidate_records = [r for r in records if r['user_id'] != user_id]

    if not candidate_records:
        del dse_chat_states[user_id]  # Очищаем состояние
        await update.message.reply_text(f"❌ По ДСЕ '{dse_value}' найдены только ваши собственные записи.")
        print(f"💬 Для {user.first_name} по ДСЕ '{dse_value}' найдены только свои записи.")
        return

    # Сохраняем кандидатов
    dse_chat_states[user_id]['candidates'] = candidate_records
    dse_chat_states[user_id]['state'] = 'waiting_for_user_selection'

    # Получаем данные пользователей для отображения имен
    users_data = get_users_data()

    # Создаем кнопки для выбора пользователя
    keyboard = []
    for i, record in enumerate(candidate_records):
        candidate_user_id = record['user_id']
        candidate_user_info = users_data.get(candidate_user_id, {})
        candidate_name = candidate_user_info.get('first_name', f"Пользователь {candidate_user_id}")

        # Создаем уникальный callback_data для каждой кнопки
        # Используем префикс 'dse_chat_select_' как в button_handler
        callback_data = f"dse_chat_select_{i}"
        button_text = f"{candidate_name} (ID: {candidate_user_id})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="dse_chat_cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Найдено {len(candidate_records)} записей по ДСЕ '{dse_value}'.\nПожалуйста, выберите пользователя для связи:",
        reply_markup=reply_markup
    )
    print(f"💬 Для {user.first_name} найдено {len(candidate_records)} кандидатов по ДСЕ '{dse_value}'.")


async def handle_dse_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор пользователя из списка кандидатов."""
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки

    selecting_user = query.from_user
    selecting_user_id = str(selecting_user.id)
    callback_data = query.data

    # Проверяем, находится ли пользователь в нужном состоянии
    if (selecting_user_id not in dse_chat_states or
            dse_chat_states[selecting_user_id]['state'] != 'waiting_for_user_selection'):
        await query.edit_message_text("❌ Ошибка состояния. Пожалуйста, начните процесс заново.")
        print(
            f"❌ {selecting_user.first_name} ошибка состояния в handle_dse_user_selection. Текущее состояние: {dse_chat_states.get(selecting_user_id, {}).get('state', 'None')}")
        return

    if callback_data == "dse_chat_cancel":
        del dse_chat_states[selecting_user_id]
        await query.edit_message_text("↩️ Поиск чата по ДСЕ отменен.")
        print(f"💬 {selecting_user.first_name} отменил выбор пользователя.")
        return

    # Извлекаем индекс выбранного кандидата
    try:
        # callback_data = 'dse_chat_select_{index}'
        parts = callback_data.split('_')
        if len(parts) >= 4 and parts[0] == 'dse' and parts[1] == 'chat' and parts[2] == 'select':
            index_str = parts[3]
            index = int(index_str)
        else:
            raise ValueError("Invalid callback_data format")
    except (ValueError, IndexError) as e:
        print(f"❌ Ошибка парсинга callback_data '{callback_data}': {e}")
        await query.edit_message_text("❌ Ошибка при обработке выбора. Пожалуйста, попробуйте снова.")
        return

    # Проверяем, существует ли запись о кандидатах и корректен ли индекс
    if (selecting_user_id not in dse_chat_states or
            'candidates' not in dse_chat_states[selecting_user_id]):
        await query.edit_message_text("❌ Ошибка данных. Пожалуйста, начните поиск чата по ДСЕ заново.")
        print(f"❌ {selecting_user.first_name} ошибка данных: нет кандидатов в состоянии.")
        return

    candidates = dse_chat_states[selecting_user_id]['candidates']
    print(f"🔍 {selecting_user.first_name} выбрал индекс {index}. Доступно кандидатов: {len(candidates)}")

    if index < 0 or index >= len(candidates):
        await query.edit_message_text("❌ Неверный выбор. Пожалуйста, попробуйте снова.")
        print(f"❌ {selecting_user.first_name} неверный индекс {index} для {len(candidates)} кандидатов.")
        return

    selected_record = candidates[index]
    # Сохраняем выбранного кандидата в состоянии
    dse_chat_states[selecting_user_id]['selected_candidate'] = selected_record
    # Устанавливаем правильное следующее состояние
    dse_chat_states[selecting_user_id]['state'] = 'waiting_for_confirmation'

    target_user_id = selected_record['user_id']
    dse_value = selected_record['dse']

    # Получаем имя инициатора для отображения
    users_data = get_users_data()
    target_user_info = users_data.get(target_user_id, {})
    target_name = target_user_info.get('first_name', f"Пользователь {target_user_id}")

    # Создаем кнопки подтверждения
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="dse_chat_confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="dse_chat_cancel_final")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"❓ Вы уверены, что хотите начать чат с {target_name} по ДСЕ '{dse_value}'?",
        reply_markup=reply_markup
    )


async def handle_dse_chat_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает подтверждение начала чата."""
    query = update.callback_query
    await query.answer()

    selecting_user = query.from_user
    selecting_user_id = str(selecting_user.id)
    callback_data = query.data

    # Проверяем, находится ли пользователь в нужном состоянии
    # Проверяем 'waiting_for_confirmation'
    if (selecting_user_id not in dse_chat_states or
            dse_chat_states[selecting_user_id]['state'] != 'waiting_for_confirmation'):
        if selecting_user_id in active_chats:
            # Возможно, пользователь уже в чате, обработаем как команду чата
            await handle_chat_control(update, context)
            return
        await query.edit_message_text("❌ Ошибка состояния. Пожалуйста, начните процесс заново.")
        print(
            f"❌ {selecting_user.first_name} ошибка состояния в handle_dse_chat_confirmation. Текущее состояние: {dse_chat_states.get(selecting_user_id, {}).get('state', 'None')}")
        return

    if callback_data == "dse_chat_cancel_final":
        del dse_chat_states[selecting_user_id]
        await query.edit_message_text("↩️ Начало чата отменено.")
        print(f"💬 {selecting_user.first_name} отменил начало чата.")
        return

    if callback_data == "dse_chat_confirm":
        # Проверяем, есть ли выбранный кандидат
        if ('selected_candidate' not in dse_chat_states[selecting_user_id]):
            await query.edit_message_text("❌ Ошибка данных. Пожалуйста, начните процесс заново.")
            print(f"❌ {selecting_user.first_name} ошибка данных: нет selected_candidate.")
            return

        selected_record = dse_chat_states[selecting_user_id]['selected_candidate']
        target_user_id = selected_record['user_id']
        dse_value = selected_record['dse']

        # Проверка, не находится ли уже один из пользователей в активном чате
        # Для простоты, разрешаем только один активный чат на пользователя
        if selecting_user_id in active_chats and active_chats[selecting_user_id].get('status') == 'active':
            del dse_chat_states[selecting_user_id]
            await query.edit_message_text("❌ Вы уже находитесь в активном чате.")
            return

        if target_user_id in active_chats and active_chats[target_user_id].get('status') == 'active':
            del dse_chat_states[selecting_user_id]
            await query.edit_message_text("❌ Выбранный пользователь уже находится в чате.")
            return

        # Устанавливаем активный чат со статусом 'active'
        active_chats[selecting_user_id] = {'partner_id': target_user_id, 'status': 'active'}
        active_chats[target_user_id] = {'partner_id': selecting_user_id, 'status': 'active'}

        # Очищаем временное состояние поиска
        del dse_chat_states[selecting_user_id]

        # Уведомляем инициатора (target_user)
        try:
            # Создаем кнопки управления для инициатора
            initiator_keyboard = get_chat_control_keyboard()
            initiator_reply_markup = InlineKeyboardMarkup(initiator_keyboard)

            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💬 С вами хочет связаться пользователь {selecting_user.first_name} по ДСЕ '{dse_value}'.\nВы можете отвечать на сообщения прямо здесь.",
                reply_markup=initiator_reply_markup
            )
            print(f"🔔 Уведомление отправлено инициатору {target_user_id} по ДСЕ '{dse_value}'.")
        except Exception as e:
            # Если не удалось уведомить инициатора, отменяем чат
            active_chats.pop(selecting_user_id, None)
            active_chats.pop(target_user_id, None)
            await query.edit_message_text("❌ Не удалось связаться с пользователем. Возможно, он заблокировал бота.")
            print(f"❌ Ошибка уведомления инициатора {target_user_id}: {e}")
            return

        # Уведомляем ответчика (selecting_user), что чат установлен, с кнопками управления
        responder_keyboard = get_chat_control_keyboard()
        responder_reply_markup = InlineKeyboardMarkup(responder_keyboard)

        await query.edit_message_text(
            f"✅ Чат с пользователем по ДСЕ '{dse_value}' установлен!\nМожете начинать писать сообщения.",
            reply_markup=responder_reply_markup
        )
        print(f"💬 Чат установлен между {selecting_user.first_name} и {target_user_id} по ДСЕ '{dse_value}'.")


def get_chat_control_keyboard():
    """Создает клавиатуру с кнопками управления чатом."""
    return [
        [InlineKeyboardButton("⏸️ Пауза", callback_data="chat_pause")],
        [InlineKeyboardButton("⏹️ Завершить чат", callback_data="chat_end")]
    ]


async def handle_chat_control(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия кнопок управления чатом."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    callback_data = query.data

    # Проверяем, находится ли пользователь в активном чате
    if user_id not in active_chats:
        await query.edit_message_text("❌ Вы не находитесь в активном чате.", reply_markup=None)
        return

    chat_info = active_chats[user_id]
    partner_id = chat_info['partner_id']
    current_status = chat_info['status']

    if callback_data == "chat_pause":
        if current_status == 'active':
            # Ставим чат на паузу для обоих пользователей
            active_chats[user_id]['status'] = 'paused'
            if partner_id in active_chats:
                active_chats[partner_id]['status'] = 'paused'

            # Обновляем клавиатуру на "Продолжить"
            keyboard = [
                [InlineKeyboardButton("▶️ Продолжить", callback_data="chat_resume")],
                [InlineKeyboardButton("⏹️ Завершить чат", callback_data="chat_end")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text("⏸️ Чат поставлен на паузу.", reply_markup=reply_markup)

            # Уведомляем партнера
            try:
                partner_keyboard = [
                    [InlineKeyboardButton("▶️ Продолжить", callback_data="chat_resume")],
                    [InlineKeyboardButton("⏹️ Завершить чат", callback_data="chat_end")]
                ]
                partner_reply_markup = InlineKeyboardMarkup(partner_keyboard)
                await context.bot.send_message(
                    chat_id=partner_id,
                    text="⏸️ Собеседник поставил чат на паузу.",
                    reply_markup=partner_reply_markup
                )
            except:
                pass
            print(f"⏸️ Чат между {user_id} и {partner_id} поставлен на паузу.")
        else:
            # Уже на паузе, возможно, партнер поставил. Обновляем кнопки.
            keyboard = [
                [InlineKeyboardButton("▶️ Продолжить", callback_data="chat_resume")],
                [InlineKeyboardButton("⏹️ Завершить чат", callback_data="chat_end")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("⏸️ Чат поставлен на паузу.", reply_markup=reply_markup)

    elif callback_data == "chat_resume":
        if current_status == 'paused':
            # Возобновляем чат для обоих пользователей
            active_chats[user_id]['status'] = 'active'
            if partner_id in active_chats:
                active_chats[partner_id]['status'] = 'active'

            # Обновляем клавиатуру на стандартную
            reply_markup = InlineKeyboardMarkup(get_chat_control_keyboard())

            await query.edit_message_text("▶️ Чат возобновлен.", reply_markup=reply_markup)

            # Уведомляем партнера
            try:
                await context.bot.send_message(
                    chat_id=partner_id,
                    text="▶️ Собеседник возобновил чат.",
                    reply_markup=InlineKeyboardMarkup(get_chat_control_keyboard())
                )
            except:
                pass
            print(f"▶️ Чат между {user_id} и {partner_id} возобновлен.")
        else:
            # Уже активен, возможно, партнер возобновил. Обновляем кнопки.
            reply_markup = InlineKeyboardMarkup(get_chat_control_keyboard())
            await query.edit_message_text("▶️ Чат активен.", reply_markup=reply_markup)

    elif callback_data == "chat_end":
        # Завершаем чат
        reason = "Собеседник завершил чат."
        await end_chat_for_users(user_id, partner_id, context, reason)
        await query.edit_message_text("👋 Чат завершен.", reply_markup=None)


async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения внутри активного чата."""
    user = update.effective_user
    user_id = str(user.id)
    text = update.message.text

    # Проверяем, находится ли пользователь в активном чате
    if user_id not in active_chats:
        # Если пользователь не в чате, возможно, это часть другого процесса
        return

    chat_info = active_chats[user_id]
    partner_id = chat_info['partner_id']
    status = chat_info['status']

    # Проверяем статус чата
    if status != 'active':
        await update.message.reply_text("⏸️ Чат находится на паузе. Возобновите чат, чтобы отправлять сообщения.")
        # Показываем кнопку возобновления
        keyboard = [
            [InlineKeyboardButton("▶️ Продолжить", callback_data="chat_resume")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Хотите возобновить чат?", reply_markup=reply_markup)
        return

    try:
        # Отправляем сообщение партнёру по чату
        await context.bot.send_message(
            chat_id=partner_id,
            text=f"👤 {user.first_name}: {text}"
        )
        print(f"💬 {user.first_name} -> (чат) -> {text}")
    except Exception as e:
        # Если не удалось отправить сообщение, завершаем чат для обоих пользователей
        await end_chat_for_users(user_id, partner_id, context, reason="Собеседник отключился или заблокировал бота.")
        await update.message.reply_text("❌ Собеседник отключился. Чат завершен.")
        print(f"❌ Ошибка отправки сообщения от {user.first_name} к {partner_id}: {e}")


async def end_chat_for_users(user1_id: str, user2_id: str, context: ContextTypes.DEFAULT_TYPE,
                             reason: str = "Чат завершен.") -> None:
    """
    Завершает чат между двумя пользователями и уведомляет их.
    """
    # Удаляем из активных чатов
    active_chats.pop(user1_id, None)
    active_chats.pop(user2_id, None)

    # Уведомляем первого пользователя
    try:
        await context.bot.send_message(chat_id=user1_id, text=f"🔚 {reason}")
    except:
        pass  # Игнорируем ошибки, если пользователь заблокировал бота

    # Уведомляем второго пользователя
    try:
        await context.bot.send_message(chat_id=user2_id, text=f"🔚 {reason}")
    except:
        pass  # Игнорируем ошибки, если пользователь заблокировал бота

    print(f"🔚 Чат между {user1_id} и {user2_id} завершен. Причина: {reason}")


async def end_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /endchat для завершения текущего чата.
    """
    user = update.effective_user
    user_id = str(user.id)

    if user_id not in active_chats:
        await update.message.reply_text("❌ Вы не находитесь в активном чате.")
        return

    chat_info = active_chats[user_id]
    partner_id = chat_info['partner_id']
    await end_chat_for_users(user_id, partner_id, context, reason="Вы завершили чат.")
    await update.message.reply_text("👋 Чат завершен.")


# Эта функция может быть вызвана из commands.py для открытия меню чата по ДСЕ
async def show_chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает меню или запускает процесс чата по ДСЕ.
    В данном случае сразу запускаем процесс.
    """
    await initiate_dse_chat_search(update, context)
