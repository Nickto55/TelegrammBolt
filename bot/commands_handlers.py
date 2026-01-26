import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime as dt

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.commands import show_main_menu, user_states, registration_states, show_application_menu, show_problem_types, show_rc_types, \
    show_dse_list_menu, show_all_dse_records, start_interactive_dse_search, select_dse_from_search, start_dse_search, \
    show_dse_statistics, show_admin_menu, show_users_list, start_change_role_process, admin_states, start_data_export, \
    send_file_to_chat, request_email_address, test_smtp_connection, show_nicknames_menu, show_users_for_nickname, \
    show_nicknames_list, start_nickname_input, remove_nickname_confirm, show_watched_dse_menu, start_add_watched_dse, \
    start_remove_watched_dse, show_watched_dse_list, start_dse_chat_search_with_selection, dse_view_states, \
    show_search_results, handle_dse_search_input, show_role_selection_menu, send_file_by_email
from bot.dse_manager import get_unique_dse_values
from bot.user_manager import has_permission, get_user_role, set_user_role, ROLES, get_all_users, check_nickname_exists, \
    set_user_nickname
from config.config import PROBLEM_TYPES, RC_TYPES, save_data, load_data, DATA_FILE


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех нажатий на кнопки"""
    query = update.callback_query
    
    data = query.data
    user = query.from_user
    user_id = str(user.id)

    
    await query.answer()
    
    # === ГЛАВНОЕ МЕНЮ ===
    if data == 'back_to_main':
        await show_main_menu(update, user_id)
    
    elif data == 'open_application':
        user_states[user_id]['application'] = 'started'
        await show_application_menu(update, user_id)
    
    # === ЗАПОЛНЕНИЕ ЗАЯВКИ ===
    elif data == 'back_to_application':
        await show_application_menu(update, user_id)
    
    elif data == 'set_dse':
        user_states[user_id]['waiting_for'] = 'dse'
        await query.edit_message_text("Введите номер ДСЕ:")
    
    elif data == 'set_problem':
        await show_problem_types(update, user_id)
    
    elif data.startswith('problem_'):
        idx = int(data.split('_')[1])
        user_states[user_id]['problem_type'] = PROBLEM_TYPES[idx]
        await show_application_menu(update, user_id)
    
    elif data == 'set_rc':
        await show_rc_types(update, user_id)
    
    elif data.startswith('rc_'):
        idx = int(data.split('_')[1])
        user_states[user_id]['rc'] = RC_TYPES[idx]
        await show_application_menu(update, user_id)
    
    elif data == 'set_programmer':
        if user_id not in user_states:
            user_states[user_id] = {
                'application': '', 'dse': '', 'problem_type': '', 'description': '', 
                'rc': '', 'programmer_name': '', 'machine_number': '', 'photo_file_id': None
            }
        user_states[user_id]['waiting_for'] = 'programmer_name'
        await query.edit_message_text("Введите ФИО программиста:")
    
    elif data == 'set_machine':
        print(f"DEBUG: Кнопка set_machine нажата пользователем {user_id}")
        if user_id not in user_states:
            user_states[user_id] = {
                'application': '', 'dse': '', 'problem_type': '', 'description': '', 
                'rc': '', 'programmer_name': '', 'machine_number': '', 'photo_file_id': None
            }
        user_states[user_id]['waiting_for'] = 'machine_number'
        await query.edit_message_text("Введите номер станка:")
    
    elif data == 'set_description':
        user_states[user_id]['waiting_for'] = 'description'
        await query.edit_message_text("Введите описание проблемы:")
    
    elif data == 'set_photo':
        user_states[user_id]['waiting_for'] = 'photo'
        await query.edit_message_text(
            "📸 Отправьте фото или используйте /cancel_photo для пропуска.\n\n"
            "Вы можете отправить одно фото."
        )
    
    elif data == 'send':
        # Отправка заявки
        user_data = user_states[user_id]
        
        # Получаем ФИО наладчика из данных пользователя 
        from bot.user_manager import get_user_data
        creator_data = get_user_data(user_id)
        creator_fio = ''
        if creator_data:
            first_name = creator_data.get('first_name', '')
            last_name = creator_data.get('last_name', '')
            creator_fio = f"{first_name} {last_name}".strip()
        
        # Скачиваем фото локально для веб-доступа
        photo_path = None
        photo_file_id = user_data.get('photo_file_id')
        if photo_file_id:
            try:
                import uuid
                from config.config import PHOTOS_DIR
                # Скачиваем файл
                file = await context.bot.get_file(photo_file_id)
                
                # Создаём имя файла
                dse_safe = user_data['dse'].replace('/', '_').replace('\\', '_')
                photo_filename = f"{user_id}_{dse_safe}_{uuid.uuid4().hex[:8]}.jpg"
                photo_path = os.path.join(PHOTOS_DIR, photo_filename)
                
                # Скачиваем
                await file.download_to_drive(photo_path)
                print(f"✅ Photo downloaded to {photo_path}")
            except Exception as e:
                print(f"❌ Failed to download photo: {e}")
                photo_path = None
        
        record = {
            'dse': user_data['dse'],
            'problem_type': user_data['problem_type'],
            'rc': user_data['rc'],
            'programmer_name': user_data.get('programmer_name', ''),
            'machine_number': user_data.get('machine_number', ''),
            'installer_fio': creator_fio,
            'description': user_data['description'],
            'datetime': dt.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'photo_file_id': photo_file_id,
            'photo_path': photo_path
        }
        
        data_list = load_data(DATA_FILE)
        if not isinstance(data_list, list):
            data_list = []
        data_list.append(record)
        save_data(data_list, DATA_FILE)
        
        # Очищаем данные пользователя
        user_states[user_id] = {
            'application': '',
            'dse': '',
            'problem_type': '',
            'description': '',
            'rc': '',
            'programmer_name': '',
            'machine_number': '',
            'photo_file_id': None
        }
        
        await query.edit_message_text(
            "Заявка успешно отправлена!\n\n"
            f"ДСЕ: {record['dse']}\n"
            f"Тип проблемы: {record['problem_type']}\n"
            f"РЦ: {record['rc']}\n"
            f"ФИО программиста: {record['programmer_name']}\n"
            f"Номер станка: {record['machine_number']}\n"
            f"ФИО наладчика: {record['installer_fio']}\n"
            f"Описание: {record['description']}\n"
            f"Дата: {record['datetime']}"
        )
        await show_main_menu(update, user_id)
    
    elif data == 'edit_application':
        await show_application_menu(update, user_id)
    
    # === ПРОСМОТР ДСЕ ===
    elif data == 'view_dse_list':
        if has_permission(user_id, 'view_dse_list'):
            await show_dse_list_menu(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав для просмотра списка ДСЕ.")
    
    elif data == 'view_all_dse':
        await show_all_dse_records(update, context, page=0)
    
    elif data.startswith('page_'):
        page = int(data.split('_')[1])
        await show_all_dse_records(update, context, page=page)
    
    elif data == 'interactive_dse_search':
        await start_interactive_dse_search(update, context)
    
    elif data.startswith('dse_search_select_'):
        idx = int(data.split('_')[-1])
        await select_dse_from_search(update, context, idx)
    
    elif data == 'search_dse':
        await start_dse_search(update, context, 'dse')
    
    elif data == 'search_type':
        await start_dse_search(update, context, 'type')
    
    elif data == 'dse_statistics':
        await show_dse_statistics(update, context)
    
    # === АДМИН МЕНЮ ===
    elif data == 'admin_users':
        if get_user_role(user_id) == 'admin':
            await show_admin_menu(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'admin_list_users':
        if get_user_role(user_id) == 'admin':
            await show_users_list(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'admin_change_role_start':
        if get_user_role(user_id) == 'admin':
            await start_change_role_process(update, context, user_id)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data.startswith('role_'):
        if get_user_role(user_id) == 'admin':
            role_name = data.split('_', 1)[1]
            if user_id in admin_states and 'changing_role_for' in admin_states[user_id]:
                target_user_id = admin_states[user_id]['changing_role_for']
                set_user_role(target_user_id, role_name)
                admin_states[user_id].pop('changing_role_for', None)
                admin_states[user_id].pop('changing_role', None)
                await query.edit_message_text(f"✅ Роль изменена на: {ROLES[role_name]}")
                await show_admin_menu(update, context)
    
    elif data == 'admin_export_data':
        if get_user_role(user_id) == 'admin':
            await start_data_export(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    # === ОБРАБОТЧИКИ ЭКСПОРТА === (НОВЫЕ)
    elif data == 'export_send_chat':
        if get_user_role(user_id) == 'admin':
            await send_file_to_chat(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'export_send_email_excel':
        if get_user_role(user_id) == 'admin':
            await request_email_address(update, context, format_type="excel")
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'export_send_email_text':
        if get_user_role(user_id) == 'admin':
            await request_email_address(update, context, format_type="text")
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'admin_test_smtp':
        if get_user_role(user_id) == 'admin':
            await test_smtp_connection(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'admin_manage_nicknames':
        if get_user_role(user_id) == 'admin':
            await show_nicknames_menu(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'nickname_set':
        if get_user_role(user_id) == 'admin':
            await show_users_for_nickname(update, context, 'set')
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'nickname_remove':
        if get_user_role(user_id) == 'admin':
            await show_users_for_nickname(update, context, 'remove')
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data == 'nickname_list':
        if get_user_role(user_id) == 'admin':
            await show_nicknames_list(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data.startswith('nickname_set_user_'):
        if get_user_role(user_id) == 'admin':
            target_user_id = data.split('_')[-1]
            await start_nickname_input(update, context, target_user_id)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    elif data.startswith('nickname_remove_user_'):
        if get_user_role(user_id) == 'admin':
            target_user_id = data.split('_')[-1]
            await remove_nickname_confirm(update, context, target_user_id)
        else:
            await query.edit_message_text("❌ У вас нет прав администратора.")
    
    # === ОТСЛЕЖИВАНИЕ ДСЕ ===
    elif data == 'watch_dse_menu':
        await show_watched_dse_menu(update, context)
    
    elif data == 'watch_add_dse':
        await start_add_watched_dse(update, context)
    
    elif data == 'watch_remove_dse':
        await start_remove_watched_dse(update, context)
    
    elif data.startswith('watch_rm_idx_'):
        idx = int(data.split('_')[-1])
        from .dse_watcher import get_watched_dse_list, remove_watched_dse
        watched_list = get_watched_dse_list(user_id)
        if 0 <= idx < len(watched_list):
            dse_to_remove = watched_list[idx]
            remove_watched_dse(user_id, dse_to_remove)
            await query.edit_message_text(f"✅ ДСЕ {dse_to_remove} удалён из отслеживания.")
            await show_watched_dse_menu(update, context)
    
    elif data == 'watch_list':
        await show_watched_dse_list(update, context)
    
    elif data.startswith('watch_select_dse_'):
        idx_str = data.split('_')[-1]
        if idx_str == 'manual':
            user_states[user_id] = user_states.get(user_id, {})
            user_states[user_id]['watch_dse_state'] = 'awaiting_manual_input'
            await query.edit_message_text("📝 Введите номер ДСЕ для отслеживания:")
        else:
            from .dse_watcher import add_watched_dse
            dse_list = get_unique_dse_values()
            idx = int(idx_str)
            if 0 <= idx < len(dse_list):
                dse_value = dse_list[idx]
                add_watched_dse(user_id, dse_value)
                await query.edit_message_text(f"✅ ДСЕ {dse_value} добавлен в отслеживание!")
                await show_watched_dse_menu(update, context)
    
    # === ЧАТ ПО ДСЕ ===
    elif data == 'chat_dse_menu':
        from .chat_manager import show_chat_menu
        await show_chat_menu(update, context)
    
    elif data == 'chat_start_search':
        await start_dse_chat_search_with_selection(update, context)
    
    elif data.startswith('chat_select_dse_'):
        idx_str = data.split('_')[-1]
        if idx_str == 'manual':
            user_states[user_id] = user_states.get(user_id, {})
            user_states[user_id]['dse_chat_state'] = 'awaiting_manual_input'
            await query.edit_message_text("📝 Введите номер ДСЕ для начала чата:")
        else:
            from .chat_manager import handle_dse_input
            dse_list = get_unique_dse_values()
            idx = int(idx_str)
            if 0 <= idx < len(dse_list):
                dse_value = dse_list[idx]
                # Имитируем текстовое сообщение
                user_states[user_id] = user_states.get(user_id, {})
                user_states[user_id]['dse_chat_state'] = 'selecting_or_manual'
                # Вызываем handle_dse_input с выбранным ДСЕ
                from .chat_manager import initiate_dse_chat_search
                user_states[user_id]['dse_chat_dse_value'] = dse_value
                await handle_dse_input(update, context)
    
    # === ОБРАБОТЧИКИ ЧАТА (из chat_manager) ===
    elif data.startswith('chat_confirm_target_') or data.startswith('chat_decline_target_'):
        from .chat_manager import handle_initiator_confirmation
        await handle_initiator_confirmation(update, context)
    
    elif data.startswith('chat_accept_') or data.startswith('chat_decline_'):
        from .chat_manager import handle_responder_confirmation
        await handle_responder_confirmation(update, context)
    
    elif data in ['chat_end', 'chat_back']:
        from .chat_manager import handle_chat_control
        await handle_chat_control(update, context)
    
    # === PDF ЭКСПОРТ ===
    elif data == 'pdf_export_menu':
        if has_permission(user_id, 'pdf_export'):
            from .pdf_generator import show_pdf_export_menu
            await show_pdf_export_menu(update, context)
        else:
            await query.edit_message_text("❌ У вас нет прав для экспорта PDF.")
    
    # === ПОМОЩЬ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ С РОЛЬЮ 'USER' ===
    elif data == 'qr_help':
        help_text = (
            "Как отправить QR код:\n\n"
            "1. Откройте камеру телефона\n"
            "2. Сфотографируйте QR код приглашения\n"
            "3. Отправьте фото прямо в этот чат\n"
            "4. Бот автоматически распознает и активирует код\n\n"
            "*Убедитесь что QR код четко виден на фото!"
        )
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("← Назад", callback_data='back_to_scan')]
        ]))
    
    elif data == 'commands_help':
        help_text = (
            "Доступные команды:\n\n"
            "/start - Главное меню\n"
            "/invite ВАШКОД - Активировать приглашение\n"
            "/link ВАШКОД - Привязать веб-аккаунт\n"
            "/help - Эта справка\n\n"
            "*Примеры:\n"
            "• /invite ABC123DEF456\n"
            "• /link XYZ789\n\n"
        )
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("← Назад", callback_data='back_to_scan')]
        ]))
    
    elif data == 'back_to_scan':
        from bot.commands import show_scan_menu
        await show_scan_menu(update, user_id)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений и фото"""
    user = update.effective_user
    user_id = str(user.id)
    
    # === ОБРАБОТКА РЕГИСТРАЦИИ ===
    if user_id in registration_states:
        if update.message.text:
            text = update.message.text.strip()
            reg_state = registration_states[user_id]
            
            if reg_state['step'] == 'ask_first_name':
                # Сохраняем имя
                registration_states[user_id]['first_name'] = text
                registration_states[user_id]['step'] = 'ask_last_name'
                await update.message.reply_text(
                    f"Спасибо, {text}!\n\n"
                    "Теперь укажите вашу фамилию:"
                )
                return
            
            elif reg_state['step'] == 'ask_last_name':
                # Сохраняем фамилию и завершаем регистрацию
                last_name = text
                first_name = reg_state['first_name']
                username = reg_state['username']
                invite_code = reg_state.get('invite_code')
                
                # Удаляем состояние регистрации
                del registration_states[user_id]
                
                # Если есть код приглашения, используем его (он сам зарегистрирует пользователя)
                if invite_code:
                    from bot.invite_manager import use_invite
                    result = use_invite(
                        invite_code, 
                        int(user_id), 
                        username, 
                        first_name,
                        last_name
                    )
                    
                    if result["success"]:
                        await update.message.reply_text(
                            f"🎉 {result['message']}\n\n"
                            f"✅ Регистрация завершена!\n"
                            f"Имя: {first_name} {last_name}\n\n"
                            f"Добро пожаловать в систему!"
                        )
                    else:
                        # Если приглашение не сработало, регистрируем с ролью по умолчанию
                        from bot.user_manager import register_user
                        register_user(user_id, username, first_name, last_name)
                        await update.message.reply_text(
                            f"⚠️ Ошибка при обработке приглашения: {result['error']}\n\n"
                            f"✅ Вы зарегистрированы с базовыми правами.\n"
                            f"Имя: {first_name} {last_name}"
                        )
                else:
                    # Нет приглашения - регистрируем с ролью по умолчанию
                    from bot.user_manager import register_user
                    register_user(user_id, username, first_name, last_name)
                    await update.message.reply_text(
                        f"✅ Регистрация завершена!\n"
                        f"Имя: {first_name} {last_name}\n\n"
                        f"Добро пожаловать в систему!"
                    )
                
                # Инициализируем состояние пользователя и показываем главное меню
                user_states[user_id] = {
                    'application': '',
                    'dse': '',
                    'problem_type': '',
                    'description': '',
                    'rc': '',
                    'photo_file_id': None
                }
                
                # Проверяем роль и показываем соответствующее меню
                from bot.user_manager import get_user_role
                user_role = get_user_role(user_id)
                if user_role == 'user':
                    from bot.commands import show_scan_menu
                    await show_scan_menu(update, user_id)
                else:
                    await show_main_menu(update, user_id)
                return
        else:
            await update.message.reply_text(
                "⚠️ Пожалуйста, отправьте текстовое сообщение."
            )
            return
    
    # Проверяем, ожидается ли ввод данных
    if user_id in user_states:
        user_data = user_states[user_id]
        
        # Обработка фото
        if update.message.photo:
            if user_data.get('waiting_for') == 'photo':
                # Сохраняем file_id самого большого фото
                photo_file_id = update.message.photo[-1].file_id
                user_states[user_id]['photo_file_id'] = photo_file_id
                user_states[user_id].pop('waiting_for', None)
                await update.message.reply_text("✅ Фото сохранено!")
                await show_application_menu(update, user_id)
                return
            # Обработка сообщений в чате
            elif 'dse_chat_state' in user_data:
                from .chat_manager import handle_chat_message
                await handle_chat_message(update, context)
                return
            else:
                # Если пользователь отправил фото, но не в режиме ожидания фото
                await update.message.reply_text(
                    "ℹ️ Чтобы прикрепить фото к заявке, сначала нажмите кнопку 'Фото' в меню заявки."
                )
                return
        
        # Обработка текстовых сообщений
        if update.message.text:
            text = update.message.text.strip()
            
            # === ЗАПОЛНЕНИЕ ЗАЯВКИ ===
            if user_data.get('waiting_for') == 'dse':
                user_states[user_id]['dse'] = text
                user_states[user_id].pop('waiting_for', None)
                await update.message.reply_text(f"✅ ДСЕ сохранён: {text}")
                await show_application_menu(update, user_id)
                return
            
            elif user_data.get('waiting_for') == 'dse_name':
                print(f"DEBUG: Сохранение наименования ДСЕ: {text}")
                user_states[user_id]['dse_name'] = text
                user_states[user_id].pop('waiting_for', None)
                await update.message.reply_text(f"✅ Наименование ДСЕ сохранено: {text}")
                await show_application_menu(update, user_id)
                return
            
            elif user_data.get('waiting_for') == 'programmer_name':
                print(f"DEBUG: Сохранение ФИО программиста: {text}")
                user_states[user_id]['programmer_name'] = text
                user_states[user_id].pop('waiting_for', None)
                await update.message.reply_text(f"✅ ФИО программиста сохранено: {text}")
                await show_application_menu(update, user_id)
                return
            
            elif user_data.get('waiting_for') == 'machine_number':
                print(f"DEBUG: Сохранение номера станка: {text}")
                user_states[user_id]['machine_number'] = text
                user_states[user_id].pop('waiting_for', None)
                await update.message.reply_text(f"✅ Номер станка сохранён: {text}")
                await show_application_menu(update, user_id)
                return
            
            elif user_data.get('waiting_for') == 'description':
                user_states[user_id]['description'] = text
                user_states[user_id].pop('waiting_for', None)
                await update.message.reply_text(f"✅ Описание сохранено")
                await show_application_menu(update, user_id)
                return
            
            # === ПОДПИСКА НА ЗАЯВКИ ===
            elif user_data.get('waiting_for') == 'subscription_email':
                import re
                email = text.strip()
                # Простая валидация email
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                
                if re.match(email_pattern, email):
                    from bot.subscription_manager import add_subscription
                    from bot.commands import show_subscription_menu
                    delivery_type = user_data.get('subscription_delivery', 'email')
                    
                    if add_subscription(user_id, delivery_type, email):
                        user_states[user_id].pop('waiting_for', None)
                        user_states[user_id].pop('subscription_delivery', None)
                        
                        delivery_text = {
                            'email': 'на Email',
                            'both': 'в Telegram и на Email'
                        }.get(delivery_type, 'на Email')
                        
                        await update.message.reply_text(
                            f"Подписка успешно создана!\n\n"
                            f"Email: {email}\n"
                            f"Доставка: {delivery_text}\n\n"
                            f"Теперь вы будете автоматически получать PDF отчёт всех новых заявок."
                        )
                        # Показываем меню подписок через callback-обёртку
                        from telegram import Update as TelegramUpdate
                        # Создаём фиктивный callback_query для show_subscription_menu
                        class FakeQuery:
                            def __init__(self, user_id):
                                self.from_user = type('obj', (object,), {'id': int(user_id)})
                            async def edit_message_text(self, *args, **kwargs):
                                await update.message.reply_text(*args, **kwargs)
                            async def answer(self, *args, **kwargs):
                                pass
                        
                        fake_update = type('obj', (object,), {'callback_query': FakeQuery(user_id)})()
                        await show_subscription_menu(fake_update, context)
                    else:
                        await update.message.reply_text("❌ Ошибка создания подписки. Попробуйте позже.")
                else:
                    await update.message.reply_text(
                        "❌ Некорректный email адрес.\n\n"
                        "Введите корректный email:"
                    )
                return
            
            # === ПОИСК ДСЕ ===
            elif user_id in dse_view_states:
                dse_state = dse_view_states[user_id]
                if dse_state.get('searching_dse'):
                    await show_search_results(update, context, text, 'dse')
                    dse_view_states[user_id].pop('searching_dse', None)
                    return
                elif dse_state.get('searching_type'):
                    await show_search_results(update, context, text, 'type')
                    dse_view_states[user_id].pop('searching_type', None)
                    return
                elif dse_state.get('interactive_search'):
                    await handle_dse_search_input(update, context)
                    return
            
            # === ОТСЛЕЖИВАНИЕ ДСЕ ===
            elif user_data.get('watch_dse_state') == 'awaiting_manual_input':
                from .dse_watcher import add_watched_dse
                dse_value = text.strip().upper()
                add_watched_dse(user_id, dse_value)
                user_states[user_id].pop('watch_dse_state', None)
                await update.message.reply_text(f"✅ ДСЕ {dse_value} добавлен в отслеживание!")
                await show_watched_dse_menu(update, context)
                return
            
            # === ЧАТ ПО ДСЕ ===
            elif user_data.get('dse_chat_state') == 'awaiting_manual_input':
                from .chat_manager import handle_dse_input
                user_states[user_id]['dse_chat_dse_value'] = text.strip().upper()
                user_states[user_id]['dse_chat_state'] = 'selecting_or_manual'
                await handle_dse_input(update, context)
                return
            
            # Проверяем, находится ли пользователь в активном чате
            from .chat_manager import active_chats, handle_chat_message
            if user_id in active_chats:
                await handle_chat_message(update, context)
                return
            
            # === АДМИН: ИЗМЕНЕНИЕ РОЛИ ===
            elif user_id in admin_states and admin_states[user_id].get('changing_role'):
                target_user_id = text.strip()
                users = get_all_users()
                if target_user_id in users:
                    admin_states[user_id]['changing_role_for'] = target_user_id
                    admin_states[user_id].pop('changing_role', None)
                    await show_role_selection_menu(update, context, target_user_id)
                else:
                    await update.message.reply_text(
                        f"❌ Пользователь с ID {target_user_id} не найден.\n\n"
                        "Введите корректный ID:"
                    )
                return
            
            # === АДМИН: УСТАНОВКА КЛИЧКИ ===
            elif user_id in admin_states and admin_states[user_id].get('setting_nickname'):
                nickname = text.strip()
                if len(nickname) > 20:
                    await update.message.reply_text("❌ Кличка слишком длинная (максимум 20 символов).\n\nВведите другую кличку:")
                    return
                
                if check_nickname_exists(nickname):
                    await update.message.reply_text(f"❌ Кличка '{nickname}' уже используется.\n\nВведите другую кличку:")
                    return
                
                target_user_id = admin_states[user_id].get('setting_nickname_for')
                if target_user_id:
                    set_user_nickname(target_user_id, nickname)
                    admin_states[user_id].pop('setting_nickname', None)
                    admin_states[user_id].pop('setting_nickname_for', None)
                    
                    users = get_all_users()
                    user_name = users.get(target_user_id, {}).get('first_name', 'Неизвестно')
                    await update.message.reply_text(f"✅ Кличка '{nickname}' установлена для {user_name}")
                    await show_nicknames_menu(update, context)
                return
            
            # === АДМИН: EMAIL АДРЕС ===
            elif user_id in admin_states and admin_states[user_id].get('waiting_for_email'):
                email = text.strip()
                # Простая проверка email
                if '@' in email and '.' in email:
                    admin_states[user_id].pop('waiting_for_email', None)
                    await send_file_by_email(update, context, email)
                else:
                    await update.message.reply_text(
                        "❌ Некорректный email адрес.\n\n"
                        "Введите корректный email:"
                    )
                return
            
            
            elif admin_states[user_id].get('creating_webuser'):
                step = admin_states[user_id].get('step')
                
                if step == 'username':
                    username = text.strip()
                    # Проверка на допустимые символы
                    if not username.replace('_', '').replace('-', '').isalnum():
                        await update.message.reply_text(
                            "❌ Логин должен содержать только латинские буквы, цифры, подчеркивание и дефис.\n\n"
                            "Введите корректный логин:"
                        )
                        return
                    
                    # Проверка на существование
                    from config.config import ADMIN_CREDENTIALS
                    if username in ADMIN_CREDENTIALS:
                        await update.message.reply_text(
                            f"❌ Пользователь '{username}' уже существует.\n\n"
                            "Введите другой логин:"
                        )
                        return
                    
                    admin_states[user_id]['username'] = username
                    admin_states[user_id]['step'] = 'password'
                    
                    await update.message.reply_text(
                        f"✅ Логин: <code>{username}</code>\n\n"
                        "Теперь введите пароль для этого пользователя:\n"
                        "(минимум 6 символов)",
                        parse_mode='HTML'
                    )
                    return
                
                elif step == 'password':
                    password = text.strip()
                    if len(password) < 6:
                        await update.message.reply_text(
                            "❌ Пароль слишком короткий (минимум 6 символов).\n\n"
                            "Введите корректный пароль:"
                        )
                        return
                    
                    username = admin_states[user_id].get('username')
                    telegram_user_id = admin_states[user_id].get('telegram_user_id')
                    telegram_name = admin_states[user_id].get('telegram_name')
                    
                    # Сохранение в config.py с привязкой к Telegram ID
                    from config.config import ADMIN_CREDENTIALS, generate_password_hash, save_admin_credentials
                    password_hash = generate_password_hash(password)
                    ADMIN_CREDENTIALS[username] = password_hash
                    
                    # Сохранение в файл с привязкой к Telegram ID
                    try:
                        save_admin_credentials(username, password_hash, telegram_user_id)
                        admin_states[user_id].clear()
                        
                        await update.message.reply_text(
                            f"✅ <b>Логин/пароль успешно привязаны к вашему аккаунту!</b>\n\n"
                            f"� Telegram: {telegram_name} (ID: <code>{telegram_user_id}</code>)\n"
                            f"�🔐 Логин: <code>{username}</code>\n"
                            f"🔑 Пароль: <code>{password}</code>\n\n"
                            f"🌐 URL: https://boltweb.servebeer.com/login\n\n"
                            f"ℹ️ Теперь вы можете входить на сайт как через Telegram, так и через логин/пароль.\n"
                            f"⚠️ <i>Сохраните эти данные, пароль больше не будет показан!</i>",
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        await update.message.reply_text(f"❌ Ошибка сохранения: {e}")
                        admin_states[user_id].clear()
                    return
    
    # Если ничего не обработано, просто игнорируем сообщение
    await update.message.reply_text(
        "Используйте /start для открытия главного меню. blb yf[eq]"
    )


async def cancel_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /cancel_photo - отменить загрузку фото"""
    user_id = str(update.effective_user.id)
    
    if user_id in user_states:
        user_data = user_states[user_id]
        if user_data.get('waiting_for') == 'photo':
            user_states[user_id].pop('waiting_for', None)
            user_states[user_id]['photo_file_id'] = None
            await update.message.reply_text("❌ Загрузка фото отменена.")
            await show_application_menu(update, user_id)
            return
    
    await update.message.reply_text("Нечего отменять.")
