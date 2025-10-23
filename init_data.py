#!/usr/bin/env python3
"""
Инициализация файлов данных для TelegrammBolt
"""

import json
import os
from pathlib import Path

# Получаем корневую директорию
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

# Создаём директории
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
(DATA_DIR / "photos").mkdir(exist_ok=True)

# Инициализируем файлы данных если не существуют
files_to_init = {
    DATA_DIR / "bot_data.json": {},
    DATA_DIR / "users_data.json": {},
    DATA_DIR / "chat_data.json": {},
    DATA_DIR / "watched_dse.json": []
}

for filepath, default_content in files_to_init.items():
    if not filepath.exists():
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_content, f, ensure_ascii=False, indent=2)
        print(f"✅ Создан: {filepath}")
    else:
        print(f"ℹ️  Существует: {filepath}")

# Создаём .gitkeep для photos
gitkeep = DATA_DIR / "photos" / ".gitkeep"
if not gitkeep.exists():
    gitkeep.touch()
    print(f"✅ Создан: {gitkeep}")

print("\n✅ Инициализация завершена!")
