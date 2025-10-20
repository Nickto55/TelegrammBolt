# Запуск веб-приложения в режиме разработки (PowerShell)

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  Запуск веб-приложения TelegrammBolt в режиме разработки" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Режим: " -NoNewline; Write-Host "Development (Debug)" -ForegroundColor Yellow
Write-Host "  Auto-reload: " -NoNewline; Write-Host "Включен" -ForegroundColor Green
Write-Host "  Адрес: " -NoNewline; Write-Host "http://127.0.0.1:5000" -ForegroundColor Blue
Write-Host ""
Write-Host "  Для остановки нажмите Ctrl+C" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Запуск приложения
python run_web_dev.py

# Пауза перед закрытием окна
Read-Host "Нажмите Enter для закрытия"
