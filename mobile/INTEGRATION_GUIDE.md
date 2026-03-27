# Интеграция мобильного приложения с веб-бэкэндом

Документация по интеграции мобильного приложения с существующим Flask бэкэндом.

## Обзор

Мобильное приложение использует тот же REST API что и веб-версия. Все запросы направлены на Flask сервер по адресу, указанному в `API_BASE_URL`.

## Конфигурация API

### 1. Установка URL сервера

Отредактируйте файл `.env` в корне папки `mobile/`:

```env
API_BASE_URL=http://your-server:5000
```

Для локальной разработки:
```env
API_BASE_URL=http://localhost:5000
```

Для продакшена:
```env
API_BASE_URL=https://your-domain.com
```

### 2. CORS Configuration

Убедитесь, что на бэкэнде включен CORS для мобильного приложения:

```python
# web/web_app.py
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],  # В production установить конкретные домены
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### 3. Аутентификация

Мобильное приложение использует токен-базированную аутентификацию:

1. При логине получить токен и сохранить в AsyncStorage
2. Все последующие запросы содержат токен в заголовке `Authorization: Bearer {token}`
3. При истечении токена (ошибка 401) - перенаправить на экран входа

```javascript
// src/services/apiService.js
this.client.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## API Endpoints

### Аутентификация

```
POST /api/auth/login
POST /api/auth/register
GET /api/auth/profile
POST /api/auth/link-telegram
```

### DSE Records

```
GET /api/dse/list?page=1&limit=20
GET /api/dse/{id}
POST /api/dse/create
PUT /api/dse/{id}
GET /api/dse/search?q=query
GET /api/dse/{id}/export-pdf
```

### Chats

```
GET /api/chat/list
GET /api/chat/{id}/messages?page=1
POST /api/chat/{id}/message
```

### User

```
POST /api/user/profile/update
POST /api/user/change-password
GET /api/user/invites
POST /api/invites/create
POST /api/invites/use
```

## Требуемые изменения в бэкэнде

### 1. API Endpoints для мобильного приложения

Убедитесь, что следующие endpoints существуют в `web/web_app.py`:

```python
# Authentication
@app.route('/api/auth/login', methods=['POST'])
@app.route('/api/auth/register', methods=['POST'])
@app.route('/api/auth/profile', methods=['GET'])
@app.route('/api/auth/link-telegram', methods=['POST'])

# DSE
@app.route('/api/dse/list', methods=['GET'])
@app.route('/api/dse/<int:dse_id>', methods=['GET'])
@app.route('/api/dse/create', methods=['POST'])
@app.route('/api/dse/<int:dse_id>', methods=['PUT'])
@app.route('/api/dse/search', methods=['GET'])

# Chat
@app.route('/api/chat/list', methods=['GET'])
@app.route('/api/chat/<int:chat_id>/messages', methods=['GET'])
@app.route('/api/chat/<int:chat_id>/message', methods=['POST'])

# User
@app.route('/api/user/profile/update', methods=['POST'])
@app.route('/api/user/change-password', methods=['POST'])

# Invites
@app.route('/api/invites/list', methods=['GET'])
@app.route('/api/invites/create', methods=['POST'])
@app.route('/api/invites/use', methods=['POST'])
```

### 2. JSON Response Format

Все endpoints должны возвращать JSON с следующей структурой:

```json
{
  "success": true,
  "data": {},
  "message": "Optional message"
}
```

Ошибки:

```json
{
  "success": false,
  "error": "Error message",
  "code": 400
}
```

### 3. Аутентификация по токену

Реализуйте JWT токены или другую систему токенов:

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            # Verify token
            user_id = verify_token(token)
        except:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/auth/profile')
@require_auth
def get_profile():
    # ...
```

## Структура Store (State Management)

Приложение использует Zustand для управления состоянием:

- `authStore` - Аутентификация и данные пользователя
- `dseStore` - Данные DSE записей
- `chatStore` - Данные чатов

Добавляйте новые store для нового функционала:

```javascript
// src/store/newStore.js
import create from 'zustand';
import apiService from '../services/apiService';

export const useNewStore = create((set, get) => ({
  data: [],
  isLoading: false,
  error: null,

  fetchData: async () => {
    try {
      set({ isLoading: true });
      const response = await apiService.getNewData();
      set({ data: response, isLoading: false });
    } catch (error) {
      set({ error: error.message, isLoading: false });
    }
  },
}));
```

## Testing API Integration

### Тестирование с помощью curl

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Get DSE list
curl -X GET http://localhost:5000/api/dse/list \
  -H "Authorization: Bearer {token}"
```

### Тестирование с помощью Postman

1. Создайте collection в Postman
2. Установите переменную `{{api_url}}` на `http://localhost:5000`
3. Сохраняйте токен как переменную после логина:

```javascript
// Tests tab
if (pm.response.code === 200) {
  pm.environment.set("token", pm.response.json().token);
}
```

## Мигрирование данных

Для миграции пользовательских данных между веб- и мобильными приложениями:

1. Используйте одну базу данных для обоих приложений
2. Ищите `web_user_id` для связи веб и Telegram аккаунтов
3. Реализуйте синхронизацию через API

## Troubleshooting

### Ошибка: "Network Error"

- Проверьте, запущен ли сервер
- Убедитесь, что URL в `.env` правильный
- Проверьте CORS настройки

### Ошибка: "401 Unauthorized"

- Проверьте, что токен сохранился в AsyncStorage
- Убедитесь, что токен передается в заголовке Authorization
- Проверьте время истечения токена на сервере

### CORS ошибка

Добавьте в `web_app.py`:

```python
from flask_cors import CORS
CORS(app)
```

## Security Best Practices

1. **HTTPS в production** - Всегда используйте HTTPS
2. **Token Security** - Сохраняйте токены в защищенном хранилище
3. **API Keys** - Не заливайте API ключи в код
4. **Validation** - Валидируйте все входные данные на сервере
5. **Rate Limiting** - Реализуйте ограничение частоты запросов

## Performance Optimization

1. **Caching** - Кешируйте данные локально где возможно
2. **Pagination** - Используйте пагинацию для больших наборов данных
3. **Compression** - Включите gzip компрессию на сервере
4. **Lazy Loading** - Загружайте данные по мере необходимости

## Future Enhancements

- [ ] WebSocket поддержка для real-time сообщений
- [ ] Push notifications
- [ ] Offline mode с синхронизацией
- [ ] Image optimization и caching
- [ ] Advanced search и filters
