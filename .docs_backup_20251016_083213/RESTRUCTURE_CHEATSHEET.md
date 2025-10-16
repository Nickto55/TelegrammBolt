# ⚡ Реструктуризация - Шпаргалка

## 🚀 БЫСТРЫЙ СТАРТ

```bash
bash restructure.sh && python update_imports.py
```

---

## 📋 ТРИ КОМАНДЫ

```bash
# 1. Backup
git add -A && git commit -m "Backup before restructure"

# 2. Restructure
bash restructure.sh && python update_imports.py

# 3. Test
python src/bot/main.py
```

---

## 🗺️ НОВАЯ СТРУКТУРА

```
├── src/          → Весь код
│   ├── bot/      → Telegram бот
│   └── web/      → Веб-интерфейс
├── config/       → Конфигурация
├── data/         → Данные
├── scripts/      → Скрипты
├── docs/         → Документация
└── tests/        → Тесты
```

---

## 📝 ИЗМЕНЕНИЯ

### Файлы:
```
bot.py              → src/bot/main.py
web_app.py          → src/web/app.py
user_manager.py     → src/bot/managers/user_manager.py
commands.py         → src/bot/handlers/commands.py
pdf_generator.py    → src/bot/utils/pdf_generator.py
ven_bot.json        → config/ven_bot.json
bot_data.json       → data/bot_data.json
setup.sh            → scripts/setup/setup.sh
README_Ubuntu.md    → docs/installation/README_Ubuntu.md
```

### Импорты:
```python
# Было:
from user_manager import UserManager

# Стало:
from src.bot.managers.user_manager import UserManager
```

### Команды:
```bash
# Было:
python bot.py

# Стало:
python src/bot/main.py
```

---

## 🔄 ОТКАТ

```bash
# Вариант 1: Git
git reset --hard HEAD && git clean -fd

# Вариант 2: Backup
cp -r ../TelegrammBolt_backup_*/* .

# Вариант 3: Branch
git checkout web
```

---

## ✅ ПРОВЕРКА

```bash
# Структура
tree -L 2

# Импорты
python -c "from src.bot.main import *"

# Запуск
python src/bot/main.py

# Тест
curl http://localhost:5000
```

---

## 📚 ДОКУМЕНТАЦИЯ

- **План**: [RESTRUCTURE_PLAN.md](RESTRUCTURE_PLAN.md)
- **Как**: [RESTRUCTURE_HOWTO.md](RESTRUCTURE_HOWTO.md)
- **Визуал**: [STRUCTURE_VISUAL.md](STRUCTURE_VISUAL.md)
- **Индекс**: [RESTRUCTURE_INDEX.md](RESTRUCTURE_INDEX.md)

---

## 🛠️ СКРИПТЫ

- **restructure.sh** - Автоматическая реорганизация
- **update_imports.py** - Обновление импортов

---

## 💡 СОВЕТЫ

1. Создайте ветку: `git checkout -b restructure-v2`
2. Сделайте backup: `git commit -m "Backup"`
3. Запустите скрипт: `bash restructure.sh`
4. Обновите импорты: `python update_imports.py`
5. Протестируйте: `python src/bot/main.py`

---

**Готово!** 🎉
