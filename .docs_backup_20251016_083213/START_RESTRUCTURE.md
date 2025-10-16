# ⚡ START - Реструктуризация TelegrammBolt

> **Начните здесь!** Это ваш входной пункт для реструктуризации проекта.

---

## 🎯 Что это?

Это **автоматическая реструктуризация** проекта TelegrammBolt в профессиональную модульную структуру.

**Было:**
```
50+ файлов в корневой директории 😱
```

**Станет:**
```
src/ config/ data/ docs/ scripts/ tests/ 🎉
```

---

## ⚡ БЫСТРЫЙ СТАРТ (30 секунд)

```bash
# 1. Backup
git add -A && git commit -m "Backup before restructure"

# 2. Run
bash restructure.sh && python update_imports.py

# 3. Done!
python src/bot/main.py
```

**Готово!** Проект реструктурирован! 🎉

---

## 📚 Если хотите больше деталей

### Для новичков:
1. Читайте: **[RESTRUCTURE_INDEX.md](RESTRUCTURE_INDEX.md)** - главная страница
2. Следуйте: **[RESTRUCTURE_HOWTO.md](RESTRUCTURE_HOWTO.md)** - пошаговая инструкция

### Для опытных:
1. Смотрите: **[RESTRUCTURE_PLAN.md](RESTRUCTURE_PLAN.md)** - полный план
2. Используйте: **[RESTRUCTURE_CHEATSHEET.md](RESTRUCTURE_CHEATSHEET.md)** - шпаргалка

### Для визуалов:
1. Изучите: **[STRUCTURE_VISUAL.md](STRUCTURE_VISUAL.md)** - дерево структуры
2. Проверьте: **[RESTRUCTURE_CHECKLIST.md](RESTRUCTURE_CHECKLIST.md)** - чеклист

---

## 🚨 ВАЖНО!

### ✅ Сделайте backup ПЕРЕД запуском:
```bash
git add -A
git commit -m "Backup before restructure v2.0"
```

### ✅ Создайте отдельную ветку:
```bash
git checkout -b restructure-v2
```

### ✅ Активируйте виртуальное окружение:
```bash
source .venv/bin/activate
```

---

## 🛠️ Что делают скрипты?

### restructure.sh
- Создает резервную копию
- Создает новую структуру директорий
- Перемещает все файлы
- Создает __init__.py
- Обновляет .gitignore

### update_imports.py
- Обновляет импорты в Python файлах
- Обновляет пути к файлам
- Обновляет команды в скриптах

---

## 📊 Новая структура (кратко)

```
TelegrammBolt/
├── src/          → Весь код (bot, web, shared)
├── config/       → Конфигурация (токены, настройки)
├── data/         → Данные (json, excel, фото)
├── scripts/      → Скрипты (setup, start, maintenance)
├── docs/         → Документация (guides, troubleshooting)
└── tests/        → Тесты
```

---

## ✅ Проверка после выполнения

```bash
# 1. Структура создана?
ls src/ config/ data/ scripts/ docs/ tests/

# 2. Импорты обновлены?
python -c "from src.bot.main import *"

# 3. Бот запускается?
python src/bot/main.py

# 4. Всё работает?
# Отправьте /start боту в Telegram
```

---

## 🔄 Откат (если что-то не так)

```bash
# Вернуться к backup
git reset --hard HEAD
git clean -fd

# Или использовать резервную копию
cp -r ../TelegrammBolt_backup_*/* .
```

---

## 🎯 Следующие шаги

После успешной реструктуризации:

1. **Проверьте** что всё работает
2. **Протестируйте** бота и веб
3. **Закоммитьте** изменения
4. **Создайте** Pull Request
5. **Merge** в main/web ветку

---

## 📞 Нужна помощь?

- **Документация**: Все файлы RESTRUCTURE_*.md
- **Issues**: [GitHub Issues](https://github.com/Nickto55/TelegrammBolt/issues)
- **Чеклист**: [RESTRUCTURE_CHECKLIST.md](RESTRUCTURE_CHECKLIST.md)

---

<div align="center">

## 🚀 ГОТОВЫ? ЗАПУСТИТЕ:

```bash
bash restructure.sh
```

### Затем:

```bash
python update_imports.py
```

### Готово! 🎉

</div>

---

**Удачи с реструктуризацией!** ⚡

_Подробности в [RESTRUCTURE_INDEX.md](RESTRUCTURE_INDEX.md)_
