#!/bin/bash
# Полное исправление всех ошибок веб-интерфейса

set -e  # Остановиться при ошибке

echo "🚀 Полное исправление веб-интерфейса TelegrammBolt..."
echo ""

cd /opt/telegrambot

# ==========================================
# 1. Добавить недостающие функции в user_manager.py
# ==========================================
echo "📝 Шаг 1: Проверка user_manager.py..."

if ! grep -q "def is_user_registered" user_manager.py; then
    echo "   Добавление функций is_user_registered() и get_user_data()..."
    cat >> user_manager.py << 'EOF'


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
    echo "   ✅ Функции добавлены"
else
    echo "   ✅ Функции уже существуют"
fi

# ==========================================
# 2. Исправить импорты в web_app.py
# ==========================================
echo ""
echo "📝 Шаг 2: Исправление импортов в web_app.py..."

# Создать резервную копию
cp web_app.py web_app.py.backup.$(date +%s)
echo "   Резервная копия создана"

# Исправить неправильные импорты
if grep -q "from dse_manager import get_all_dse, get_dse_by_id" web_app.py; then
    echo "   Исправление импортов dse_manager..."
    sed -i 's/from dse_manager import get_all_dse, get_dse_by_id, add_dse, update_dse, delete_dse/from dse_manager import get_all_dse_records, get_dse_records_by_user, search_dse_records/' web_app.py
    echo "   ✅ Импорты dse_manager исправлены"
else
    echo "   ✅ Импорты dse_manager уже корректны"
fi

# ==========================================
# 3. Установить зависимости
# ==========================================
echo ""
echo "📦 Шаг 3: Проверка зависимостей..."

if [ ! -d ".venv" ]; then
    echo "   Создание виртуального окружения..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Проверить основные пакеты
echo "   Установка необходимых пакетов..."
pip install -q flask flask-cors gunicorn 2>/dev/null || true

# Проверить requirements.txt
if [ -f "requirements.txt" ]; then
    echo "   Установка из requirements.txt..."
    pip install -q -r requirements.txt 2>/dev/null || true
fi

echo "   ✅ Зависимости проверены"

# ==========================================
# 4. Проверить конфигурацию
# ==========================================
echo ""
echo "⚙️  Шаг 4: Проверка конфигурации..."

# Проверить config.py
if [ ! -f "config.py" ]; then
    echo "   ❌ config.py не найден!"
    exit 1
fi

# Проверить ven_bot.json
if [ ! -f "ven_bot.json" ]; then
    echo "   ⚠️  ven_bot.json не найден, создание шаблона..."
    cat > ven_bot.json << 'EOF'
{
  "BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
  "ADMIN_IDS": []
}
EOF
    echo "   📝 Заполните ven_bot.json!"
else
    echo "   ✅ ven_bot.json найден"
fi

# Создать пустые файлы данных если их нет
for file in bot_data.json users_data.json chat_data.json; do
    if [ ! -f "$file" ]; then
        echo '{}' > "$file"
        echo "   ✅ Создан $file"
    fi
done

# ==========================================
# 5. Проверить синтаксис Python
# ==========================================
echo ""
echo "🔍 Шаг 5: Проверка синтаксиса..."

python3 -m py_compile web_app.py
if [ $? -eq 0 ]; then
    echo "   ✅ web_app.py - синтаксис корректен"
else
    echo "   ❌ Ошибка в web_app.py!"
    exit 1
fi

python3 -m py_compile user_manager.py
if [ $? -eq 0 ]; then
    echo "   ✅ user_manager.py - синтаксис корректен"
else
    echo "   ❌ Ошибка в user_manager.py!"
    exit 1
fi

# ==========================================
# 6. Тест импортов
# ==========================================
echo ""
echo "🧪 Шаг 6: Тестирование импортов..."

python3 << 'PYEOF'
import sys
try:
    from user_manager import has_permission, get_users_data, get_user_data, is_user_registered
    print("   ✅ user_manager импорты работают")
except Exception as e:
    print(f"   ❌ Ошибка импорта user_manager: {e}")
    sys.exit(1)

try:
    from dse_manager import get_all_dse_records, get_dse_records_by_user, search_dse_records
    print("   ✅ dse_manager импорты работают")
except Exception as e:
    print(f"   ❌ Ошибка импорта dse_manager: {e}")
    sys.exit(1)

try:
    from config import BOT_TOKEN
    print("   ✅ config импорт работает")
except Exception as e:
    print(f"   ❌ Ошибка импорта config: {e}")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Ошибка при тестировании импортов!"
    exit 1
fi

# ==========================================
# Финал
# ==========================================
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Все исправления применены успешно!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🚀 Запуск веб-приложения:"
echo ""
echo "   cd /opt/telegrambot"
echo "   source .venv/bin/activate"
echo "   gunicorn -w 4 -b 0.0.0.0:5000 web_app:app"
echo ""
echo "Или в фоне:"
echo "   nohup gunicorn -w 4 -b 0.0.0.0:5000 web_app:app > web.log 2>&1 &"
echo ""
echo "Для проверки логов:"
echo "   tail -f web.log"
echo ""
echo "═══════════════════════════════════════════════════════"
