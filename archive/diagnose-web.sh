#!/bin/bash

# Диагностика веб-сервера TelegrammBolt
# Проверяет почему HTTPS не работает

echo "=========================================="
echo "TelegrammBolt Web Diagnostics"
echo "=========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для проверки
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK]${NC} $1"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $1"
        return 1
    fi
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

info() {
    echo -e "[INFO] $1"
}

echo "=== 1. Проверка Nginx ==="
echo ""

# Проверка установки nginx
if command -v nginx &> /dev/null; then
    check "Nginx установлен"
    nginx -v 2>&1 | sed 's/^/  /'
else
    check "Nginx установлен"
    echo "  Установите: sudo apt install nginx"
    exit 1
fi

# Проверка запуска nginx
if systemctl is-active --quiet nginx; then
    check "Nginx запущен"
else
    check "Nginx запущен"
    echo "  Запустите: sudo systemctl start nginx"
fi

# Проверка автозапуска
if systemctl is-enabled --quiet nginx; then
    check "Nginx в автозапуске"
else
    warn "Nginx не в автозапуске"
    echo "  Добавьте: sudo systemctl enable nginx"
fi

echo ""
echo "=== 2. Проверка портов ==="
echo ""

# Проверка порта 80 (HTTP)
if netstat -tuln 2>/dev/null | grep -q ':80 '; then
    check "Порт 80 (HTTP) слушается"
    netstat -tuln | grep ':80 ' | sed 's/^/  /'
else
    check "Порт 80 (HTTP) слушается"
fi

# Проверка порта 443 (HTTPS)
if netstat -tuln 2>/dev/null | grep -q ':443 '; then
    check "Порт 443 (HTTPS) слушается"
    netstat -tuln | grep ':443 ' | sed 's/^/  /'
else
    check "Порт 443 (HTTPS) слушается"
    echo "  Nginx не слушает порт 443 - HTTPS не работает!"
fi

# Проверка порта 5000 (Flask)
if netstat -tuln 2>/dev/null | grep -q ':5000 '; then
    check "Порт 5000 (Flask) слушается"
    netstat -tuln | grep ':5000 ' | sed 's/^/  /'
else
    warn "Порт 5000 (Flask) не слушается"
    echo "  Flask не запущен или запущен на другом порту"
fi

echo ""
echo "=== 3. Проверка SSL сертификатов ==="
echo ""

# Проверка файла сертификата
if [ -f /etc/nginx/ssl/telegrambot.crt ]; then
    check "SSL сертификат существует"
    info "Срок действия:"
    openssl x509 -in /etc/nginx/ssl/telegrambot.crt -noout -dates 2>/dev/null | sed 's/^/  /'
else
    check "SSL сертификат существует"
    echo "  Файл не найден: /etc/nginx/ssl/telegrambot.crt"
    echo "  Создайте: sudo bash setup-ssl-quick.sh"
fi

# Проверка ключа
if [ -f /etc/nginx/ssl/telegrambot.key ]; then
    check "SSL ключ существует"
else
    check "SSL ключ существует"
    echo "  Файл не найден: /etc/nginx/ssl/telegrambot.key"
fi

echo ""
echo "=== 4. Проверка конфигурации Nginx ==="
echo ""

# Проверка наличия конфига
if [ -f /etc/nginx/sites-available/telegrambot ]; then
    check "Конфиг telegrambot существует"
else
    check "Конфиг telegrambot существует"
    echo "  Скопируйте: sudo cp /opt/telegrambot/nginx-ssl.conf /etc/nginx/sites-available/telegrambot"
fi

# Проверка активации конфига
if [ -L /etc/nginx/sites-enabled/telegrambot ]; then
    check "Конфиг telegrambot активирован"
else
    check "Конфиг telegrambot активирован"
    echo "  Активируйте: sudo ln -s /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/"
fi

# Проверка синтаксиса nginx
if sudo nginx -t 2>&1 | grep -q "successful"; then
    check "Синтаксис конфигурации nginx"
else
    check "Синтаксис конфигурации nginx"
    echo "  Ошибки конфигурации:"
    sudo nginx -t 2>&1 | sed 's/^/  /'
fi

echo ""
echo "=== 5. Проверка Flask приложения ==="
echo ""

# Проверка процесса Flask
if pgrep -f "python.*bot.py" > /dev/null; then
    check "Бот запущен (bot.py)"
    ps aux | grep "[p]ython.*bot.py" | sed 's/^/  /'
else
    warn "Бот не запущен"
    echo "  Запустите: python3 bot.py"
fi

# Проверка доступности Flask на localhost
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/login 2>/dev/null | grep -q "200\|302\|401"; then
    check "Flask доступен на localhost:5000"
else
    check "Flask доступен на localhost:5000"
    echo "  Flask не отвечает на http://127.0.0.1:5000"
