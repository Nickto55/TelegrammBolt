# API Endpoints Reference для мобильного приложения

## Обзор

Мобильное приложение TelegrammBolt использует REST API для связи с Flask бэкендом. 

**Base URL:** `http(s)://your-server:5000`

## Authentication

### Login
```
POST /api/auth/login
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "password": "password"
}

Response:
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "role": "user"
  }
}
```

### Register
```
POST /api/auth/register
Content-Type: application/json

Request:
{
  "email": "newuser@example.com",
  "password": "password",
  "full_name": "Jane Doe"
}

Response:
{
  "success": true,
  "message": "User registered successfully. Please log in."
}
```

### Get Profile
```
GET /api/auth/profile
Authorization: Bearer {token}

Response:
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "role": "user",
    "telegram_id": 123456789
  }
}
```

### Link Telegram Account
```
POST /api/auth/link-telegram
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "linking_code": "ABC123"  // 6-digit code from Telegram bot
}

Response:
{
  "success": true,
  "message": "Telegram account linked successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "telegram_id": 123456789
  }
}
```

## DSE Records

### Get DSE List
```
GET /api/dse/list?page=1&limit=20
Authorization: Bearer {token}

Response:
{
  "success": true,
  "dse_records": [
    {
      "id": 1,
      "name": "DSE Record 1",
      "description": "Description text",
      "status": "in_progress",
      "user_id": 1,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    ...
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

### Get DSE Detail
```
GET /api/dse/{id}
Authorization: Bearer {token}

Response:
{
  "success": true,
  "id": 1,
  "name": "DSE Record 1",
  "description": "Full description",
  "status": "in_progress",
  "user_id": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "additional_info": "Extra details"
}
```

### Create DSE
```
POST /api/dse/create
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "name": "New DSE Record",
  "description": "Record description",
  "status": "pending"
}

Response:
{
  "success": true,
  "message": "DSE record created successfully",
  "dse_record": {
    "id": 1,
    "name": "New DSE Record",
    "description": "Record description",
    "status": "pending",
    "user_id": 1,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Update DSE
```
PUT /api/dse/{id}
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "name": "Updated Name",
  "description": "Updated description",
  "status": "completed"
}

Response:
{
  "success": true,
  "message": "DSE record updated successfully",
  "dse_record": { ... }
}
```

### Search DSE
```
GET /api/dse/search?q=search_query
Authorization: Bearer {token}

Response:
{
  "success": true,
  "results": [
    {
      "id": 1,
      "name": "Matching Record",
      "description": "...",
      "status": "...",
      "created_at": "..."
    },
    ...
  ]
}
```

## Chat & Messages

### Get Chat List
```
GET /api/chat/list
Authorization: Bearer {token}

Response:
{
  "success": true,
  "chats": [
    {
      "id": 1,
      "name": "John Doe",
      "last_message": "Hi there!",
      "last_message_at": "2024-01-15T10:30:00Z",
      "unread_count": 0
    },
    ...
  ]
}
```

### Get Chat Messages
```
GET /api/chat/{chat_id}/messages?page=1
Authorization: Bearer {token}

Response:
{
  "success": true,
  "messages": [
    {
      "id": 1,
      "chat_id": 1,
      "user_id": 1,
      "text": "Message content",
      "created_at": "2024-01-15T10:30:00Z",
      "sender": {
        "id": 1,
        "full_name": "John Doe"
      }
    },
    ...
  ],
  "page": 1,
  "total": 100
}
```

### Send Message
```
POST /api/chat/{chat_id}/message
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "text": "Hello, this is a message!"
}

Response:
{
  "success": true,
  "message": {
    "id": 1,
    "chat_id": 1,
    "user_id": 1,
    "text": "Hello, this is a message!",
    "created_at": "2024-01-15T10:30:00Z",
    "sender": {
      "id": 1,
      "full_name": "John Doe"
    }
  }
}
```

## User Profile

### Update Profile
```
POST /api/user/profile/update
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "full_name": "John Doe Updated",
  "phone": "+1234567890"
}

Response:
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe Updated",
    "phone": "+1234567890"
  }
}
```

### Change Password
```
POST /api/user/change-password
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "old_password": "current_password",
  "new_password": "new_password"
}

Response:
{
  "success": true,
  "message": "Password changed successfully"
}
```

## Invites

### Get Active Invites
```
GET /api/invites/list
Authorization: Bearer {token}

Response:
{
  "success": true,
  "invites": [
    {
      "id": 1,
      "code": "ABC123DEF456",
      "created_at": "2024-01-15T10:30:00Z",
      "expires_at": "2024-01-22T10:30:00Z",
      "uses": 0,
      "max_uses": 5,
      "used": false
    },
    ...
  ]
}
```

### Create Invite
```
POST /api/invites/create
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "expiry_days": 7,
  "max_uses": 5
}

Response:
{
  "success": true,
  "invite": {
    "id": 1,
    "code": "ABC123DEF456",
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-22T10:30:00Z",
    "qr_code": "data:image/png;base64,..."
  }
}
```

## Error Responses

### Standard Error Response
```
HTTP 400 / 401 / 500

{
  "success": false,
  "error": "Error message",
  "code": 400
}
```

### Common Http Status Codes
- `200` - OK
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Authentication Headers

Все защищенные endpoints требуют заголовок:

```
Authorization: Bearer {token}
```

Token получается при логине и хранится в AsyncStorage.

## CORS Configuration (Required)

На Flask сервере нужно включить CORS для мобильного приложения:

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

## Rate Limiting (Recommended)

Рекомендуется установить rate limiting:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

## Testing API Endpoints

### With curl

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Get DSE list (with token)
curl -X GET http://localhost:5000/api/dse/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### With Postman

1. Set up Environment Variables:
   - `base_url`: `http://localhost:5000`
   - `token`: (set dynamically after login)

2. Use Pre-request Script to set token:
```javascript
var loginResponse = pm.response.json();
pm.environment.set("token", loginResponse.token);
```

3. Use in Headers:
```
Authorization: Bearer {{token}}
```

## WebSocket Support (Optional Future Upgrade)

For real-time messaging, consider adding WebSocket support:

```python
from flask_socketio import SocketIO, emit, join_room

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('send_message')
def handle_message(data):
    emit('new_message', data, room=data['chat_id'])
```

---

Полная интеграция мобильного приложения с этими endpoints обеспечит полнофункциональное приложение для Android и iOS.
