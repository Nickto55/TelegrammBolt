# 📦 Backup старой документации

Эта папка содержит 31 MD файл, которые были удалены при упрощении документации.

## Восстановление

### Все файлы:
```powershell
Move-Item .docs_backup_20251016_083213\* .
```

### Один файл:
```powershell
Move-Item .docs_backup_20251016_083213\FILENAME.md .
```

## Удалить backup:
```powershell
Remove-Item -Recurse -Force .docs_backup_20251016_083213
```
