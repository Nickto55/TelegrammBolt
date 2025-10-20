#!/bin/bash
# Быстрый рестарт веб-сервера BOLT

echo "🔄 Перезапуск веб-сервера BOLT..."
echo ""

# 1. Остановка текущих процессов
echo "1️⃣  Остановка процессов..."
pkill -f "web_app.py" 2>/dev/null
pkill -f "gunicorn.*web_app" 2>/dev/null
sleep 1

# 2. Проверка systemd сервиса
if systemctl list-unit-files | grep -q boltweb.service; then
    echo "2️⃣  Перезапуск systemd сервиса..."
    sudo systemctl restart boltweb
    sleep 2
    sudo systemctl status boltweb --no-pager -l | head -20
else
    echo "2️⃣  Systemd сервис не найден, запускаю напрямую..."
    cd /root/TelegrammBolt || cd ~/TelegrammBolt || cd .
    nohup python3 web_app.py > web.log 2>&1 &
    echo "   Сервер запущен в фоне"
fi

echo ""
echo "3️⃣  Проверка запуска..."
sleep 2

if pgrep -f "web_app.py|gunicorn.*web_app" > /dev/null; then
    echo "✅ Сервер запущен успешно!"
    echo ""
    echo "Процессы:"
    ps aux | grep -E "web_app|gunicorn" | grep -v grep
    echo ""
    echo "Порты:"
    netstat -tlnp 2>/dev/null | grep -E ":5000|:8000|:80" || ss -tlnp | grep -E ":5000|:8000|:80"
    echo ""
    echo "📋 Просмотр логов: tail -f web.log"
else
    echo "❌ Ошибка запуска!"
    echo "Проверьте логи: tail -50 web.log"
fi
