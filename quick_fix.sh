#!/bin/bash
# Быстрое исправление ошибок заявок на сервере Ubuntu

echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║     ИСПРАВЛЕНИЕ ОШИБОК ЗАЯВОК - BOLT WEB APP         ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Проверка, что мы в правильной директории
if [ ! -f "web_app.py" ]; then
    echo "❌ Ошибка: web_app.py не найден!"
    echo "Перейдите в директорию проекта:"
    echo "  cd /root/TelegrammBolt"
    exit 1
fi

echo "🔍 Шаг 1: Диагностика системы..."
python3 server_check.py
echo ""

read -p "Продолжить с перезапуском? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Шаг 2: Перезапуск веб-сервера..."
    bash restart_web.sh
    echo ""
    
    echo "✅ Готово!"
    echo ""
    echo "📋 Следующие шаги:"
    echo "  1. Откройте заявку в браузере"
    echo "  2. Смотрите логи: tail -f web.log"
    echo "  3. Если ошибка - запустите: python3 diagnose_dse.py"
else
    echo "Отменено."
fi
