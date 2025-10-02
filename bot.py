import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from commands import start, button_handler, handle_message,cancel_photo_command

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

    load_watched_dse_data()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()


    loop.create_task(start_watcher_job(application))
    print("⏱️  Задача DSE Watcher запланирована (ожидает запуска цикла событий).")

    print("✅ Дополнительные сервисы инициализированы.")

"""wsl.exe -d Ubuntu"""
def main():
    """Основная функция запуска бота"""
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chat", chat_command))
    app.add_handler(CommandHandler("endchat", end_chat_command))
    app.add_handler(CommandHandler("cancel_photo", cancel_photo_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.CAPTION, handle_message))

    print("🚀 Бот запущен! Нажмите Ctrl+C для остановки")
    print("=" * 50)


    app.run_polling()


if __name__ == "__main__":
    main()