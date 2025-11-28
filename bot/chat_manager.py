import json
import os
import sys
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import load_data, DATA_FILE, USERS_FILE

dse_chat_states = {}
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

    for user_id, user_records in all_bot_data.items():
        if isinstance(user_records, list):
            for record in user_records:

                if record.get('dse', '').strip().lower() == dse_value.strip().lower():
                    record_copy = record.copy()
                    record_copy['user_id'] = user_id
                    matching_records.append(record_copy)

    return matching_records


async def initiate_dse_chat_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс поиска чата по ДСЕ. Запрашивает у пользователя номер ДСЕ."""
    from .commands import user_states
    
    user = update.effective_user
    user_id = str(user.id)

    dse_chat_states[user_id] = {'state': 'waiting_for_dse_input', 'dse': None, 'target_user_id': None,
                                'target_candidates': {}}

    # ВАЖНО: Устанавливаем состояние также в user_states для обработки текстовых сообщений
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]['dse_chat_state'] = 'awaiting_manual_input'

    if update.callback_query:
        await update.callback_query.edit_message_text("🔍 Пожалуйста, введите номер ДСЕ для поиска:")
    elif update.message:
        await update.message.reply_text("🔍 Пожалуйста, введите номер ДСЕ для поиска:")

    print(f"💬 {user.first_name} начал поиск чата по ДСЕ.")


async def handle_dse_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ввод номера ДСЕ пользователем."""
    from .commands import user_states
    
    user = update.effective_user
    user_id = str(user.id)
    
    # Получаем значение DSE: из текстового сообщения или из user_states
    if update.message and update.message.text:
        dse_value = update.message.text.strip()
    elif user_id in user_states and 'dse_chat_dse_value' in user_states[user_id]:
        dse_value = user_states[user_id]['dse_chat_dse_value']
    else:
        # Если нет ни того, ни другого, запрашиваем ввод
        if update.callback_query:
            await update.callback_query.edit_message_text("🔍 Пожалуйста, введите номер ДСЕ для поиска:")
        elif update.message:
            await update.message.reply_text("🔍 Пожалуйста, введите номер ДСЕ для поиска:")
        return

    dse_chat_states[user_id] = {'state': 'waiting_for_dse_input', 'dse': None, 'target_user_id': None,
                                'target_candidates': {}}

    dse_chat_states[user_id]['dse'] = dse_value
    dse_chat_states[user_id]['state'] = 'processing'

    records = get_dse_records_by_dse_value(dse_value)

    if not records:
        del dse_chat_states[user_id]
        # Очищаем состояние в user_states
        if user_id in user_states:
            user_states[user_id].pop('dse_chat_state', None)
            user_states[user_id].pop('dse_chat_dse_value', None)
        # Отправляем сообщение в зависимости от типа update
        if update.callback_query:
            await update.callback_query.edit_message_text(f"❌ По запросу ДСЕ '{dse_value}' ничего не найдено.")
        elif update.message:
            await update.message.reply_text(f"❌ По запросу ДСЕ '{dse_value}' ничего не найдено.")
        print(f"💬 Для {user.first_name} ничего не найдено по ДСЕ '{dse_value}'.")
        return

    candidate_records = [r for r in records]
    users_data = get_users_data()
    grouped_records = defaultdict(list)
    for record in candidate_records:
        grouped_records[record['user_id']].append(record)

    target_candidates = {}
    for target_user_id, user_records in grouped_records.items():
        target_user_info = users_data.get(target_user_id, {})
        target_name = target_user_info.get('first_name', f"Пользователь {target_user_id}")
        target_candidates[target_user_id] = {
            'records': user_records,
            'name': target_name
        }

    dse_chat_states[user_id]['target_candidates'] = target_candidates
    
    # Очищаем состояние ожидания ввода в user_states
    if user_id in user_states:
        user_states[user_id].pop('dse_chat_state', None)
        user_states[user_id].pop('dse_chat_dse_value', None)

    if len(target_candidates) == 1:
        single_target_user_id = list(target_candidates.keys())[0]
        dse_chat_states[user_id]['target_user_id'] = single_target_user_id
        dse_chat_states[user_id]['state'] = 'waiting_for_initiator_confirmation'
        await request_initiator_confirmation(update, context, user_id, single_target_user_id)
    else:
        dse_chat_states[user_id]['state'] = 'waiting_for_target_selection'
        await show_target_selection_menu(update, context, user_id)


