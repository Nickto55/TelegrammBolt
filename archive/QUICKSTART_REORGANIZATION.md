# 🔄 БЫСТРЫЙ СТАРТ: Реорганизация проекта

## ⚡ Автоматическая реорганизация (РЕКОМЕНДУЕТСЯ)

### На Windows:
```powershell
# 1. Откройте PowerShell в корне проекта
cd C:\Users\truni\PycharmProjects\TelegrammBolt

# 2. Запустите скрипт реорганизации
.\reorganize.ps1
```

### На Linux/Mac:
```bash
# Скоро будет доступен bash-скрипт
```

---

## 📝 Что будет сделано:

✅ Создана структура: `src/`, `docs/`, `scripts/`, `config/`, `data/`  
✅ Python модули перемещены в `src/` (bot, managers, utils, web)  
✅ Документация перемещена в `docs/`  
✅ Скрипты перемещены в `scripts/`  
✅ Конфиги перемещены в `config/`  
✅ Данные перемещены в `data/`  
✅ Устаревшие файлы удалены  
✅ Созданы `__init__.py` для всех пакетов  
✅ Обновлен `.gitignore`  

---

## ⚠️ ВАЖНО: После реорганизации

### 1. Проверьте структуру
Убедитесь что все файлы на месте

### 2. НЕ ЗАПУСКАЙТЕ БОТ СРАЗУ!
Сначала нужно обновить импорты или создать точку входа

### 3. Два варианта решения:

#### Вариант A: Создать точку входа в корне (ЛЕГКО)
```python
# Создайте файл bot.py в корне проекта:
#!/usr/bin/env python3
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем и запускаем
from src.bot.bot import main

if __name__ == "__main__":
    main()
```

#### Вариант B: Обновить все импорты (ПРАВИЛЬНО, но долго)
Заменить все импорты во всех файлах:
```python
# Старое:
from user_manager import get_user_role

# Новое:
from src.managers.user_manager import get_user_role
```

---

## 🚀 Запуск после реорганизации

### Если создали точку входа (Вариант A):
```bash
python bot.py  # Из корня проекта
```

### Если обновили импорты (Вариант B):
```bash
python src/bot/bot.py  # Из корня проекта
```

---

## 🔙 Откат (если что-то пошло не так)

```bash
git reset --hard HEAD
git clean -fd
```

---

## 📚 Полная документация

См. `REORGANIZATION_GUIDE.md` для подробностей

---

**Готовы? Запускайте `.\reorganize.ps1`**
