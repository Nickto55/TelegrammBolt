#!/bin/bash
# TelegrammBolt - Скрипт запуска для Linux/Ubuntu

set -e  # Остановка при любой ошибке

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Запуск TelegrammBolt..."
echo "📁 Рабочая директория: $SCRIPT_DIR"
echo

# Проверяем существование виртуального окружения
if [ ! -f ".venv/bin/python" ]; then
    echo "❌ Ошибка: Виртуальное окружение не найдено!"
    echo "📝 Пожалуйста, создайте виртуальное окружение:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

# Проверяем существование основного файла бота
if [ ! -f "bot.py" ]; then
    echo "❌ Ошибка: Файл bot.py не найден!"
    echo "📁 Убедитесь, что вы запускаете скрипт из корневой директории проекта."
    echo
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

# Активируем виртуальное окружение и запускаем бота
echo "🐍 Активация виртуального окружения..."
source .venv/bin/activate

echo "▶️  Запуск бота..."
echo "=" * 50

# Запускаем бота с обработкой сигналов
trap 'echo -e "\n⏹️  Остановка бота..."; exit 0' SIGINT SIGTERM

.venv/bin/python bot.py

# Если бот завершился с ошибкой, показываем сообщение
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo
    echo "❌ Бот остановлен с кодом ошибки $EXIT_CODE"
    echo "📋 Проверьте логи выше для получения подробностей."
    echo
    read -p "Нажмите Enter для выхода..."
fi