async def show_target_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     initiator_user_id: str) -> None:
    """Показывает меню выбора пользователя для чата."""
    user = update.effective_user if update.effective_user else context.bot
    user_id = str(user.id) if user else initiator_user_id

    target_candidates = dse_chat_states[initiator_user_id]['target_candidates']
    dse_value = dse_chat_states[initiator_user_id]['dse']

    keyboard = []
    for target_user_id, candidate_info in target_candidates.items():
        candidate_name = candidate_info['name']

        callback_data = f"dse_chat_select_target_{target_user_id}"
        button_text = f"{candidate_name} (ID: {target_user_id})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="dse_chat_cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение в зависимости от типа update
    message_text = f"✅ Найдено {len(target_candidates)} записей по ДСЕ '{dse_value}' от разных пользователей.\nПожалуйста, выберите пользователя для связи:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    
    print(f"💬 Найдено {len(target_candidates)} кандидатов по ДСЕ '{dse_value}'.")


async def handle_target_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор пользователя из списка кандидатов."""
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки

    selecting_user = query.from_user
    selecting_user_id = str(selecting_user.id)
    callback_data = query.data

    # Проверяем, находится ли пользователь в нужном состоянии
    if (selecting_user_id not in dse_chat_states or
            dse_chat_states[selecting_user_id]['state'] != 'waiting_for_target_selection'):
        await query.edit_message_text("❌ Ошибка состояния. Пожалуйста, начните процесс заново.")
        return

    if callback_data == "dse_chat_cancel":
        del dse_chat_states[selecting_user_id]
        await query.edit_message_text("↩️ Поиск чата по ДСЕ отменен.")
        print(f"💬 {selecting_user.first_name} отменил выбор пользователя.")
        return

    # Извлекаем ID выбранного пользователя
    try:
        _, _, _, _, target_user_id = callback_data.split('_')
    except (ValueError, IndexError):
        await query.edit_message_text("❌ Ошибка при обработке выбора. Пожалуйста, попробуйте снова.")
        return

    if target_user_id not in dse_chat_states[selecting_user_id]['target_candidates']:
        await query.edit_message_text("❌ Неверный выбор. Пожалуйста, попробуйте снова.")
        return

    # Сохраняем выбранного пользователя
    dse_chat_states[selecting_user_id]['target_user_id'] = target_user_id
    dse_chat_states[selecting_user_id]['state'] = 'waiting_for_initiator_confirmation'

    # Запрашиваем подтверждение у инициатора
    await request_initiator_confirmation(update, context, selecting_user_id, target_user_id)


async def request_initiator_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, initiator_user_id: str,
                                         target_user_id: str) -> None:
    """Запрашивает подтверждение начала чата у инициатора."""
    dse_value = dse_chat_states[initiator_user_id]['dse']
    target_candidates = dse_chat_states[initiator_user_id]['target_candidates']
    target_name = target_candidates[target_user_id]['name']

    # Создаем кнопки подтверждения для инициатора
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="dse_chat_confirm_initiator")],
        [InlineKeyboardButton("❌ Отмена", callback_data="dse_chat_cancel_initiator")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение инициатору
    try:
        await context.bot.send_message(
            chat_id=initiator_user_id,
            text=f"❓ Вы уверены, что хотите начать чат с {target_name} по ДСЕ '{dse_value}'?\nПожалуйста, подтвердите.",
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"❌ Ошибка отправки запроса подтверждения инициатору {initiator_user_id}: {e}")
        del dse_chat_states[initiator_user_id]


async def handle_initiator_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает подтверждение начала чата от инициатора."""
    query = update.callback_query
    # await query.answer() # Уже вызван в button_handler

    print(f"🔍 handle_initiator_confirmation: Called with data '{query.data}'")

    initiator_user = query.from_user
    initiator_user_id = str(initiator_user.id)
    callback_data = query.data

    # Проверяем, находится ли пользователь в нужном состоянии
    print(f"🔍 handle_initiator_confirmation: Checking state for {initiator_user_id}")
    if (initiator_user_id not in dse_chat_states or
            dse_chat_states[initiator_user_id]['state'] != 'waiting_for_initiator_confirmation'):
        print(f"❌ handle_initiator_confirmation: State mismatch for {initiator_user_id}")
        print(f"   Expected: 'waiting_for_initiator_confirmation'")
        print(f"   Actual state: {dse_chat_states.get(initiator_user_id, {}).get('state', 'NOT_FOUND')}")
        print(f"   Full state: {dse_chat_states.get(initiator_user_id, 'NOT_FOUND')}")

        # Проверим, может быть пользователь уже в чате?
        if initiator_user_id in active_chats:
            print(f"   User {initiator_user_id} is already in active_chats.")
            # Возможно, пользователь уже в чате, обработаем как команду чата
            # await handle_chat_control(update, context) # Осторожно, может вызвать рекурсию
            # Лучше просто сообщить об ошибке
            await query.edit_message_text("❌ Вы уже находитесь в активном чате.")
            return

        await query.edit_message_text("❌ Ошибка состояния. Пожалуйста, начните процесс заново.")
        return

    print(f"🔍 handle_initiator_confirmation: Processing {callback_data} for {initiator_user_id}")

    if callback_data == "dse_chat_cancel_initiator":
        print(f"↩️ handle_initiator_confirmation: User {initiator_user_id} cancelled chat initiation.")
        if initiator_user_id in dse_chat_states:
            del dse_chat_states[initiator_user_id]
        await query.edit_message_text("↩️ Начало чата отменено.")
        print(f"💬 {initiator_user.first_name} отменил начало чата.")
        return

    if callback_data == "dse_chat_confirm_initiator":
        print(f"✅ handle_initiator_confirmation: User {initiator_user_id} confirmed chat initiation.")

        # Добавим проверку наличия необходимых ключей
        user_state = dse_chat_states.get(initiator_user_id, {})
        target_user_id = user_state.get('target_user_id')
        dse_value = user_state.get('dse')

        if not target_user_id or not dse_value:
            print(f"❌ handle_initiator_confirmation: Missing target_user_id or dse_value for {initiator_user_id}")
            print(f"   target_user_id: {target_user_id}")
            print(f"   dse_value: {dse_value}")
            if initiator_user_id in dse_chat_states:
                del dse_chat_states[initiator_user_id]
            await query.edit_message_text("❌ Ошибка данных. Пожалуйста, начните процесс заново.")
            return

        print(f"🔍 handle_initiator_confirmation: Target user is {target_user_id}, DSE is '{dse_value}'")

        # Проверка, не находится ли уже один из пользователей в активном чате
        # Для простоты, разрешаем только один активный чат на пользователя
        if initiator_user_id in active_chats and active_chats[initiator_user_id].get('status') == 'active':
            print(f"❌ handle_initiator_confirmation: Initiator {initiator_user_id} already in active chat.")
            if initiator_user_id in dse_chat_states:
                del dse_chat_states[initiator_user_id]
            await query.edit_message_text("❌ Вы уже находитесь в активном чате.")
            return

        if target_user_id in active_chats and active_chats[target_user_id].get('status') == 'active':
            print(f"❌ handle_initiator_confirmation: Target {target_user_id} already in active chat.")
            if initiator_user_id in dse_chat_states:
                del dse_chat_states[initiator_user_id]
            await query.edit_message_text("❌ Выбранный пользователь уже находится в чате.")
            return

        # Запрашиваем подтверждение у ответчика
        # Меняем состояние ИНИЦИАТОРА на ожидание ответа от ответчика
        dse_chat_states[initiator_user_id]['state'] = 'waiting_for_responder_confirmation'
        print(
            f"🔍 handle_initiator_confirmation: State changed to 'waiting_for_responder_confirmation' for {initiator_user_id}")

        await request_responder_confirmation(context, initiator_user_id, target_user_id, dse_value)
        # Сообщение инициатору обновляется внутри request_responder_confirmation или позже
        await query.edit_message_text(f"⏳ Ожидаем подтверждения от {target_user_id}...")


