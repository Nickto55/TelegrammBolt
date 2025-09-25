# bot.py
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from commands import start, button_handler, handle_message,cancel_photo_command

# Импортируем функции из dse_watcher
from dse_watcher import load_watched_dse_data, start_watcher_job


async def chat_command(update, context):
    """Команда /chat"""
    from chat_manager import show_chat_menu
    from user_manager import has_permission
    user_id = str(update.effective_user.id)

    if has_permission(user_id, 'chat_dse'):
        await show_chat_menu(update, context)
    else:
        await update.message.reply_text("❌ У вас нет прав для использования чата.")


async def end_chat_command(update, context):
    """Команда /endchat"""
    from chat_manager import end_chat_command
    from user_manager import has_permission
    user_id = str(update.effective_user.id)

    if has_permission(user_id, 'chat_dse'):
        await end_chat_command(update, context)
    else:
        await update.message.reply_text("❌ У вас нет прав для завершения чата.")


async def post_init(application) -> None:
    """Функция, вызываемая после инициализации приложения."""
    print("🚀 Бот инициализирован. Запуск дополнительных сервисов...")

    # 1. Загружаем данные отслеживаемых ДСЕ
    load_watched_dse_data()

    # 2. Запускаем задачу отслеживания
    # Используем asyncio.create_task напрямую в цикле событий приложения
    # Это устраняет предупреждение PTBUserWarning о запуске до run_polling
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Если цикл не запущен (маловероятно на этом этапе, но на всякий случай)
        loop = asyncio.get_event_loop()

    # Планируем задачу watcher в цикле событий приложения
    loop.create_task(start_watcher_job(application))
    print("⏱️  Задача DSE Watcher запланирована (ожидает запуска цикла событий).")

    print("✅ Дополнительные сервисы инициализированы.")


def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chat", chat_command))
    app.add_handler(CommandHandler("endchat", end_chat_command))
    app.add_handler(CommandHandler("cancel_photo", cancel_photo_command)) # <<< НОВАЯ КОМАНДА
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.CAPTION, handle_message))
    # filters.PHOTO добавлен, чтобы handle_message получал фото

    print("🚀 Бот запущен! Нажмите Ctrl+C для остановки")
    print("=" * 50)

    # Запускаем бота
    app.run_polling()


if __name__ == "__main__":
    main()