@echo off
title TelegrammBolt - Telegram Bot
cd /d "%~dp0"
echo Starting TelegrammBolt...
echo.

REM Проверяем существование виртуального окружения
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please create virtual environment first:
    echo python -m venv .venv
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

REM Активируем виртуальное окружение и запускаем бота
.venv\Scripts\python.exe bot.py

REM Если бот завершился с ошибкой, показываем сообщение
if errorlevel 1 (
    echo.
    echo Bot stopped with error code %errorlevel%
    echo Check the logs above for details.
    pause
)