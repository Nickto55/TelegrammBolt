#!/usr/bin/env python3
"""
Тест монитора - создаёт тестовые данные для проверки monitor.py
"""

import json
from datetime import datetime

# Создаём тестовый файл статистики
stats = {
    "status": "running",
    "uptime": 3600,
    "users_total": 25,
    "users_active": 5,
    "dse_total": 150,
    "requests_total": 1234,
    "requests_per_minute": 12.5,
    "memory_mb": 125.6,
    "last_update": datetime.now().isoformat()
}

with open("monitor_stats.json", "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

# Создаём тестовый файл команд
commands = {
    "commands": [
        {"command": "reload_stats", "timestamp": "2025-10-17 15:30:00", "status": "completed"},
        {"command": "clear_cache", "timestamp": "2025-10-17 15:31:00", "status": "pending"}
    ]
}

with open("monitor_commands.json", "w", encoding="utf-8") as f:
    json.dump(commands, f, ensure_ascii=False, indent=2)

# Создаём тестовый лог-файл
with open("bot_monitor.log", "w", encoding="utf-8") as f:
    f.write("[2025-10-17 15:00:00] [INFO] 🚀 Бот запущен\n")
    f.write("[2025-10-17 15:01:00] [SUCCESS] ✅ Все сервисы инициализированы\n")
    f.write("[2025-10-17 15:02:00] [INFO] 📥 Новая заявка от пользователя 123456\n")
    f.write("[2025-10-17 15:03:00] [WARN] ⚠️ Высокая нагрузка на сервер\n")
    f.write("[2025-10-17 15:04:00] [ERROR] ❌ Ошибка подключения к базе данных\n")
    f.write("[2025-10-17 15:05:00] [SUCCESS] ✅ База данных восстановлена\n")

print("✅ Тестовые файлы созданы:")
print("  - monitor_stats.json")
print("  - monitor_commands.json")
print("  - bot_monitor.log")
print("\nТеперь можно запустить: python3 monitor.py")
