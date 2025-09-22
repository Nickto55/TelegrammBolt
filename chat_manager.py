import json
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import load_data, save_data, DATA_FILE, USERS_FILE

# Глобальные переменные для управления чатом
active_chats = {}  # {user1_id: user2_id, user2_id: user1_id}
waiting_users = []  # Список пользователей, ждущих собеседника


def get_users_data():
    """Получить данные пользователей"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def get_dse_records_by_dse(dse_value):
    """Получить записи по значению ДСЕ"""
    all_data = load_data(DATA_FILE)
    records = []

    for user_id, user_records in all_data.items():
        if isinstance(user_records, list):
            for record in user_records:
                if record.get('dse', '').strip().lower() == dse_value.strip().lower():
                    record_with_user = record.copy()
                    record_with_user['user_id'] = user_id
                    records.append(record_with_user)

    return records


async def start_dse_chat_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать поиск чата по ДСЕ"""
    user = update.effective_user
    user_id = str(user.id)

    # Проверяем права доступа
    from user_manager import has_permission
    if not has_permission(user_id, 'chat_dse'):
        await update.callback_query.edit_message_text("❌ У вас нет прав для чата по ДСЕ.")
        return

    # Запрашиваем ДСЕ
    await update.callback_query.edit_message_text("Введите номер ДСЕ:")


async def show_dse_options(update: Update, context: ContextTypes.DEFAULT_TYPE, dse_value: str) -> None:
    """Показать список пользователей с данным ДСЕ"""
    user = update.effective_user
    user_id = str(user.id)

    # Получаем записи по ДСЕ
    records = get_dse_records_by_dse(dse_value)

    if not records:
        await update.callback_query.edit_message_text(f"❌ Нет записей с ДСЕ: {dse_value}")
        return

    # Создаем кнопки для каждого пользователя
    keyboard = []
    users_data = get_users_data()

    for record in records:
        target_user_id = record.get('user_id')
        target_user = users_data.get(target_user_id, {})
        target_name = target_user.get('first_name', 'Неизвестно')

        button_text = f"{target_name} (ID: {target_user_id})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'start_chat_{target_user_id}')])

    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("⬅️ Отмена", callback_data='back_to_main')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"Выберите пользователя с ДСЕ: {dse_value}",
        reply_markup=reply_markup
    )


async def start_dse_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: str) -> None:
    """Начать чат с конкретным пользователем"""
    user = update.effective_user
    user_id = str(user.id)

    # Проверяем, не является ли пользователь самим собой
    if user_id == target_user_id:
        await update.callback_query.edit_message_text("❌ Вы не можете начать чат с собой.")
        return

    # Проверяем, есть ли активный чат
    if user_id in active_chats:
        await update.callback_query.edit_message_text("❌ У вас уже идет чат.")
        return

    # Проверяем, есть ли у целевого пользователя активный чат
    if target_user_id in active_chats:
        await update.callback_query.edit_message_text("❌ Пользователь уже в чате.")
        return

    # Соединяем пользователей
    active_chats[user_id] = target_user_id
    active_chats[target_user_id] = user_id

    # Уведомляем обоих пользователей
    try:
        # Уведомляем партнера
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"💬 Начался чат с {user.first_name}."
        )

        # Уведомляем текущего пользователя
        await update.callback_query.edit_message_text(
            text=f"💬 Чат установлен с {user.first_name}!"
        )

        print(f"💬 Начат чат между {user.first_name} и пользователем ID {target_user_id}")

    except Exception as e:
        # Если не удалось отправить сообщение, завершаем чат
        await end_chat_for_user(user_id, context)
        await update.callback_query.edit_message_text("❌ Не удалось установить соединение.")


async def handle_dse_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка сообщений в чате по ДСЕ"""
    user = update.effective_user
    user_id = str(user.id)
    text = update.message.text

    # Проверяем, находится ли пользователь в активном чате
    if user_id in active_chats:
        partner_id = active_chats[user_id]

        try:
            # Отправляем сообщение партнёру
            await context.bot.send_message(
                chat_id=partner_id,
                text=f"👤 {user.first_name}: {text}"
            )

            # Подтверждение отправки
            await update.message.reply_text(f"✅ Отправлено: {text}")
            print(f"💬 {user.first_name} -> {text}")
        except:
            # Если не удалось отправить, завершаем чат
            await end_chat_for_user(user_id, context)
            await update.message.reply_text("❌ Собеседник отключился. Чат завершен.")
    else:
        await update.message.reply_text("💬 Чтобы начать чат, используйте команду /chat")


async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить чат"""
    user = update.effective_user
    user_id = str(user.id)

    await end_chat_for_user(user_id, context)
    if update.message:
        await update.message.reply_text("👋 Чат завершен.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("👋 Чат завершен.")


async def end_chat_for_user(user_id: str, context: ContextTypes.DEFAULT_TYPE):
    """Завершить чат для конкретного пользователя"""
    if user_id in active_chats:
        partner_id = active_chats[user_id]

        # Уведомляем партнера
        try:
            await context.bot.send_message(
                chat_id=partner_id,
                text="👋 Собеседник завершил чат."
            )
        except:
            pass  # Игнорируем ошибки отправки

        # Удаляем из активных чатов
        if partner_id in active_chats:
            del active_chats[partner_id]
        del active_chats[user_id]

        print(f"🔚 Чат завершен для пользователя {user_id}")