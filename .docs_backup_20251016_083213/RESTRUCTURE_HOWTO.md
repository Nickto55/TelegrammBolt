# 🚀 Как выполнить реструктуризацию

## ⚡ Быстрый старт

```bash
# 1. Создать резервную копию
git add -A
git commit -m "Backup before restructure"

# 2. Выполнить реструктуризацию
bash restructure.sh

# 3. Обновить импорты
python update_imports.py

# 4. Проверить изменения
git status
git diff

# 5. Тестировать
python src/bot/main.py
```

---

## 📋 Пошаговая инструкция

### Шаг 1: Подготовка

```bash
# Убедитесь что вы в ветке web
git branch

# Создайте новую ветку для реструктуризации
git checkout -b restructure-v2

# Закоммитьте текущее состояние
git add -A
git commit -m "Backup before restructure"
```

### Шаг 2: Выполнение реструктуризации

```bash
# Запустить скрипт
bash restructure.sh
```

Скрипт выполнит:
- ✅ Создание резервной копии в `../TelegrammBolt_backup_YYYYMMDD_HHMMSS`
- ✅ Создание новой структуры директорий
- ✅ Перемещение всех файлов
- ✅ Создание __init__.py файлов
- ✅ Создание нового README.md
- ✅ Обновление .gitignore

### Шаг 3: Обновление импортов

```bash
# Автоматически обновить импорты во всех файлах
python update_imports.py
```

Скрипт обновит:
- Импорты в Python файлах
- Пути к файлам данных
- Пути к конфигурационным файлам
- Команды в shell скриптах

### Шаг 4: Проверка

```bash
# Посмотреть что изменилось
git status

# Посмотреть детали изменений
git diff src/bot/main.py
git diff src/web/app.py

# Проверить новую структуру
tree -L 3  # или ls -R
```

### Шаг 5: Тестирование

#### Тест бота:

```bash
# Активировать виртуальное окружение
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows

# Запустить бота
python src/bot/main.py
# или
python -m src.bot.main

# Отправить /start в Telegram
# Проверить что бот отвечает
```

#### Тест веб-интерфейса:

```bash
# Запустить веб (в отдельном терминале)
python src/web/app.py

# Открыть в браузере
# http://localhost:5000

# Проверить авторизацию через Telegram
```

#### Тест установки:

```bash
# В новой директории
mkdir test_install
cd test_install

# Клонировать ветку
git clone -b restructure-v2 https://github.com/Nickto55/TelegrammBolt.git .

# Запустить установку
bash scripts/setup/setup.sh

# Проверить что всё работает
```

### Шаг 6: Финализация

```bash
# Если всё работает, закоммитить
git add -A
git commit -m "Restructure project v2.0"

# Пушнуть ветку
git push origin restructure-v2

# Создать Pull Request в GitHub
# После ревью - смержить в web/main
```

---

## 🔄 Откат изменений

Если что-то пошло не так:

### Вариант 1: Git reset
```bash
# Вернуться к последнему коммиту
git reset --hard HEAD

# Удалить все неотслеживаемые файлы
git clean -fd
```

### Вариант 2: Использовать резервную копию
```bash
# Найти резервную копию
ls -la ../TelegrammBolt_backup_*

# Восстановить
rm -rf *
cp -r ../TelegrammBolt_backup_YYYYMMDD_HHMMSS/* .
```

### Вариант 3: Переключиться на другую ветку
```bash
git checkout web
# или
git checkout main
```

---

## 📊 Проверочный список

### Перед реструктуризацией:
- [ ] Создана резервная копия (git commit)
- [ ] Создана новая ветка (restructure-v2)
- [ ] Виртуальное окружение активировано
- [ ] Все файлы сохранены

### После реструктуризации:
- [ ] Скрипт restructure.sh выполнен успешно
- [ ] Скрипт update_imports.py выполнен успешно
- [ ] Новая структура проверена (tree или ls)
- [ ] README.md создан
- [ ] .gitignore обновлен

### Тестирование:
- [ ] Бот запускается (python src/bot/main.py)
- [ ] Бот отвечает на /start в Telegram
- [ ] Веб-интерфейс доступен (http://localhost:5000)
- [ ] Авторизация через Telegram работает
- [ ] Нет ошибок импорта
- [ ] Пути к файлам корректные

### Git:
- [ ] Изменения закоммичены
- [ ] Ветка запушена
- [ ] Pull Request создан
- [ ] Тесты прошли успешно

---

## 🛠️ Ручное исправление

Если автоматические скрипты не справились, вот что нужно исправить вручную:

### 1. Импорты в src/bot/main.py

```python
# Было:
from user_manager import UserManager
from chat_manager import ChatManager
from dse_manager import DSEManager
from commands import *

# Стало:
from src.bot.managers.user_manager import UserManager
from src.bot.managers.chat_manager import ChatManager
from src.bot.managers.dse_manager import DSEManager
from src.bot.handlers.commands import *
```

### 2. Импорты в src/web/app.py

```python
# Было:
from user_manager import UserManager
from dse_manager import DSEManager

# Стало:
from src.bot.managers.user_manager import UserManager
from src.bot.managers.dse_manager import DSEManager
```

### 3. Пути к файлам

```python
# Было:
with open('bot_data.json', 'r') as f:

# Стало:
with open('data/bot_data.json', 'r') as f:
```

### 4. Скрипты запуска

**scripts/start/start_bot.sh:**
```bash
# Было:
python bot.py

# Стало:
python src/bot/main.py
```

---

## 💡 Советы

1. **Используйте IDE** для автоматического рефакторинга импортов (PyCharm, VS Code)

2. **Поиск и замена** в редакторе:
   ```
   Find:    from user_manager import
   Replace: from src.bot.managers.user_manager import
   ```

3. **Проверка импортов** в Python:
   ```python
   python -c "from src.bot.main import *"
   ```

4. **Линтер** поможет найти проблемы:
   ```bash
   pylint src/bot/main.py
   flake8 src/
   ```

---

## 📞 Помощь

Если возникли проблемы:

1. Проверьте логи: `cat logs/error.log`
2. Проверьте импорты: `python -m src.bot.main`
3. Откройте issue на GitHub
4. Проверьте документацию: `docs/`

---

**Готовы начать?** Запустите `bash restructure.sh` 🚀
