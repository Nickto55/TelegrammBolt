#!/bin/bash
# Скрипт для диагностики и исправления проблем на сервере

echo "=== ДИАГНОСТИКА СЕРВЕРА ==="
echo ""

# 1. Проверка логов Flask
echo "1. Последние ошибки в логах Flask:"
if [ -f "web.log" ]; then
    tail -n 50 web.log | grep -i "error\|exception\|traceback" || echo "Нет ошибок в web.log"
else
    echo "Файл web.log не найден"
fi
echo ""

# 2. Проверка процесса
echo "2. Проверка запущенных процессов:"
ps aux | grep -i "web_app\|gunicorn\|flask" | grep -v grep
echo ""

# 3. Проверка портов
echo "3. Проверка занятых портов:"
netstat -tlnp 2>/dev/null | grep -E ":5000|:8000|:80" || ss -tlnp | grep -E ":5000|:8000|:80"
echo ""

# 4. Проверка bot_data.json
echo "4. Проверка структуры bot_data.json:"
python3 << 'PYEOF'
import json
try:
    with open('bot_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total = sum(len(records) for records in data.values())
    users = len(data.keys())
    
    print(f"  Всего пользователей: {users}")
    print(f"  Всего заявок: {total}")
    
    # Проверка на проблемные записи
    problems = []
    for user_id, records in data.items():
        for i, record in enumerate(records):
            if not record.get('dse'):
                problems.append(f"User {user_id}, record {i+1}: missing 'dse'")
            if not record.get('problem_type'):
                problems.append(f"User {user_id}, record {i+1}: missing 'problem_type'")
            if not record.get('datetime'):
                problems.append(f"User {user_id}, record {i+1}: missing 'datetime'")
    
    if problems:
        print(f"  ⚠ Найдено {len(problems)} проблемных записей:")
        for p in problems[:10]:
            print(f"    - {p}")
    else:
        print("  ✓ Все записи корректны")
        
except FileNotFoundError:
    print("  ✗ bot_data.json не найден!")
except json.JSONDecodeError as e:
    print(f"  ✗ Ошибка JSON: {e}")
except Exception as e:
    print(f"  ✗ Ошибка: {e}")
PYEOF
echo ""

# 5. Рестарт сервиса
echo "5. Перезапуск веб-сервиса..."
if [ -f "/etc/systemd/system/boltweb.service" ]; then
    sudo systemctl restart boltweb
    sleep 2
    sudo systemctl status boltweb --no-pager -l
elif [ -f "start_bot.sh" ]; then
    echo "  Используйте: ./start_bot.sh для запуска"
else
    echo "  Сервис не найден. Запустите вручную: python3 web_app.py"
fi
echo ""

echo "=== ГОТОВО ==="
echo "Для просмотра логов в реальном времени:"
echo "  tail -f web.log"
