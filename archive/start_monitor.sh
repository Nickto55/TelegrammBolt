#!/bin/bash
# TelegrammBolt Monitor Launcher для Linux/Mac

echo ""
echo "=================================================="
echo "     TelegrammBolt Monitor"
echo "=================================================="
echo ""
echo "Запуск интерактивной консоли мониторинга..."
echo ""

# Активация виртуального окружения
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "[!] Виртуальное окружение не найдено!"
    echo "Установите зависимости: pip install -r requirements.txt"
    exit 1
fi

# Проверка psutil
python -c "import psutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "[!] Модуль psutil не установлен"
    echo "Установка psutil..."
    pip install psutil
    echo ""
fi

# Запуск монитора
python monitor.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[!] Ошибка запуска монитора"
    read -p "Нажмите Enter для выхода..."
fi
