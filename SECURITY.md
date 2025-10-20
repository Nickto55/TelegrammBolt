# 🔒 Безопасность

## Конфиденциальные данные

**⚠️ ВАЖНО:** Следующие файлы содержат конфиденциальную информацию и **НЕ ДОЛЖНЫ** попадать в git:

### Токены и ключи
- `config/ven_bot.json` - BOT_TOKEN Telegram
- `config/smtp_config.json` - SMTP пароли
- Любые файлы с `.secret` или `.key` расширением

### Данные пользователей
- `data/` - ВСЯ папка (заявки, пользователи, чаты)
- `photos/` - Фотографии заявок

### Бэкапы
- `backup_*/` - Любые бэкапы с датой
- `archive/` - Архив старых файлов
- `.docs_backup_*/` - Бэкапы документации

## Проверка перед коммитом

Перед каждым `git push` выполняйте:

```bash
# Проверить что игнорируется
git status --ignored

# Убедиться что конфиденциальных файлов нет
git ls-files | Select-String -Pattern "ven_bot.json|smtp_config|bot_data|users_data|backup"
```

## Если случайно закоммитили секреты

### 1. Удалить из последнего коммита
```bash
git rm --cached config/ven_bot.json
git commit --amend -m "Remove secrets"
git push --force
```

### 2. Удалить из истории (если уже запушили)
```bash
# ОПАСНО! Перезапишет историю!
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config/ven_bot.json" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

### 3. Сменить токены!
**КРИТИЧЕСКИ ВАЖНО:** Если токен попал в git - считайте его скомпрометированным:
1. Зайдите в @BotFather
2. Используйте `/token` → выберите бота → `/revoke`
3. Получите новый токен
4. Обновите `config/ven_bot.json`

## Настройка .gitignore

Файл `.gitignore` уже настроен правильно. Проверить можно так:

```bash
# Проверить что файл игнорируется
git check-ignore -v config/ven_bot.json

# Должен вывести:
# .gitignore:XX:config/ven_bot.json    config/ven_bot.json
```

## Безопасная работа

### ✅ ПРАВИЛЬНО
```bash
# Перед коммитом проверяйте
git status
git diff --staged

# Используйте .gitignore
# Храните секреты ТОЛЬКО локально
```

### ❌ НЕПРАВИЛЬНО
```bash
# НЕ делайте так!
git add .  # без проверки
git commit -am "fix"  # без просмотра изменений
git push  # без проверки что коммитите
```

## Автоматическая проверка

Создайте pre-commit hook:

```bash
# .git/hooks/pre-commit
#!/bin/sh
if git diff --cached --name-only | grep -E "ven_bot\.json|smtp_config\.json|bot_data\.json|users_data\.json"; then
    echo "❌ ОШИБКА: Попытка закоммитить конфиденциальные файлы!"
    echo "Проверьте .gitignore"
    exit 1
fi
```

## Что делать при утечке

1. **Немедленно** смените все токены и пароли
2. Удалите файлы из git истории (см. выше)
3. Force push новую историю
4. Проверьте логи GitHub на предмет доступа
5. Пересоздайте бота если нужно

## Проверка репозитория

```bash
# Поиск возможных секретов в истории
git log --all --full-history -- config/ven_bot.json

# Должно быть пусто!
```
