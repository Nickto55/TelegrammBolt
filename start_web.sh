#!/bin/bash
#
# Запуск веб-интерфейса TelegrammBolt
#

# Переход в директорию проекта
cd "$(dirname "$0")"

# Создание директории для логов
mkdir -p logs

# Активация виртуального окружения
source .venv/bin/activate

# Проверка что gunicorn установлен
if ! command -v gunicorn &> /dev/null; then
    echo "[ERROR] gunicorn не установлен. Устанавливаю..."
    pip install gunicorn
fi

# Запуск через gunicorn для production
echo "[INFO] Запуск веб-интерфейса..."
echo "[INFO] URL: http://0.0.0.0:5000"

# 4 воркера, порт 5000
exec gunicorn -w 4 \
    -b 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile logs/web_access.log \
    --error-logfile logs/web_error.log \
    --log-level info \
    web.web_app:app