async def request_responder_confirmation(context: ContextTypes.DEFAULT_TYPE, initiator_user_id: str,
                                         target_user_id: str, dse_value: str) -> None:
    """Запрашивает подтверждение начала чата у ответчика."""
    print(
        f"🔍 request_responder_confirmation: Called for initiator {initiator_user_id}, target {target_user_id}, DSE '{dse_value}'")

    initiator_user_info = get_users_data().get(initiator_user_id, {})
    initiator_name = initiator_user_info.get('first_name', f"Пользователь {initiator_user_id}")

    print(f"🔍 request_responder_confirmation: Initiator name is '{initiator_name}'")

    # Создаем кнопки подтверждения для ответчика
    # ВАЖНО: callback_data должен содержать initiator_user_id, чтобы ответчик мог его идентифицировать
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"dse_chat_confirm_responder_{initiator_user_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"dse_chat_cancel_responder_{initiator_user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    print(f"🔍 request_responder_confirmation: Sending confirmation request to {target_user_id}")

    # Отправляем сообщение ответчику
    try:
        sent_message = await context.bot.send_message(
            chat_id=target_user_id,
            text=f"💬 С вами хочет связаться пользователь {initiator_name} по ДСЕ '{dse_value}'.\nПожалуйста, подтвердите начало чата.",
            reply_markup=reply_markup
        )
        print(
            f"🔔 request_responder_confirmation: Confirmation request sent to {target_user_id} (message_id: {sent_message.message_id}).")

        # Также обновляем сообщение инициатора
        # Найдем последнее сообщение инициатора или отправим новое
        # Проще всего просто отправить новое сообщение инициатору
        try:
            await context.bot.send_message(
                chat_id=initiator_user_id,
                text=f"⏳ Запрос на подтверждение чата отправлен пользователю {target_user_id}. Ожидаем ответ..."
            )
            print(f"🔔 request_responder_confirmation: Notification sent to initiator {initiator_user_id}.")
        except Exception as e:
            print(f"⚠️ request_responder_confirmation: Could not notify initiator {initiator_user_id}: {e}")

    except Exception as e:
        # Если не удалось уведомить ответчика, отменяем чат
        print(f"❌ request_responder_confirmation: Failed to notify responder {target_user_id}: {e}")
        if initiator_user_id in dse_chat_states:
            del dse_chat_states[initiator_user_id]
        try:
            await context.bot.send_message(
                chat_id=initiator_user_id,
                text="❌ Не удалось связаться с пользователем. Возможно, он заблокировал бота."
            )
        except Exception as e2:
            print(f"❌ request_responder_confirmation: Also failed to notify initiator {initiator_user_id}: {e2}")
        print(f"❌ Ошибка уведомления ответчика {target_user_id}: {e}")



async def handle_responder_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает подтверждение начала чата от ответчика."""
    query = update.callback_query
    await query.answer()

    responder_user = query.from_user
    responder_user_id = str(responder_user.id)
    callback_data = query.data
    print("kjodsjdjsiljksdjhkfjkjkdsjkasdjjhashjdsfj")

    # Извлекаем ID инициатора из callback_data
    try:
        _, _, _, _, initiator_user_id = callback_data.split('_')
    except (ValueError, IndexError):
        await query.edit_message_text("❌ Ошибка при обработке подтверждения.")
        return

    # Проверяем, находится ли инициатор в нужном состоянии
    if (initiator_user_id not in dse_chat_states or
            dse_chat_states[initiator_user_id]['state'] != 'waiting_for_responder_confirmation' or
            dse_chat_states[initiator_user_id]['target_user_id'] != responder_user_id):
        await query.edit_message_text("❌ Ошибка состояния.")
        return

    if callback_data.endswith("cancel_responder_" + initiator_user_id):
        del dse_chat_states[initiator_user_id]
        await query.edit_message_text("↩️ Начало чата отклонено.")
        # Уведомляем инициатора
        try:
            await context.bot.send_message(
                chat_id=initiator_user_id,
                text="❌ Пользователь отклонил запрос на начало чата."
            )
        except:
            pass
        print(f"💬 {responder_user.first_name} отклонил чат с {initiator_user_id}.")
        return

    if callback_data.endswith("confirm_responder_" + initiator_user_id):
        target_user_id = responder_user_id
        initiator_user_id = dse_chat_states[initiator_user_id][
            'target_user_id']  # Это должно быть равно responder_user_id

        dse_chat_states[initiator_user_id] = {'state': 'waiting_for_dse_input', 'dse': None, 'target_user_id': None,
                                    'target_candidates': {}}

        dse_value = dse_chat_states[initiator_user_id]['dse']

        # Устанавливаем активный чат со статусом 'active'
        active_chats[initiator_user_id] = {'partner_id': target_user_id, 'status': 'active'}
        active_chats[target_user_id] = {'partner_id': initiator_user_id, 'status': 'active'}

        # Очищаем временное состояние поиска
        del dse_chat_states[initiator_user_id]

        # Уведомляем ответчика, что чат установлен
        responder_keyboard = get_chat_control_keyboard()
        responder_reply_markup = InlineKeyboardMarkup(responder_keyboard)

        await query.edit_message_text(
            f"✅ Чат с пользователем по ДСЕ '{dse_value}' установлен!\nМожете начинать писать сообщения.",
            reply_markup=responder_reply_markup
        )

        # Уведомляем инициатора, что чат установлен
        initiator_keyboard = get_chat_control_keyboard()
        initiator_reply_markup = InlineKeyboardMarkup(initiator_keyboard)

        try:
            await context.bot.send_message(
                chat_id=initiator_user_id,
                text=f"✅ Чат с пользователем по ДСЕ '{dse_value}' установлен!\nМожете начинать писать сообщения.",
                reply_markup=initiator_reply_markup
            )
        except Exception as e:
            print(f"❌ Ошибка уведомления инициатора {initiator_user_id}: {e}")

        print(f"💬 Чат установлен между {initiator_user_id} и {target_user_id} по ДСЕ '{dse_value}'.")


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
