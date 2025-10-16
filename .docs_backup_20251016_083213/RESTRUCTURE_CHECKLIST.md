# ✅ Контрольный список реструктуризации

## 📋 Используйте этот чеклист для отслеживания прогресса

---

## 🎯 Подготовка

- [ ] Прочитана вся документация:
  - [ ] RESTRUCTURE_INDEX.md
  - [ ] RESTRUCTURE_PLAN.md
  - [ ] RESTRUCTURE_HOWTO.md
  - [ ] STRUCTURE_VISUAL.md
  - [ ] RESTRUCTURE_CHEATSHEET.md

- [ ] Понята новая структура проекта

- [ ] Создана резервная копия:
  ```bash
  git add -A
  git commit -m "Backup before restructure v2.0"
  ```

- [ ] Создана новая ветка:
  ```bash
  git checkout -b restructure-v2
  ```

- [ ] Виртуальное окружение активировано:
  ```bash
  source .venv/bin/activate
  ```

---

## 🛠️ Выполнение

- [ ] Запущен скрипт restructure.sh:
  ```bash
  bash restructure.sh
  ```

- [ ] Проверен вывод скрипта на ошибки

- [ ] Резервная копия создана скриптом:
  ```
  Путь: ../TelegrammBolt_backup_YYYYMMDD_HHMMSS
  ```

- [ ] Структура директорий создана:
  ```bash
  ls -la src/ config/ data/ scripts/ docs/ tests/
  ```

- [ ] Запущен update_imports.py:
  ```bash
  python update_imports.py
  ```

- [ ] Проверен вывод обновления импортов

---

## 🔍 Проверка

### Структура файлов

- [ ] Исходный код перемещен:
  - [ ] src/bot/main.py (ex bot.py)
  - [ ] src/bot/handlers/commands.py
  - [ ] src/bot/managers/user_manager.py
  - [ ] src/bot/managers/chat_manager.py
  - [ ] src/bot/managers/dse_manager.py
  - [ ] src/bot/workers/dse_watcher.py
  - [ ] src/bot/utils/pdf_generator.py
  - [ ] src/web/app.py (ex web_app.py)

- [ ] Конфигурация перемещена:
  - [ ] config/ven_bot.json
  - [ ] config/smtp_config.json
  - [ ] config/nginx.conf

- [ ] Данные перемещены:
  - [ ] data/bot_data.json
  - [ ] data/users_data.json
  - [ ] data/photos/

- [ ] Скрипты перемещены:
  - [ ] scripts/setup/setup.sh
  - [ ] scripts/start/start_bot.sh
  - [ ] scripts/maintenance/cleanup-bot.sh

- [ ] Документация перемещена:
  - [ ] docs/installation/
  - [ ] docs/configuration/
  - [ ] docs/troubleshooting/
  - [ ] docs/guides/
  - [ ] docs/reference/

### __init__.py файлы

- [ ] src/__init__.py
- [ ] src/bot/__init__.py
- [ ] src/bot/handlers/__init__.py
- [ ] src/bot/managers/__init__.py
- [ ] src/bot/workers/__init__.py
- [ ] src/bot/utils/__init__.py
- [ ] src/web/__init__.py
- [ ] src/web/routes/__init__.py
- [ ] src/shared/__init__.py
- [ ] tests/__init__.py

### Новые файлы

- [ ] README.md (новый главный README)
- [ ] .gitignore (обновлен)
- [ ] .gitkeep в пустых директориях

### Git проверка

- [ ] Просмотр изменений:
  ```bash
  git status
  git diff
  ```

- [ ] Проверка новой структуры:
  ```bash
  tree -L 3
  # или
  ls -R
  ```

---

## 🧪 Тестирование

### Импорты

- [ ] Проверка импортов в Python:
  ```bash
  python -c "from src.bot.main import *"
  python -c "from src.web.app import *"
  python -c "from src.bot.managers.user_manager import UserManager"
  ```

- [ ] Нет ошибок ImportError

### Запуск бота

- [ ] Бот запускается без ошибок:
  ```bash
  python src/bot/main.py
  ```

- [ ] Или через модуль:
  ```bash
  python -m src.bot.main
  ```

