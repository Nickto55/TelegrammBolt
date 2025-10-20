# Отправка исправлений на сервер

Write-Host "================================================" -ForegroundColor Cyan
Write-Host " ОТПРАВКА ИСПРАВЛЕНИЙ НА СЕРВЕР" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$SERVER = "root@87.120.166.213"
$REMOTE_PATH = "/root/TelegrammBolt"

Write-Host "Отправка файлов на сервер $SERVER..." -ForegroundColor Yellow
Write-Host ""

# Проверка наличия scp
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ОШИБКА: scp не найден!" -ForegroundColor Red
    Write-Host "Установите OpenSSH Client:" -ForegroundColor Yellow
    Write-Host "  Settings > Apps > Optional Features > Add OpenSSH Client" -ForegroundColor Gray
    exit 1
}

try {
    # Основные файлы
    Write-Host "[1/4] Отправка web_app.py..." -ForegroundColor Green
    scp web_app.py "${SERVER}:${REMOTE_PATH}/"
    
    Write-Host "[2/4] Отправка диагностических скриптов..." -ForegroundColor Green
    scp server_check.py, check_dse_id.py, diagnose_dse.py, clear_logs.py "${SERVER}:${REMOTE_PATH}/"
    
    Write-Host "[3/4] Отправка shell скриптов..." -ForegroundColor Green
    scp restart_web.sh, fix_server.sh "${SERVER}:${REMOTE_PATH}/"
    
    Write-Host "[4/4] Отправка документации..." -ForegroundColor Green
    scp SERVER_FIX.md, QUICK_SERVER_FIX.md, FIX_INSTRUCTIONS.txt, FIX_SUMMARY.md, README_FIX.txt "${SERVER}:${REMOTE_PATH}/"
    
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host " ✅ ФАЙЛЫ УСПЕШНО ОТПРАВЛЕНЫ!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Следующие шаги:" -ForegroundColor Yellow
    Write-Host "  1. Подключитесь к серверу:" -ForegroundColor White
    Write-Host "     ssh $SERVER" -ForegroundColor Gray
    Write-Host "  2. Перейдите в директорию:" -ForegroundColor White
    Write-Host "     cd $REMOTE_PATH" -ForegroundColor Gray
    Write-Host "  3. Дайте права на выполнение:" -ForegroundColor White
    Write-Host "     chmod +x *.sh" -ForegroundColor Gray
    Write-Host "  4. Запустите диагностику:" -ForegroundColor White
    Write-Host "     python3 server_check.py" -ForegroundColor Gray
    Write-Host "  5. Перезапустите сервер:" -ForegroundColor White
    Write-Host "     bash restart_web.sh" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ ОШИБКА: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Попробуйте подключиться вручную:" -ForegroundColor Yellow
    Write-Host "  ssh $SERVER" -ForegroundColor Gray
    exit 1
}

Write-Host "Нажмите любую клавишу для выхода..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
