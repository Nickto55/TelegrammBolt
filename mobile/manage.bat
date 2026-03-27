#!/bin/bash

# Windows Batch Script для управления мобильным приложением
# Usage: manage.bat <command>

@echo off
setlocal enabledelayedexpansion

:menu
cls
echo ================================
echo TelegrammBolt Mobile App Manager
echo ================================
echo.
echo 1. Start development server
echo 2. Build for iOS
echo 3. Build for Android  
echo 4. Install dependencies
echo 5. Clean cache
echo 6. Exit
echo.
set /p choice="Select option (1-6): "

if "%choice%"=="1" goto start_dev
if "%choice%"=="2" goto build_ios
if "%choice%"=="3" goto build_android
if "%choice%"=="4" goto install_deps
if "%choice%"=="5" goto clean_cache
if "%choice%"=="6" goto end
goto menu

:start_dev
echo Starting development server...
call npm start
goto menu

:build_ios
echo Building for iOS...
call npm run ios
goto menu

:build_android
echo Building for Android...
call npm run android
goto menu

:install_deps
echo Installing dependencies...
call npm install
goto menu

:clean_cache
echo Cleaning cache...
call npm start -- --clear
goto menu

:end
echo Goodbye!
exit /b 0
