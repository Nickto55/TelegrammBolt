#!/bin/bash
# Быстрое исправление импортов для веб-интерфейса

echo "🔧 Исправление импортов в user_manager.py..."

# Проверка наличия функций
if ! grep -q "def is_user_registered" /opt/telegrambot/user_manager.py; then
    echo "Добавление недостающих функций..."
    
    cat >> /opt/telegrambot/user_manager.py << 'EOF'


# === ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ВЕБ-ИНТЕРФЕЙСА ===

def is_user_registered(user_id):
    """Проверить, зарегистрирован ли пользователь"""
    users_data = get_users_data()
    return str(user_id) in users_data


def get_user_data(user_id):
    """Получить данные конкретного пользователя"""
    users_data = get_users_data()
    return users_data.get(str(user_id), None)
EOF
    
    echo "✅ Функции добавлены!"
else
    echo "✅ Функции уже существуют"
fi

echo ""
echo "Теперь запустите веб-приложение:"
echo "cd /opt/telegrambot && python web_app.py"