- [ ] Бот подключается к Telegram API

- [ ] Нет ошибок в консоли

### Telegram команды

- [ ] Отправлена команда /start в бота

- [ ] Бот отвечает без ошибок

- [ ] Проверены другие команды:
  - [ ] /help
  - [ ] /add
  - [ ] /list

### Веб-интерфейс

- [ ] Веб запускается без ошибок:
  ```bash
  python src/web/app.py
  ```

- [ ] Веб доступен по адресу:
  ```
  http://localhost:5000
  ```

- [ ] Страница логина открывается

- [ ] Авторизация через Telegram работает

- [ ] Dashboard отображается корректно

### Пути к файлам

- [ ] Конфигурация читается:
  ```bash
  python -c "import json; print(json.load(open('config/ven_bot.json')))"
  ```

- [ ] Данные читаются:
  ```bash
  python -c "import json; print(json.load(open('data/bot_data.json')))"
  ```

- [ ] Фотографии доступны:
  ```bash
  ls -la data/photos/
  ```

### Скрипты

- [ ] Скрипты запускаются:
  ```bash
  bash scripts/maintenance/cleanup-bot.sh
  bash scripts/maintenance/show-web-url.sh
  ```

- [ ] Пути в скриптах обновлены

---

## 📝 Документация

- [ ] README.md содержит актуальную информацию

- [ ] PROJECT_STRUCTURE.md обновлен

- [ ] CHANGELOG.md содержит запись о v2.0

- [ ] Все ссылки в документации работают

- [ ] Примеры кода актуальны

---

## 🔄 Git операции

- [ ] Все изменения добавлены:
  ```bash
  git add -A
  ```

- [ ] Создан коммит:
  ```bash
  git commit -m "Restructure project v2.0

  - New modular structure
  - Separated code, config, data, docs
  - Updated imports and paths
  - Created __init__.py files
  - Updated documentation"
  ```

- [ ] Ветка запушена:
  ```bash
  git push origin restructure-v2
  ```

---

## 🚀 Pull Request

- [ ] Pull Request создан на GitHub

- [ ] Описание PR содержит:
  - Цель реструктуризации
  - Основные изменения
  - Инструкции по тестированию
  - Breaking changes (если есть)

- [ ] Назначены reviewers

- [ ] Добавлены labels (restructure, v2.0, breaking)

- [ ] CI/CD тесты прошли (если настроены)

---

## 📋 Post-merge задачи

После мержа в main/web ветку:

- [ ] Обновлена документация на GitHub Pages (если есть)

- [ ] Создан release v2.0.0:
  ```bash
  git tag -a v2.0.0 -m "Version 2.0.0: Project restructure"
  git push origin v2.0.0
  ```

- [ ] Release notes опубликованы

- [ ] Обновлены скрипты установки

- [ ] Пользователи уведомлены о breaking changes

- [ ] Создан миграционный гайд для существующих установок

---

## 🎉 Завершение

- [ ] Все пункты чеклиста выполнены

- [ ] Проект успешно реструктурирован

- [ ] Документация актуальна

- [ ] Тесты проходят

- [ ] Готово к production

---

## 📊 Статистика

После завершения:

- Дата начала: _______________
- Дата окончания: _______________
- Время выполнения: _______________
- Количество файлов перемещено: _______________
- Количество директорий создано: _______________
- Количество обновленных импортов: _______________

---

## 🆘 Если что-то пошло не так

- [ ] Проверены логи ошибок

- [ ] Использован откат:
  ```bash
  git reset --hard HEAD
  git clean -fd
  ```

- [ ] Восстановлена резервная копия

- [ ] Создан issue на GitHub с описанием проблемы

- [ ] Запрошена помощь в сообществе

---

## 💡 Заметки

_Используйте это пространство для записи важных моментов, ошибок или советов:_

```
_________________________________
_________________________________
_________________________________
_________________________________
_________________________________
```

---

**Прогресс:** ▢▢▢▢▢▢▢▢▢▢ 0%

**Статус:** ⏳ Не начато / 🚧 В процессе / ✅ Завершено

---

_Обновите статус по мере выполнения пунктов!_
