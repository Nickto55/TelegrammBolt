#!/bin/bash
# TelegrammBolt - Минимальная установка для Debian/Ubuntu
# Этот скрипт использует только базовые пакеты

set -e

echo "🚀 TelegrammBolt - Минимальная установка"
echo "============================================================"

# Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get install -y python3 python3-pip python3-venv git curl wget build-essential

# Создание пользователя
echo "👤 Создание пользователя telegrambot..."
if ! id "telegrambot" &>/dev/null; then
    useradd --system --shell /bin/bash --home /opt/telegrambot --create-home telegrambot
fi

# Клонирование репозитория
echo "📥 Клонирование репозитория..."
if [ -d "/opt/telegrambot/.git" ]; then
    cd /opt/telegrambot
    sudo -u telegrambot git pull
else
    rm -rf /opt/telegrambot
    git clone https://github.com/Nickto55/TelegrammBolt.git /opt/telegrambot
fi

chown -R telegrambot:telegrambot /opt/telegrambot

# Установка Python окружения
echo "🐍 Установка Python окружения..."
cd /opt/telegrambot
sudo -u telegrambot python3 -m venv .venv
sudo -u telegrambot .venv/bin/pip install --upgrade pip
sudo -u telegrambot .venv/bin/pip install -r requirements.txt

# Создание конфигурации
echo "⚙️ Создание конфигурации..."
if [ ! -f "ven_bot.json" ]; then
    sudo -u telegrambot bash -c 'cat > ven_bot.json << EOF
{
  "BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
  "ADMIN_IDS": ["YOUR_TELEGRAM_ID_HERE"]
}
EOF'
fi

if [ ! -f "smtp_config.json" ]; then
    sudo -u telegrambot bash -c 'cat > smtp_config.json << EOF
{
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": 587,
  "SMTP_USER": "your_email@gmail.com",
  "SMTP_PASSWORD": "your_app_password",
  "FROM_NAME": "TelegrammBolt"
}
EOF'
fi

# Установка службы (если systemd доступен)
echo "🔧 Установка службы..."
if command -v systemctl &> /dev/null; then
    cp /opt/telegrambot/telegrambot.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable telegrambot.service
    
    echo
    echo "============================================================"
    echo "✅ Установка завершена!"
    echo
    echo "📋 Следующие шаги:"
    echo "1. Настройте конфигурацию:"
    echo "   nano /opt/telegrambot/ven_bot.json"
    echo
    echo "2. Запустите бота:"
    echo "   systemctl start telegrambot"
    echo
    echo "3. Проверьте статус:"
    echo "   systemctl status telegrambot"
    echo
    echo "4. Просмотр логов:"
    echo "   journalctl -u telegrambot -f"
    echo "============================================================"
else
    echo "⚠️  systemd не обнаружен. Создание init.d скрипта..."
    
    cat > /etc/init.d/telegrambot << 'INITEOF'
#!/bin/sh
### BEGIN INIT INFO
# Provides:          telegrambot
# Required-Start:    $remote_fs $syslog $network
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: TelegrammBolt Telegram Bot
# Description:       Telegram bot for DSE management
### END INIT INFO

PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC="TelegrammBolt Telegram Bot"
NAME=telegrambot
DAEMON=/opt/telegrambot/.venv/bin/python
DAEMON_ARGS="/opt/telegrambot/bot.py"
PIDFILE=/var/run/$NAME.pid
SCRIPTNAME=/etc/init.d/$NAME
USER=telegrambot
WORKDIR=/opt/telegrambot

[ -x "$DAEMON" ] || exit 0

. /lib/lsb/init-functions

do_start()
{
    start-stop-daemon --start --quiet --pidfile $PIDFILE --chuid $USER \
        --background --make-pidfile --chdir $WORKDIR \
        --exec $DAEMON -- $DAEMON_ARGS \
        || return 2
}

do_stop()
{
    start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 --pidfile $PIDFILE
    RETVAL="$?"
    [ "$RETVAL" = 2 ] && return 2
    rm -f $PIDFILE
    return "$RETVAL"
}

case "$1" in
  start)
    log_daemon_msg "Starting $DESC" "$NAME"
    do_start
    case "$?" in
        0|1) log_end_msg 0 ;;
        2) log_end_msg 1 ;;
    esac
    ;;
  stop)
    log_daemon_msg "Stopping $DESC" "$NAME"
    do_stop
    case "$?" in
        0|1) log_end_msg 0 ;;
        2) log_end_msg 1 ;;
    esac
    ;;
  status)
    status_of_proc "$DAEMON" "$NAME" && exit 0 || exit $?
    ;;
  restart|force-reload)
    log_daemon_msg "Restarting $DESC" "$NAME"
    do_stop
    case "$?" in
      0|1)
        do_start
        case "$?" in
            0) log_end_msg 0 ;;
            1) log_end_msg 1 ;;
            *) log_end_msg 1 ;;
        esac
        ;;
      *)
        log_end_msg 1
        ;;
    esac
    ;;
  *)
    echo "Usage: $SCRIPTNAME {start|stop|status|restart|force-reload}" >&2
    exit 3
    ;;
esac

:
INITEOF

    chmod +x /etc/init.d/telegrambot
    
    if command -v update-rc.d &> /dev/null; then
        update-rc.d telegrambot defaults
    elif command -v chkconfig &> /dev/null; then
        chkconfig --add telegrambot
    fi
    
    echo
    echo "============================================================"
    echo "✅ Установка завершена!"
    echo
    echo "📋 Следующие шаги:"
    echo "1. Настройте конфигурацию:"
    echo "   nano /opt/telegrambot/ven_bot.json"
    echo
    echo "2. Запустите бота:"
    echo "   /etc/init.d/telegrambot start"
    echo "   или: service telegrambot start"
    echo
    echo "3. Проверьте статус:"
    echo "   /etc/init.d/telegrambot status"
    echo "   или: service telegrambot status"
    echo
    echo "4. Для ручного запуска:"
    echo "   cd /opt/telegrambot"
    echo "   sudo -u telegrambot .venv/bin/python bot.py"
    echo "============================================================"
fi
