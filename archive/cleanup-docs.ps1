# cleanup-docs.ps1 - Удаление лишних MD файлов (оставляем только 4)

Write-Host "🧹 Удаление лишних MD файлов..." -ForegroundColor Cyan

# Создать папку для backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = ".docs_backup_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Список файлов для СОХРАНЕНИЯ (только 4!)
$keepFiles = @(
    "README.md",
    "INSTALLATION.md",
    "TROUBLESHOOTING.md",
    "CHEATSHEET.md"
)

Write-Host "`n📁 Файлы которые останутся:" -ForegroundColor Green
$keepFiles | ForEach-Object { Write-Host "   - $_" }

Write-Host "`n🗑️  Удаляемые файлы (будут перемещены в $backupDir):" -ForegroundColor Yellow

# Найти все MD файлы
$mdFiles = Get-ChildItem -Path . -Filter "*.md" -File

$movedCount = 0
foreach ($file in $mdFiles) {
    # Проверить, находится ли в списке сохранения
    if ($keepFiles -notcontains $file.Name) {
        Write-Host "   - $($file.Name)" -ForegroundColor Gray
        Move-Item -Path $file.FullName -Destination $backupDir -Force
        $movedCount++
    }
}

Write-Host "`n✅ Готово!" -ForegroundColor Green
Write-Host "`n📊 Результат:" -ForegroundColor Cyan
Write-Host "   Перемещено файлов: $movedCount"
Write-Host "   Осталось файлов: $($keepFiles.Count)"
Write-Host "   Backup: $backupDir"

Write-Host "`n💡 Восстановить файлы: Move-Item $backupDir\* ." -ForegroundColor Yellow

# Показать оставшиеся файлы
Write-Host "`n📄 Оставшиеся MD файлы:" -ForegroundColor Cyan
Get-ChildItem -Path . -Filter "*.md" -File | ForEach-Object {
    Write-Host "   ✓ $($_.Name)" -ForegroundColor Green
}
