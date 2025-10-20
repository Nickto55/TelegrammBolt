# ============================================
# Скрипт реорганизации проекта TelegrammBolt
# ============================================

Write-Host "🔄 Начинаем реорганизацию проекта TelegrammBolt..." -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# ============================================
# 1. Перемещение Python модулей в src/
# ============================================
Write-Host "📦 Перемещение Python модулей в src/..." -ForegroundColor Yellow

# Основные файлы бота
$botFiles = @(
    "bot.py",
    "commands.py",
    "config.py"
)

# Managers
$managerFiles = @(
    "user_manager.py",
    "chat_manager.py",
    "dse_manager.py",
    "dse_watcher.py",
    "email_manager.py"
)

# Утилиты
$utilFiles = @(
    "pdf_generator.py",
    "genereteTabl.py",
    "gui_manager.py"
)

# Web приложение
$webFiles = @(
    "web_app.py",
    "windows_service.py"
)

# Устаревшие файлы
$deprecatedFiles = @(
    "commands_handlers.py",
    "update_imports.py"
)

# Перемещаем bot файлы
foreach ($file in $botFiles) {
    if (Test-Path $file) {
        Write-Host "  → $file -> src/bot/" -ForegroundColor Gray
        Move-Item -Path $file -Destination "src/bot/" -Force
    }
}

# Перемещаем managers
foreach ($file in $managerFiles) {
    if (Test-Path $file) {
        Write-Host "  → $file -> src/managers/" -ForegroundColor Gray
        Move-Item -Path $file -Destination "src/managers/" -Force
    }
}

# Перемещаем utils
foreach ($file in $utilFiles) {
    if (Test-Path $file) {
        Write-Host "  → $file -> src/utils/" -ForegroundColor Gray
        Move-Item -Path $file -Destination "src/utils/" -Force
    }
}

# Перемещаем web
foreach ($file in $webFiles) {
    if (Test-Path $file) {
        Write-Host "  → $file -> src/web/" -ForegroundColor Gray
        Move-Item -Path $file -Destination "src/web/" -Force
    }
}

Write-Host ""

# ============================================
# 2. Перемещение документации в docs/
# ============================================
Write-Host "📚 Перемещение документации в docs/..." -ForegroundColor Yellow

$docFiles = @(
    "CHEATSHEET.md",
    "DOCKER_TROUBLESHOOTING.md",
    "HTTPS_QUICK_SETUP.txt",
    "HTTPS_SETUP.md",
    "INSTALLATION.md",
    "QUICK_FIX.md",
    "TROUBLESHOOTING.md"
)

foreach ($file in $docFiles) {
    if (Test-Path $file) {
        Write-Host "  → $file -> docs/" -ForegroundColor Gray
        Move-Item -Path $file -Destination "docs/" -Force
    }
}

Write-Host ""

# ============================================
# 3. Перемещение скриптов в scripts/
# ============================================
Write-Host "📜 Перемещение скриптов в scripts/..." -ForegroundColor Yellow

$scriptFiles = @(
    "add-pdf-menu-function.sh",
    "check_installation.sh",
    "cleanup-bot.sh",
    "cleanup-docs.ps1",
    "cleanup-docs.sh",
    "restructure.sh",
    "setup-https.sh",
    "setup.sh",
    "setup_minimal.sh",
    "show-web-url.sh",
    "start_bot.bat",
    "start_bot.sh"
)

foreach ($file in $scriptFiles) {
    if (Test-Path $file) {
        Write-Host "  → $file -> scripts/" -ForegroundColor Gray
        Move-Item -Path $file -Destination "scripts/" -Force
    }
}

Write-Host ""

# ============================================
# 4. Перемещение конфигов в config/
# ============================================
Write-Host "⚙️  Перемещение конфигурационных файлов в config/..." -ForegroundColor Yellow

$configFiles = @(
    "ven_bot.json.example",
    "smtp_config.json.example",
    "nginx.conf",
    "nginx-ssl.conf",
    "telegrambot.service",
    "installer.nsi"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "  → $file -> config/" -ForegroundColor Gray
        Move-Item -Path $file -Destination "config/" -Force
    }
}

