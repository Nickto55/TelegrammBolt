#!/bin/bash

# TelegrammBolt Mobile App - Полная установка и запуск
# Для Linux/macOS

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════╗"
echo "║   TelegrammBolt Mobile App - Быстрая Помощь   ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Node.js
echo ""
echo -e "${YELLOW}Проверка требований...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED} Node.js не найден${NC}"
    echo "Установите Node.js 16+ с https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN} Node.js $(node --version)${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED} npm не найден${NC}"
    exit 1
fi
echo -e "${GREEN} npm $(npm --version)${NC}"

# Navigate to mobile directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOBILE_DIR="$SCRIPT_DIR/mobile"

if [ ! -d "$MOBILE_DIR" ]; then
    echo -e "${RED} Папка /mobile не найдена${NC}"
    exit 1
fi

cd "$MOBILE_DIR"
echo -e "${GREEN} Скрипт запущен из: $MOBILE_DIR${NC}"

# Create .env file
echo ""
echo -e "${YELLOW}Конфигурирование приложения...${NC}"

if [ ! -f "$MOBILE_DIR/.env" ]; then
    echo "Создание .env файла..."
    cp .env.example .env
    echo -e "${GREEN} .env создан${NC}"
    echo ""
    echo -e "${BLUE} Отредактируйте .env файл если нужно:${NC}"
    echo "   API_BASE_URL=http://localhost:5000"
    echo ""
else
    echo -e "${GREEN} .env уже существует${NC}"
fi

# Install dependencies
echo ""
echo -e "${YELLOW}Установка зависимостей (это может занять время)...${NC}"
npm install

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Готово к запуску!                  ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════╝${NC}"

echo ""
echo -e "${BLUE}🚀 Запуск приложения:${NC}"
echo ""
echo "Выберите платформу:"
echo "  1) Запустить dev сервер (npm start)"
echo "  2) Запустить на iOS (npm run ios)"
echo "  3) Запустить на Android (npm run android)"
echo "  4) Запустить веб (npm run web)"
echo "  5) Собрать APK файл (EAS Build)"
echo "  6) Выход"
echo ""
read -p "Выберите (1-6): " choice

case $choice in
    1)
        echo -e "${BLUE}Запуск dev сервера...${NC}"
        npm start
        ;;
    2)
        echo -e "${BLUE}Запуск на iOS...${NC}"
        npm run ios
        ;;
    3)
        echo -e "${BLUE}Запуск на Android...${NC}"
        npm run android
        ;;
    4)
        echo -e "${BLUE}Запуск веб версии...${NC}"
        npm run web
        ;;
    5)
        echo -e "${BLUE}Подготовка к сборке APK...${NC}"
        # Check if eas-cli is installed
        if ! command -v eas &> /dev/null; then
            echo -e "${YELLOW}Установка eas-cli...${NC}"
            npm install -g eas-cli
        fi
        echo -e "${BLUE}Запуск сборки APK (облачная сборка)...${NC}"
        echo "Это может занять 10-15 минут..."
        eas build --platform android --local
        echo -e "${GREEN}✅ APK собран! Ссылка для скачивания выше.${NC}"
        ;;
    6)
        echo -e "${YELLOW}До свидания!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Неверный выбор${NC}"
        exit 1
        ;;
esac
