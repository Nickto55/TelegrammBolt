#!/bin/bash
# Исправление импортов в web_app.py для совместимости с dse_manager.py

echo "🔧 Исправление импортов в web_app.py..."

cd /opt/telegrambot

# Создать резервную копию
cp web_app.py web_app.py.backup.$(date +%s)

# Исправить импорт из dse_manager (строка 21)
sed -i 's/from dse_manager import get_all_dse, get_dse_by_id, add_dse, update_dse, delete_dse/from dse_manager import get_all_dse_records, get_dse_records_by_user, search_dse_records/' web_app.py

# Также исправить импорт из user_manager (строка 20)
sed -i 's/from user_manager import has_permission, get_user_data, is_user_registered/from user_manager import (\n    has_permission, \n    get_users_data, \n    get_user_data,\n    get_user_role, \n    register_user,\n    is_user_registered\n)/' web_app.py

echo "✅ Импорты исправлены!"

# Проверить синтаксис Python
echo ""
echo "Проверка синтаксиса..."
python3 -m py_compile web_app.py

if [ $? -eq 0 ]; then
    echo "✅ Синтаксис корректен!"
    echo ""
    echo "Теперь можно запустить приложение:"
    echo "gunicorn -w 4 -b 0.0.0.0:5000 web_app:app"
else
    echo "❌ Ошибка в синтаксисе! Восстанавливаем резервную копию..."
    cp web_app.py.backup.* web_app.py
fi
