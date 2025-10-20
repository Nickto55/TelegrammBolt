#!/bin/bash

# Quick SSL Setup for TelegrammBolt
# Настройка HTTPS с самоподписанным сертификатом

set -e

echo "=========================================="
echo "TelegrammBolt - Quick SSL Setup"
echo "=========================================="
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Этот скрипт требует прав root"
    echo "Запустите: sudo bash setup-ssl-quick.sh"
    exit 1
fi

# Определение IP-адреса сервера
SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')
echo "[1/6] Определен IP сервера: $SERVER_IP"

# Создание директории для SSL сертификатов
echo "[2/6] Создание директории для SSL..."
mkdir -p /etc/nginx/ssl
chmod 700 /etc/nginx/ssl

# Генерация самоподписанного SSL сертификата
echo "[3/6] Генерация самоподписанного SSL сертификата..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/telegrambot.key \
    -out /etc/nginx/ssl/telegrambot.crt \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=TelegrammBolt/CN=$SERVER_IP" \
    2>/dev/null

chmod 600 /etc/nginx/ssl/telegrambot.key
chmod 644 /etc/nginx/ssl/telegrambot.crt

echo "   SSL сертификат создан для IP: $SERVER_IP"

# Обновление конфига nginx с правильным IP
echo "[4/6] Настройка nginx конфигурации..."
NGINX_CONF="/etc/nginx/sites-available/telegrambot"
NGINX_ENABLED="/etc/nginx/sites-enabled/telegrambot"

# Копируем конфиг из проекта
cp /opt/telegrambot/nginx-ssl.conf $NGINX_CONF

# Заменяем IP в конфиге
sed -i "s/87\.120\.166\.213/$SERVER_IP/g" $NGINX_CONF

# Активируем конфиг
ln -sf $NGINX_CONF $NGINX_ENABLED

# Удаляем дефолтный конфиг nginx
rm -f /etc/nginx/sites-enabled/default

echo "   Конфиг nginx настроен для $SERVER_IP"

# Проверка конфигурации nginx
echo "[5/6] Проверка конфигурации nginx..."
if nginx -t 2>/dev/null; then
    echo "   Конфигурация nginx корректна"
else
    echo "ERROR: Ошибка в конфигурации nginx!"
    nginx -t
    exit 1
fi

# Перезапуск nginx
echo "[6/6] Перезапуск nginx..."
systemctl restart nginx
systemctl enable nginx

# Проверка статуса
if systemctl is-active --quiet nginx; then
    echo "   Nginx успешно запущен"
else
    echo "ERROR: Nginx не запустился!"
    systemctl status nginx
    exit 1
fi

echo ""
echo "=========================================="
echo "HTTPS успешно настроен!"
echo "=========================================="
echo ""
echo "Ваш сайт доступен по адресам:"
echo ""
echo "  HTTPS: https://$SERVER_IP/"
echo "  HTTP:  http://$SERVER_IP/ (автоматически перенаправляется на HTTPS)"
echo ""
echo "ВАЖНО:"
echo "  - Используется самоподписанный SSL сертификат"
echo "  - Браузер покажет предупреждение о безопасности"
echo "  - Нажмите 'Дополнительно' -> 'Продолжить на сайт'"
echo ""
echo "Проверка портов:"
netstat -tulpn | grep -E ':(80|443|5000)' || echo "  Порты не найдены (возможно, не установлен net-tools)"
echo ""
echo "Логи nginx:"
echo "  sudo tail -f /var/log/nginx/telegrambot_error.log"
echo ""
echo "Готово!"
