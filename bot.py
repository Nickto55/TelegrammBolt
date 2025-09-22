from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from commands import start, button_handler, handle_message


async def chat_command(update, context):
    """Команда /chat"""
    from chat_manager import show_chat_menu
    from user_manager import has_permission
    user_id = str(update.effective_user.id)



async def end_chat_command(update, context):
    """Команда /endchat"""
    from chat_manager import end_chat
    from user_manager import has_permission
    user_id = str(update.effective_user.id)

    if has_permission(user_id, 'chat_dse'):
        await end_chat(update, context)
    else:
        await update.message.reply_text("❌ У вас нет прав для завершения чата.")


def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chat", chat_command))
    app.add_handler(CommandHandler("endchat", end_chat_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Бот запущен! Нажмите Ctrl+C для остановки")
    print("=" * 50)

    # Запускаем бота
    app.run_polling()


if __name__ == "__main__":
    main()