# Активные конфиги (только копируем пример, если не существуют)
if (Test-Path "ven_bot.json") {
    Write-Host "  → ven_bot.json -> data/ (сохранен)" -ForegroundColor Gray
    Move-Item -Path "ven_bot.json" -Destination "data/" -Force
}

if (Test-Path "smtp_config.json") {
    Write-Host "  → smtp_config.json -> data/ (сохранен)" -ForegroundColor Gray
    Move-Item -Path "smtp_config.json" -Destination "data/" -Force
}

Write-Host ""

# ============================================
# 5. Перемещение данных в data/
# ============================================
Write-Host "💾 Перемещение данных в data/..." -ForegroundColor Yellow

$dataFiles = @(
    "bot_data.json",
    "users_data.json",
    "RezultBot.xlsx",
    "test_report.pdf"
)

foreach ($file in $dataFiles) {
    if (Test-Path $file) {
        Write-Host "  → $file -> data/" -ForegroundColor Gray
        Move-Item -Path $file -Destination "data/" -Force
    }
}

# Перемещаем photos
if (Test-Path "photos") {
    Write-Host "  → photos/ -> data/photos/" -ForegroundColor Gray
    Move-Item -Path "photos" -Destination "data/" -Force
}

Write-Host ""

# ============================================
# 6. Перемещение веб-ресурсов
# ============================================
Write-Host "🌐 Перемещение веб-ресурсов в src/web/..." -ForegroundColor Yellow

if (Test-Path "static") {
    Write-Host "  → static/ -> src/web/static/" -ForegroundColor Gray
    Move-Item -Path "static" -Destination "src/web/" -Force
}

if (Test-Path "templates") {
    Write-Host "  → templates/ -> src/web/templates/" -ForegroundColor Gray
    Move-Item -Path "templates" -Destination "src/web/" -Force
}

Write-Host ""

# ============================================
# 7. Удаление устаревших файлов
# ============================================
Write-Host "🗑️  Удаление устаревших файлов..." -ForegroundColor Yellow

foreach ($file in $deprecatedFiles) {
    if (Test-Path $file) {
        Write-Host "  ✗ Удален: $file" -ForegroundColor Red
        Remove-Item -Path $file -Force
    }
}

# Удаляем старый backup
if (Test-Path ".docs_backup_20251016_083213") {
    Write-Host "  ✗ Удален старый backup: .docs_backup_20251016_083213" -ForegroundColor Red
    Remove-Item -Path ".docs_backup_20251016_083213" -Recurse -Force
}

Write-Host ""

# ============================================
# 8. Создание __init__.py файлов
# ============================================
Write-Host "📝 Создание __init__.py файлов..." -ForegroundColor Yellow

$initDirs = @(
    "src",
    "src/bot",
    "src/managers",
    "src/utils",
    "src/web"
)

foreach ($dir in $initDirs) {
    $initFile = Join-Path $dir "__init__.py"
    if (-not (Test-Path $initFile)) {
        Write-Host "  + Создан: $initFile" -ForegroundColor Green
        New-Item -Path $initFile -ItemType File -Force | Out-Null
    }
}

Write-Host ""

# ============================================
# Итог
# ============================================
Write-Host "✅ Реорганизация завершена!" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Новая структура проекта:" -ForegroundColor Cyan
Write-Host @"
TelegrammBolt/
├── src/                      # Исходный код
│   ├── bot/                  # Бот и команды
│   ├── managers/             # Менеджеры (user, chat, dse, email)
│   ├── utils/                # Утилиты (pdf, excel)
│   └── web/                  # Веб-приложение
├── config/                   # Конфигурационные файлы (примеры)
├── data/                     # Данные и активные конфиги
├── docs/                     # Документация
├── scripts/                  # Скрипты установки и управления
├── requirements.txt          # Зависимости
└── README.md                 # Главная документация
"@ -ForegroundColor Gray

Write-Host ""
Write-Host "⚠️  ВАЖНО: Обновите пути импорта в коде!" -ForegroundColor Yellow
Write-Host "   Используйте: from src.managers.user_manager import ..." -ForegroundColor Yellow
Write-Host ""
