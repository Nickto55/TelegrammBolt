#!/bin/bash
# cleanup-docs.sh - Удаление лишних MD файлов (оставляем только 4)

echo "🧹 Удаление лишних MD файлов..."

# Переместить старые файлы в backup
mkdir -p .docs_backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=".docs_backup_$(date +%Y%m%d_%H%M%S)"

# Список файлов для СОХРАНЕНИЯ (только 4!)
KEEP_FILES=(
    "README.md"
    "INSTALLATION.md"
    "TROUBLESHOOTING.md"
    "CHEATSHEET.md"
)

echo "📁 Файлы которые останутся:"
printf '%s\n' "${KEEP_FILES[@]}"

echo ""
echo "🗑️  Удаляемые файлы (будут перемещены в $BACKUP_DIR):"

# Найти все MD файлы
for md_file in *.md docs/*.md 2>/dev/null; do
    # Пропустить несуществующие файлы
    [ -f "$md_file" ] || continue
    
    # Получить имя файла
    filename=$(basename "$md_file")
    
    # Проверить, находится ли в списке сохранения
    keep=0
    for keep_file in "${KEEP_FILES[@]}"; do
        if [ "$filename" = "$keep_file" ]; then
            keep=1
            break
        fi
    done
    
    # Если не в списке - переместить в backup
    if [ $keep -eq 0 ]; then
        echo "  - $md_file"
        mv "$md_file" "$BACKUP_DIR/" 2>/dev/null
    fi
done

echo ""
echo "✅ Готово!"
echo ""
echo "📊 Результат:"
echo "   Осталось файлов: $(ls -1 *.md 2>/dev/null | wc -l)"
echo "   Backup: $BACKUP_DIR"
echo ""
echo "💡 Восстановить файлы: mv $BACKUP_DIR/* ."

# Показать оставшиеся файлы
echo ""
echo "📄 Оставшиеся MD файлы:"
ls -1 *.md 2>/dev/null
