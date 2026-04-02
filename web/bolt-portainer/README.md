# BOLT - Docker Portainer Deployment

Полная структура Docker-проекта для развёртывания через Portainer.

## Структура проекта

```
bolt-portainer/
├── docker-compose.yml          # Основная конфигурация Docker Compose
├── install.sh                  # Интерактивный установщик
├── manage.sh                   # Скрипт управления стеком
├── .env.example                # Пример конфигурации окружения
├── README.md                   # Документация
│
├── backend/                    # Backend сервис (Node.js/Express)
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── package.json
│   └── src/
│       ├── index.js            # Точка входа
│       ├── config/
│       │   ├── database.js     # Конфигурация PostgreSQL
│       │   ├── init-schema.sql # SQL схема
│       │   └── seed.js         # Начальные данные
│       ├── middleware/
│       │   └── auth.js         # JWT middleware
│       └── routes/
│           ├── auth.js         # Аутентификация
│           ├── dse.js          # DSE управление
│           ├── users.js        # Пользователи
│           ├── messages.js     # Чат
│           ├── invites.js      # Приглашения
│           └── logs.js         # Логи
│
├── frontend/                   # Frontend сервис (React + Nginx)
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── nginx.conf.template
│   └── package.json
│
├── nginx/                      # Nginx конфигурация (опционально)
│   └── nginx.conf.template
│
└── init-scripts/               # SQL скрипты инициализации
    └── 01-init-schema.sql
```

## Быстрый старт

### 1. Установка

```bash
# Интерактивный режим
./install.sh

# Или с аргументами
./install.sh \
  --db-password "secure_password" \
  --backend-port 3001 \
  --frontend-port 80 \
  --nginx-port 80
```

### 2. Управление

```bash
# Запуск
./manage.sh start

# Остановка
./manage.sh stop

# Перезапуск
./manage.sh restart

# Статус
./manage.sh status

# Логи
./manage.sh logs
./manage.sh logs backend

# Бэкап базы данных
./manage.sh backup

# Восстановление
./manage.sh restore ./backups/backup_20240101_120000.sql
```

## API Endpoints

### Аутентификация
- `POST /api/auth/login` - Вход
- `GET /api/auth/me` - Текущий пользователь
- `PUT /api/auth/password` - Смена пароля

### DSE
- `GET /api/dse` - Список DSE
- `GET /api/dse/:id` - Получить DSE
- `POST /api/dse` - Создать DSE
- `PUT /api/dse/:id` - Обновить DSE
- `DELETE /api/dse/:id` - Удалить DSE

### Пользователи
- `GET /api/users` - Список пользователей
- `GET /api/users/:id` - Получить пользователя
- `POST /api/users` - Создать пользователя
- `PUT /api/users/:id` - Обновить пользователя
- `DELETE /api/users/:id` - Удалить пользователя

### Сообщения (Чат)
- `GET /api/messages` - История сообщений
- `POST /api/messages` - Отправить сообщение
- `DELETE /api/messages/:id` - Удалить сообщение

### Приглашения
- `GET /api/invites` - Список приглашений
- `POST /api/invites` - Создать приглашение
- `GET /api/invites/validate/:token` - Проверить токен
- `POST /api/invites/use/:token` - Использовать приглашение
- `DELETE /api/invites/:id` - Удалить приглашение

### Логи
- `GET /api/logs` - Системные логи
- `GET /api/logs/stats` - Статистика логов
- `DELETE /api/logs` - Очистить старые логи

## WebSocket

WebSocket доступен по пути `/socket.io/` для real-time чата.

## Health Checks

- Backend: `GET /health`
- Frontend/Nginx: `GET /health`
- PostgreSQL: встроенный healthcheck через `pg_isready`

## Безопасность

- JWT аутентификация
- Пароли хешируются с bcrypt
- SQL-инъекции защищены через параметризованные запросы
- CORS настроен
- Security headers в Nginx

## Учётные данные по умолчанию

После первого запуска создаются следующие пользователи:

| Username | Password    | Role     |
|----------|-------------|----------|
| admin    | admin123    | admin    |
| manager  | manager123  | manager  |
| operator | operator123 | operator |

**Важно:** Смените пароли после первого входа!

## Переменные окружения

| Переменная    | Описание                    | По умолчанию     |
|---------------|-----------------------------|------------------|
| DB_HOST       | Хост базы данных            | postgres         |
| DB_PORT       | Порт базы данных            | 5432             |
| DB_NAME       | Имя базы данных             | bolt_db          |
| DB_USER       | Пользователь БД             | bolt_user        |
| DB_PASSWORD   | Пароль БД                   | -                |
| BACKEND_PORT  | Порт backend                | 3001             |
| FRONTEND_PORT | Порт frontend               | 80               |
| JWT_SECRET    | Секретный ключ JWT          | bolt-secret-key  |
| NODE_ENV      | Окружение Node.js           | production       |

## Развёртывание в Portainer

1. Скопируйте все файлы проекта на сервер
2. Запустите `./install.sh` для создания `.env`
3. В Portainer создайте новый Stack
4. Загрузите `docker-compose.yml`
5. Укажите переменные окружения из `.env`
6. Deploy the stack

## Лицензия

MIT
