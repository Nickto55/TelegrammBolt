# 🐳 Диагностика проблемы ERR_EMPTY_RESPONSE в Docker

## 🔍 Проблема
**Сайт 87.120.166.213 не отправил данных (ERR_EMPTY_RESPONSE)**

Это означает, что браузер не получает ответ от сервера. Возможные причины:

---

## ✅ Шаг 1: Проверка Docker контейнера

Подключитесь к серверу через SSH и выполните:

```bash
# Проверить запущен ли контейнер
docker ps -a

# Если контейнер не запущен, запустить его
docker start <container_name>

# Проверить логи контейнера
docker logs <container_name> --tail 100

# Проверить логи в реальном времени
docker logs -f <container_name>
```

**Что искать в логах:**
- ✅ `Running on http://0.0.0.0:5000` - приложение запущено
- ❌ `Error` или `Exception` - есть ошибки
- ❌ `Address already in use` - порт занят

---

## ✅ Шаг 2: Проверка портов Docker

```bash
# Проверить проброс портов
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Должно быть что-то вроде:
# 0.0.0.0:5000->5000/tcp

# Если порт не пробросен, пересоздать контейнер
docker run -d -p 5000:5000 --name telegrambot your_image
```

**Частая ошибка:** Контейнер слушает только localhost (127.0.0.1:5000), а не 0.0.0.0:5000

**Исправление в web_app.py:**
```python
# ❌ НЕПРАВИЛЬНО для Docker:
app.run(host='127.0.0.1', port=5000)

# ✅ ПРАВИЛЬНО для Docker:
app.run(host='0.0.0.0', port=5000)
```

---

## ✅ Шаг 3: Проверка firewall на сервере

```bash
# Проверить открыт ли порт 5000
sudo ufw status

# Если порт закрыт, открыть его
sudo ufw allow 5000/tcp

# Или для конкретного порта (например 80/443)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Проверить что порт слушается
sudo netstat -tulpn | grep 5000
# или
sudo ss -tulpn | grep 5000
```

**Ожидаемый результат:**
```
tcp        0      0 0.0.0.0:5000            0.0.0.0:*               LISTEN      12345/docker-proxy
```

---

## ✅ Шаг 4: Проверка Nginx (если используется)

```bash
# Проверить статус Nginx
sudo systemctl status nginx

# Если не запущен
sudo systemctl start nginx

# Проверить конфигурацию
sudo nginx -t

# Проверить логи ошибок
sudo tail -f /var/log/nginx/error.log

# Перезапустить Nginx
sudo systemctl restart nginx
```

**Проверка конфигурации Nginx для proxy:**

```nginx
server {
    listen 80;
    server_name 87.120.166.213;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## ✅ Шаг 5: Проверка доступности изнутри сервера

```bash
# Зайти внутрь контейнера
docker exec -it <container_name> /bin/bash

# ИЛИ протестировать с хоста
curl http://localhost:5000
curl http://127.0.0.1:5000

# Проверить извне (с другой машины)
curl http://87.120.166.213:5000
```

**Ожидаемый результат:**
- Должен вернуться HTML код или перенаправление

**Если curl работает, но браузер - нет:**
- Проблема может быть в CORS или заголовках безопасности

---

## ✅ Шаг 6: Проверка конфигурации Docker

### Если используется docker-compose.yml:

```yaml
version: '3.8'
services:
  web:
    image: python:3.12-slim
    container_name: telegrambot_web
    working_dir: /app
    volumes:
      - ./:/app
    ports:
      - "5000:5000"  # ← ВАЖНО: проброс портов
    command: >
      sh -c "pip install -r requirements.txt &&
             python web_app.py"
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
```

**Перезапуск:**
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f web
```

### Если используется Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Копировать зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копировать приложение
COPY . .

# Открыть порт
EXPOSE 5000

# Запустить приложение (ВАЖНО: host=0.0.0.0)
CMD ["python", "web_app.py"]
```

**Сборка и запуск:**
```bash
docker build -t telegrambot .
docker run -d -p 5000:5000 --name telegrambot telegrambot
```

---

## ✅ Шаг 7: Использование Gunicorn (РЕКОМЕНДУЕТСЯ)

Flask встроенный сервер не подходит для production!

```bash
# Войти в контейнер
docker exec -it <container_name> /bin/bash

# Установить gunicorn
pip install gunicorn

# Запустить с gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

**Обновить Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .

# Установить зависимости включая gunicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 5000

# Использовать Gunicorn вместо Flask dev server
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_app:app"]
```

---

## ✅ Шаг 8: Проверка виртуальной сети Docker

```bash
# Проверить сети Docker
docker network ls

# Проверить какие контейнеры подключены
docker network inspect bridge

# Если проблема с сетью, создать новую
docker network create telegrambot_network

# Подключить контейнер к сети
docker network connect telegrambot_network <container_name>
```

---

## ✅ Шаг 9: Полная диагностика (скрипт)

Создайте файл `docker-diagnostic.sh` на сервере:

```bash
#!/bin/bash

echo "=== 🐳 Docker Контейнеры ==="
docker ps -a

echo -e "\n=== 📊 Использование портов ==="
docker ps --format "table {{.Names}}\t{{.Ports}}"

