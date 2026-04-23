# BOLT - Инструкция по развёртыванию

## Архитектура системы

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│    Backend      │────▶│   PostgreSQL    │
│   (React)       │◄────│   (Node.js)     │◄────│   (Docker)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       Port: 5173              Port: 3001             Port: 5432
```

## Быстрый старт

### 1. Клонирование и подготовка

```bash
git clone https://github.com/Nickto55/TelegrammBolt.git
cd TelegrammBolt/web/
```

### 2. Настройка окружения

Скопируйте файл `.env.example` в `.env` и настройте переменные:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=bolt_db
DB_USER=bolt_user
DB_PASSWORD=your_secure_password

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
JWT_EXPIRES_IN=7d

# Backend Configuration
BACKEND_PORT=3001
NODE_ENV=production

# Frontend Configuration
FRONTEND_PORT=5173

# CORS
CORS_ORIGIN=http://<domain>
```

### 3. Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Полная очистка (включая данные БД)
docker-compose down -v
```

### 4. Доступ к приложению

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:3001/api
- **Health Check**: http://localhost:3001/health

### 5. Данные для входа

После первого запуска создаётся пользователь по умолчанию:

- **Логин**: `admin`
- **Пароль**: `admin123`

⚠️ **Важно**: Смените пароль после первого входа!

---

## Ручная установка (без Docker)

### Требования

- Node.js 18+
- PostgreSQL 14+
- npm или yarn

### 1. Установка базы данных

```bash
# Создание базы данных
sudo -u postgres psql -c "CREATE DATABASE bolt_db;"
sudo -u postgres psql -c "CREATE USER bolt_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE bolt_db TO bolt_user;"
```

### 2. Backend

```bash
cd bolt-backend

# Установка зависимостей
npm install

# Настройка окружения
cp .env.example .env
# Отредактируйте .env

# Запуск в режиме разработки
npm run dev

# Или сборка и запуск production
npm run build
npm start
```

### 3. Frontend

```bash
cd app

# Установка зависимостей
npm install

# Настройка окружения
echo "VITE_API_URL=http://localhost:3001/api" > .env.local

# Запуск в режиме разработки
npm run dev

# Сборка production
npm run build
```

---

## API Endpoints

### Аутентификация

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/auth/login` | Вход по логину/паролю |
| POST | `/api/auth/telegram` | Вход через Telegram |
| POST | `/api/auth/qr` | Вход по QR-коду |
| GET | `/api/auth/me` | Информация о текущем пользователе |
| GET | `/api/auth/permissions` | Права доступа |

### DSE (Детали)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/dse` | Список заявок |
| GET | `/api/dse/:id` | Детали заявки |
| POST | `/api/dse` | Создать заявку |
| PUT | `/api/dse/:id` | Обновить заявку |
| DELETE | `/api/dse/:id` | Скрыть заявку |
| POST | `/api/dse/:id/restore` | Восстановить заявку |
| GET | `/api/dse/stats` | Статистика |
| GET | `/api/dse/pending` | Заявки на проверку |

### Пользователи

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/users` | Список пользователей |
| POST | `/api/users` | Создать пользователя |
| PUT | `/api/users/:id` | Обновить пользователя |
| DELETE | `/api/users/:id` | Удалить пользователя |

### Сообщения (WebSocket + REST)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/messages` | История сообщений |
| POST | `/api/messages` | Отправить сообщение |
| GET | `/api/messages/unread-count` | Непрочитанные |

---

## WebSocket Events

Подключение: `ws://localhost:3001`

### Клиент → Сервер

| Event | Payload | Описание |
|-------|---------|----------|
| `join-room` | `{ roomId }` | Присоединиться к комнате |
| `leave-room` | `{ roomId }` | Покинуть комнату |
| `send-message` | `{ content, room_id }` | Отправить сообщение |
| `typing` | `{ room_id }` | Индикатор набора |

### Сервер → Клиент

| Event | Payload | Описание |
|-------|---------|----------|
| `new-message` | `{ content, sender_id, ... }` | Новое сообщение |
| `user-typing` | `{ user_id }` | Пользователь печатает |

---

## Роли и права доступа

| Роль | Описание | Права |
|------|----------|-------|
| `admin` | Администратор | Полный доступ |
| `responder` | Ответственный | Просмотр, редактирование, экспорт |
| `initiator` | Инициатор | Создание заявок, чат |
| `user` | Пользователь | Просмотр, чат |

---

## Резервное копирование

### База данных

```bash
# Создание бэкапа
docker exec bolt-postgres pg_dump -U bolt_user bolt_db > backup_$(date +%Y%m%d).sql

# Восстановление
cat backup_20240101.sql | docker exec -i bolt-postgres psql -U bolt_user bolt_db
```

### Автоматические бэкапы

Добавьте в crontab:

```bash
# Ежедневный бэкап в 2:00
0 2 * * * docker exec bolt-postgres pg_dump -U bolt_user bolt_db > /backups/bolt_$(date +\%Y\%m\%d).sql
```

---

## Мониторинг

### Health Check

```bash
curl http://localhost:3001/health
```

### Логи

```bash
# Backend logs
docker-compose logs -f backend

# Database logs
docker-compose logs -f postgres

# All logs
docker-compose logs -f
```

---

## Обновление

```bash
# Остановка
docker-compose down

# Получение обновлений
git pull

# Пересборка
docker-compose build --no-cache

# Запуск
docker-compose up -d
```

---

## Устранение неполадок

### Проблема: "Connection refused" к базе данных

```bash
# Проверка статуса PostgreSQL
docker-compose logs postgres

# Перезапуск
docker-compose restart postgres
```

### Проблема: JWT ошибки

```bash
# Проверка переменных окружения
docker-compose exec backend env | grep JWT
```

### Проблема: CORS ошибки

Проверьте `CORS_ORIGIN` в `.env` - должен совпадать с URL фронтенда.

---

## Производственное развёртывание

### 1. SSL/TLS (Let's Encrypt)

```yaml
# Добавьте в docker-compose.yml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certbot:/etc/letsencrypt
```

### 2. Environment Variables

```bash
# Production
NODE_ENV=production
JWT_SECRET=$(openssl rand -base64 32)
```

### 3. Security Headers

```nginx
# nginx.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

---

## Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs`
2. Проверьте health: `curl http://localhost:3001/health`
3. Создайте issue в репозитории

---
