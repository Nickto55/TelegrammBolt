#!/usr/bin/env python3
import asyncio
import logging
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.commands import start, button_handler, cancel_photo_command, createwebuser_command, scan_command, invite_command, link_command, qr_photo_handler
from bot.commands_handlers import handle_message
from bot.dse_watcher import load_watched_dse_data, start_watcher_job
from config.config import BOT_TOKEN
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters


logger = logging.getLogger(__name__)


async def chat_command(update, context):
    """Команда /chat"""
    from bot.chat_manager import show_chat_menu
    from bot.user_manager import has_permission
    user_id = str(update.effective_user.id)

    if has_permission(user_id, 'chat_dse'):
        await show_chat_menu(update, context)
    else:
        await update.message.reply_text("❌ У вас нет прав для использования чата.")


async def end_chat_command(update, context):
    """Команда /endchat"""
    from bot.chat_manager import end_chat_command as end_chat_func
    from bot.user_manager import has_permission
    user_id = str(update.effective_user.id)

    if has_permission(user_id, 'chat_dse'):
        await end_chat_func(update, context)
    else:
        await update.message.reply_text("У вас нет прав для завершения чата.")


async def post_init(application) -> None:
    """Функция, вызываемая после инициализации приложения."""
    print("Бот инициализирован. Запуск дополнительных сервисов...")

    load_watched_dse_data()

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(start_watcher_job(application))
        logger.info("⏱️  Задача DSE Watcher запланирована")

        logger.info("Дополнительные сервисы инициализированы")
    except Exception as e:
        logger.error(f"Ошибка инициализации дополнительных сервисов: {e}")
        raise


def _register_handlers(app: Application) -> None:
    """Регистрирует все обработчики команд и сообщений"""
    handlers = [
        CommandHandler("start", start),
        CommandHandler("chat", chat_command),
        CommandHandler("endchat", end_chat_command),
        CommandHandler("cancel_photo", cancel_photo_command),
        CommandHandler("createwebuser", createwebuser_command),
        CommandHandler("scan", scan_command),
        CommandHandler("invite", invite_command),
        CommandHandler("link", link_command),
        CallbackQueryHandler(button_handler),
        MessageHandler(filters.PHOTO, qr_photo_handler),  # Отдельный обработчик для фото
        MessageHandler(filters.TEXT | filters.CAPTION, handle_message),
    ]
    
    for handler in handlers:
        app.add_handler(handler)
    
    logger.info(f"📋 Зарегистрировано {len(handlers)} обработчиков")


def main() -> None:
    """Основная функция запуска бота"""


    # --- Запуск Telegram бота ---
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    _register_handlers(app)

    # --- Запуск web-интерфейса, если включён ---
    import threading
    import json
    try:
        with open("ven_bot.json", "r", encoding="utf-8") as f:
            ven_cfg = json.load(f)
        web_enabled = ven_cfg.get("web_enabled", True)
        web_port = ven_cfg.get("web_port", 5000)
    except Exception:
        web_enabled = True
        web_port = 5000

    if web_enabled:
        def run_web():
            from web.web_app import app as flask_app
            flask_app.run(host="0.0.0.0", port=web_port, debug=False, use_reloader=False)
        threading.Thread(target=run_web, daemon=True).start()
        print(f"🌐 Веб-интерфейс запущен на порту {web_port}")

    print("Бот запущен! Нажмите Ctrl+C для остановки")
    print("=" * 50)
    app.run_polling()


if __name__ == "__main__":
    main()