fi

echo ""
echo "=== 6. Проверка firewall ==="
echo ""

# Проверка ufw
if command -v ufw &> /dev/null; then
    if ufw status 2>/dev/null | grep -q "Status: active"; then
        info "UFW активен"
        
        if ufw status | grep -q "80/tcp.*ALLOW"; then
            check "Порт 80 открыт в UFW"
        else
            check "Порт 80 открыт в UFW"
            echo "  Откройте: sudo ufw allow 80/tcp"
        fi
        
        if ufw status | grep -q "443/tcp.*ALLOW"; then
            check "Порт 443 открыт в UFW"
        else
            check "Порт 443 открыт в UFW"
            echo "  Откройте: sudo ufw allow 443/tcp"
        fi
    else
        info "UFW не активен"
    fi
else
    info "UFW не установлен"
fi

echo ""
echo "=== 7. Определение IP адреса ==="
echo ""

# Внешний IP
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s api.ipify.org 2>/dev/null || echo "Не удалось определить")
info "Внешний IP: $EXTERNAL_IP"

# Локальный IP
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "Не удалось определить")
info "Локальный IP: $LOCAL_IP"

echo ""
echo "=== 8. Тест доступности ==="
echo ""

# Проверка HTTP
info "Тест HTTP (порт 80)..."
if timeout 3 curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null | grep -q "301\|302\|200"; then
    check "HTTP localhost доступен"
else
    warn "HTTP localhost не отвечает"
fi

# Проверка HTTPS
info "Тест HTTPS (порт 443)..."
if timeout 3 curl -k -s -o /dev/null -w "%{http_code}" https://localhost/ 2>/dev/null | grep -q "200\|302"; then
    check "HTTPS localhost доступен"
else
    check "HTTPS localhost доступен"
    echo "  HTTPS не работает!"
fi

echo ""
echo "=== 9. Последние ошибки Nginx ==="
echo ""

if [ -f /var/log/nginx/telegrambot_error.log ]; then
    info "Последние 10 строк из error.log:"
    echo ""
    sudo tail -10 /var/log/nginx/telegrambot_error.log 2>/dev/null | sed 's/^/  /' || echo "  Нет ошибок"
else
    warn "Лог-файл не найден: /var/log/nginx/telegrambot_error.log"
fi

echo ""
echo "=========================================="
echo "Резюме"
echo "=========================================="
echo ""

# Определение основной проблемы
PROBLEM_FOUND=false

if ! systemctl is-active --quiet nginx; then
    echo -e "${RED}ПРОБЛЕМА:${NC} Nginx не запущен"
    echo "  Решение: sudo systemctl start nginx"
    PROBLEM_FOUND=true
fi

if ! [ -f /etc/nginx/ssl/telegrambot.crt ]; then
    echo -e "${RED}ПРОБЛЕМА:${NC} SSL сертификат не создан"
    echo "  Решение: sudo bash setup-ssl-quick.sh"
    PROBLEM_FOUND=true
fi

if ! [ -L /etc/nginx/sites-enabled/telegrambot ]; then
    echo -e "${RED}ПРОБЛЕМА:${NC} Конфиг nginx не активирован"
    echo "  Решение: sudo ln -s /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/"
    PROBLEM_FOUND=true
fi

if ! netstat -tuln 2>/dev/null | grep -q ':443 '; then
    echo -e "${RED}ПРОБЛЕМА:${NC} Порт 443 (HTTPS) не слушается"
    echo "  Возможные причины:"
    echo "    1. Nginx не запущен"
    echo "    2. Конфиг не активирован"
    echo "    3. Ошибка в конфигурации nginx"
    echo "  Решение: sudo bash setup-ssl-quick.sh"
    PROBLEM_FOUND=true
fi

if ! curl -s -o /dev/null http://127.0.0.1:5000/login 2>/dev/null; then
    echo -e "${YELLOW}ВНИМАНИЕ:${NC} Flask не запущен на порту 5000"
    echo "  Nginx не сможет проксировать запросы"
    echo "  Решение: python3 bot.py"
    PROBLEM_FOUND=true
fi

if [ "$PROBLEM_FOUND" = false ]; then
    echo -e "${GREEN}Все проверки пройдены!${NC}"
    echo ""
    echo "Ваш сайт должен быть доступен:"
    echo "  https://$EXTERNAL_IP/"
    echo ""
    echo "Если HTTPS всё равно не работает:"
    echo "  1. Проверьте firewall на облачном сервере (VPS панель управления)"
    echo "  2. Проверьте логи: sudo tail -f /var/log/nginx/telegrambot_error.log"
    echo "  3. Перезапустите nginx: sudo systemctl restart nginx"
fi

echo ""
echo "Готово!"
