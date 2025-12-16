#!/bin/bash
# Скрипт для обновления systemd сервиса веб-интерфейса
# Использует Gunicorn с eventlet для поддержки WebSocket

set -e

SERVICE_FILE="/etc/systemd/system/telegramweb.service"
WORK_DIR="/root/TelegrammBolt"
VENV_DIR="$WORK_DIR/venv"

echo "Обновление systemd сервиса для веб-терминала..."

# Создаем новый файл сервиса
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=TelegrammBolt Web Interface with Terminal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$WORK_DIR
Environment="PATH=$VENV_DIR/bin"

ExecStart=$VENV_DIR/bin/gunicorn \\
    --worker-class eventlet \\
    -w 1 \\
    --bind 0.0.0.0:5000 \\
    --access-logfile /var/log/telegramweb.log \\
    --error-logfile /var/log/telegramweb.log \\
    --log-level info \\
    web.web_app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Файл сервиса обновлен"

# Перезагружаем systemd
sudo systemctl daemon-reload
echo "✓ systemd daemon перезагружен"

# Перезапускаем сервис
sudo systemctl restart telegramweb
echo "✓ Сервис перезапущен"

# Проверяем статус
sudo systemctl status telegramweb --no-pager

echo ""
echo "Готово! Веб-терминал должен работать на порту 5000"
echo "Проверьте статус: sudo systemctl status telegramweb"
echo "Логи: sudo journalctl -u telegramweb -f"
