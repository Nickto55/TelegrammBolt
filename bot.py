# bot.py
import asyncio
import logging
from typing import Optional

from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from commands import start, button_handler, handle_message, cancel_photo_command
from dse_watcher import load_watched_dse_data, start_watcher_job

logger = logging.getLogger(__name__)


async def chat_command(update, context):
    """Команда /chat"""
    from chat_manager import show_chat_menu

    if await _check_permission(update, 'chat_dse'):
        await show_chat_menu(update, context)


async def end_chat_command(update, context):
    """Команда /endchat"""
    from chat_manager import end_chat_command

    if await _check_permission(update, 'chat_dse'):
        await end_chat_command(update, context)


async def _check_permission(update, permission: str) -> bool:
    """Проверяет права пользователя и отправляет сообщение об ошибке при необходимости"""
    from user_manager import has_permission
    
    user_id = str(update.effective_user.id)
    if has_permission(user_id, permission):
        return True
    
    await update.message.reply_text("❌ У вас нет прав для использования этой команды.")
    return False


async def post_init(application: Application) -> None:
    """Функция, вызываемая после инициализации приложения."""
    logger.info("🚀 Бот инициализирован. Запуск дополнительных сервисов...")

    try:
        # Загружаем данные отслеживаемых ДСЕ
        load_watched_dse_data()
        logger.info("📊 Данные отслеживаемых ДСЕ загружены")

        # Запускаем задачу отслеживания в текущем цикле событий
        loop = asyncio.get_running_loop()
        loop.create_task(start_watcher_job(application))
        logger.info("⏱️  Задача DSE Watcher запланирована")

        logger.info("✅ Дополнительные сервисы инициализированы")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации дополнительных сервисов: {e}")
        raise


def _register_handlers(app: Application) -> None:
    """Регистрирует все обработчики команд и сообщений"""
    handlers = [
        CommandHandler("start", start),
        CommandHandler("chat", chat_command),
        CommandHandler("endchat", end_chat_command),
        CommandHandler("cancel_photo", cancel_photo_command),
        CallbackQueryHandler(button_handler),
        MessageHandler(filters.TEXT | filters.PHOTO | filters.CAPTION, handle_message),
    ]
    
    for handler in handlers:
        app.add_handler(handler)
    
    logger.info(f"📋 Зарегистрировано {len(handlers)} обработчиков")


def main() -> None:
    """Основная функция запуска бота"""
    try:
        # Создаем приложение
        app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

        # Регистрируем обработчики
        _register_handlers(app)

        logger.info("🚀 Бот запущен! Нажмите Ctrl+C для остановки")
        logger.info("=" * 50)

        # Запускаем бота
        app.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    main()