echo -e "\n=== 🔍 Процессы слушающие порты ==="
sudo netstat -tulpn | grep -E ":(5000|80|443)"

echo -e "\n=== 🔥 Firewall статус ==="
sudo ufw status

echo -e "\n=== 📝 Логи контейнера (последние 50 строк) ==="
docker logs telegrambot_web --tail 50 2>&1

echo -e "\n=== 🌐 Проверка доступности изнутри ==="
curl -I http://localhost:5000 2>&1

echo -e "\n=== 🔍 Nginx статус ==="
sudo systemctl status nginx --no-pager

echo -e "\n=== 📋 Nginx конфигурация ==="
sudo nginx -t 2>&1

echo -e "\n=== 📄 Docker Compose файлы ==="
find . -name "docker-compose.yml" -o -name "Dockerfile" 2>/dev/null

echo -e "\n=== ✅ Диагностика завершена ==="
```

**Запустить:**
```bash
chmod +x docker-diagnostic.sh
./docker-diagnostic.sh > diagnostic-report.txt
cat diagnostic-report.txt
```

---

## 🔧 Быстрые исправления

### Проблема 1: Контейнер не запускается

```bash
# Проверить последние логи
docker logs <container_name>

# Перезапустить контейнер
docker restart <container_name>

# Если не помогло - пересоздать
docker stop <container_name>
docker rm <container_name>
docker run -d -p 5000:5000 --name telegrambot your_image
```

### Проблема 2: Порт занят

```bash
# Найти процесс занимающий порт
sudo lsof -i :5000

# Убить процесс
sudo kill -9 <PID>

# Или использовать другой порт
docker run -d -p 8080:5000 --name telegrambot your_image
```

### Проблема 3: Приложение падает сразу после запуска

```bash
# Запустить контейнер в интерактивном режиме
docker run -it --rm -p 5000:5000 your_image /bin/bash

# Внутри контейнера попробовать запустить вручную
python web_app.py
```

### Проблема 4: Nginx не может достучаться до контейнера

```bash
# Проверить что контейнер в сети host или bridge
docker inspect <container_name> | grep NetworkMode

# Если нужно, запустить с network host
docker run -d --network host --name telegrambot your_image
```

---

## 📊 Проверка правильности настройки

### ✅ Контрольный список:

- [ ] Docker контейнер запущен: `docker ps`
- [ ] Порт пробросен правильно: `docker ps` показывает `0.0.0.0:5000->5000/tcp`
- [ ] Приложение слушает 0.0.0.0:5000 (не 127.0.0.1)
- [ ] Firewall разрешает порт: `sudo ufw allow 5000`
- [ ] Порт не занят другим процессом: `sudo lsof -i :5000`
- [ ] Нет ошибок в логах: `docker logs <container_name>`
- [ ] curl localhost:5000 работает с сервера
- [ ] curl http://87.120.166.213:5000 работает извне
- [ ] Nginx настроен правильно (если используется)
- [ ] Используется Gunicorn, а не Flask dev server

---

## 🚀 Рекомендуемая конфигурация для Production

### docker-compose.yml:

```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: telegrambot_web
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./bot_data.json:/app/bot_data.json
      - ./users_data.json:/app/users_data.json
      - ./photos:/app/photos
    command: gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 web_app:app

  nginx:
    image: nginx:alpine
    container_name: telegrambot_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./static:/opt/telegrambot/static
    depends_on:
      - web
```

### nginx.conf:

```nginx
server {
    listen 80;
    server_name 87.120.166.213;

    client_max_body_size 16M;

    location /static/ {
        alias /opt/telegrambot/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://web:5000;  # ← web - имя сервиса в docker-compose
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## 💡 Команды для быстрого реагирования

```bash
# Перезапустить все
docker-compose restart

# Посмотреть логи в реальном времени
docker-compose logs -f

# Полная переустановка
docker-compose down
docker-compose up -d --build

# Зайти внутрь контейнера
docker exec -it telegrambot_web /bin/bash

# Проверить порты
docker port telegrambot_web

# Проверить переменные окружения
docker exec telegrambot_web env
```

---

## 📞 Если ничего не помогает

1. **Соберите диагностическую информацию:**
```bash
./docker-diagnostic.sh > report.txt
```

2. **Проверьте базовую доступность:**
```bash
# На сервере
curl -v http://localhost:5000

# С другой машины
curl -v http://87.120.166.213:5000
```

3. **Проверьте логи на ошибки Python:**
```bash
docker logs telegrambot_web 2>&1 | grep -i error
```

4. **Временно отключите Nginx (если используется):**
```bash
sudo systemctl stop nginx
# И попробуйте напрямую http://87.120.166.213:5000
```

---

## ✅ После исправления

После того как проблема решена, не забудьте:

1. Настроить автозапуск:
```bash
docker update --restart=unless-stopped telegrambot_web
```

2. Настроить логирование:
```bash
docker-compose logs -f > /var/log/telegrambot.log 2>&1 &
```

3. Добавить мониторинг:
```bash
# Простой healthcheck
curl -f http://localhost:5000 || docker restart telegrambot_web
```

---

**Успехов! 🚀**
