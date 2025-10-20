# 🚀 Быстрое применение исправлений для Windows
# Дата: $(Get-Date)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🔧 ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ ДЛЯ TELEGRAM БОТА" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Проверка директории
if (-not (Test-Path ".\bot.py")) {
    Write-Host "❌ Ошибка: bot.py не найден в текущей директории" -ForegroundColor Red
    Write-Host "📍 Перейдите в директорию с ботом" -ForegroundColor Yellow
    exit 1
}

Write-Host "📍 Текущая директория: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Остановка бота
Write-Host "⏸️  Остановка бота..." -ForegroundColor Yellow
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*bot.py*"} | Stop-Process -Force
Start-Sleep -Seconds 2

# Проверка портов
Write-Host "🔍 Проверка портов..." -ForegroundColor Yellow
$Port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($Port5000) {
    Write-Host "⚠️  Порт 5000 занят, освобождаем..." -ForegroundColor Yellow
    $Port5000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
}

# Резервное копирование
Write-Host "💾 Создание резервной копии..." -ForegroundColor Yellow
$BackupDir = "backups\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item "commands.py" "$BackupDir\" -ErrorAction SilentlyContinue
Copy-Item "pdf_generator.py" "$BackupDir\" -ErrorAction SilentlyContinue
Write-Host "   Резервная копия: $BackupDir" -ForegroundColor Green
Write-Host ""

# Проверка Python окружения
Write-Host "🐍 Проверка Python окружения..." -ForegroundColor Yellow
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    . ".\venv\Scripts\Activate.ps1"
    Write-Host "   ✅ Virtual environment активирован" -ForegroundColor Green
} elseif (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . ".\.venv\Scripts\Activate.ps1"
    Write-Host "   ✅ Virtual environment активирован" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Virtual environment не найден, используем системный Python" -ForegroundColor Yellow
}

# Проверка зависимостей
Write-Host "📦 Проверка зависимостей..." -ForegroundColor Yellow
python -c "import telegram, flask, reportlab" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️  Устанавливаем отсутствующие зависимости..." -ForegroundColor Yellow
    pip install python-telegram-bot flask reportlab pillow psutil -q
}

# Проверка файлов конфигурации
Write-Host "⚙️  Проверка конфигурации..." -ForegroundColor Yellow
if (-not (Test-Path "ven_bot.json")) {
    Write-Host "   ❌ Ошибка: ven_bot.json не найден" -ForegroundColor Red
    exit 1
}

$BotConfig = Get-Content "ven_bot.json" | ConvertFrom-Json
if ([string]::IsNullOrEmpty($BotConfig.BOT_USERNAME)) {
    Write-Host "   ⚠️  Предупреждение: BOT_USERNAME пустой в ven_bot.json" -ForegroundColor Yellow
    Write-Host "   📝 Установите его в конфигурации для работы веб-авторизации" -ForegroundColor Yellow
}

# Запуск бота
Write-Host ""
Write-Host "🚀 Запуск бота..." -ForegroundColor Yellow
$BotProcess = Start-Process python -ArgumentList "bot.py" -NoNewWindow -PassThru -RedirectStandardOutput "bot.log" -RedirectStandardError "bot_error.log"

# Ожидание запуска
Write-Host "⏳ Ожидание инициализации (5 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Проверка статуса
if (Get-Process -Id $BotProcess.Id -ErrorAction SilentlyContinue) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "✅ БОТ УСПЕШНО ЗАПУЩЕН!" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Информация:" -ForegroundColor Cyan
    Write-Host "   - PID: $($BotProcess.Id)"
    Write-Host "   - Логи: Get-Content bot.log -Wait"
    Write-Host "   - Web: http://localhost:5000 (если включен)"
    Write-Host ""
    Write-Host "🧪 Тестирование исправлений:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   1️⃣  Изменение роли пользователя:" -ForegroundColor Yellow
    Write-Host "      - Панель администратора → Изменить роль"
    Write-Host "      - Выбрать пользователя → Выбрать роль"
    Write-Host "      - ✅ Должно показать: 'Роль изменена на: [Роль]'" -ForegroundColor Green
    Write-Host ""
    Write-Host "   2️⃣  Выборочный экспорт PDF:" -ForegroundColor Yellow
    Write-Host "      - Главное меню → Экспорт в PDF"
    Write-Host "      - Выбрать записи → Выбрать ДСЕ"
    Write-Host "      - Экспорт выбранных"
    Write-Host "      - ✅ Должны прийти PDF файлы" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Команды управления:" -ForegroundColor Cyan
    Write-Host "   - Остановить: Stop-Process -Id $($BotProcess.Id)"
    Write-Host "   - Перезапустить: .\apply-fixes.ps1"
    Write-Host "   - Логи: Get-Content bot.log -Wait"
    Write-Host "   - Ошибки: Get-Content bot_error.log"
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ ОШИБКА ЗАПУСКА БОТА" -ForegroundColor Red
    Write-Host "==================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔍 Проверьте логи:" -ForegroundColor Yellow
    Write-Host "   Get-Content bot.log"
    Write-Host "   Get-Content bot_error.log"
    Write-Host ""
    Write-Host "📝 Последние строки лога:" -ForegroundColor Yellow
    if (Test-Path "bot.log") {
        Get-Content "bot.log" -Tail 20
    }
    if (Test-Path "bot_error.log") {
        Get-Content "bot_error.log" -Tail 20
    }
    Write-Host ""
    Write-Host "🛠️  Возможные причины:" -ForegroundColor Yellow
    Write-Host "   - Неверный токен в ven_bot.json"
    Write-Host "   - Порт 5000 занят другим процессом"
    Write-Host "   - Отсутствуют зависимости Python"
    Write-Host "   - Синтаксическая ошибка в коде"
    Write-Host ""
    exit 1
}

Write-Host "✨ Готово!" -ForegroundColor Green
