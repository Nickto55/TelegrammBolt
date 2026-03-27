# Quick Start Guide - TelegrammBolt Mobile

Быстрый старт для создания и запуска мобильного приложения.

## 🚀 Быстрый старт (5 минут)

### Шаг 1: Подготовка окружения

```bash
# Убедитесь что установлены:
# - Node.js 16+ (https://nodejs.org/)
# - npm или yarn

# Установите Expo CLI
npm install -g expo-cli
```

### Шаг 2: Клонирование и стновка

```bash
cd TelegrammBolt/mobile

# Копируем .env файл
cp .env.example .env

# Редактируем .env и устанавливаем API_BASE_URL
# Для локальной разработки:
# API_BASE_URL=http://localhost:5000

# Устанавливаем зависимости
npm install
```

### Шаг 3: Запуск

```bash
# Запускаем dev server
npm start

# В терминале появится меню:
# Нажмите 'i' для iOS
# Нажмите 'a' для Android
# Нажмите 'w' для Web
# Нажмите 'j' для запуска debugger
```

## 📱 Запуск для каждой платформы

### iOS (Mac только)

```bash
# Требует Xcode
npm run ios

# Или запустить с конкретным симулятором
npx react-native run-ios --simulator="iPhone 14"
```

### Android

```bash
# Требует Android Studio и эмулятор
npm run android

# Или с запуском эмулятора
npm run android -- --emulator
```

### Web (для тестирования UI)

```bash
npm run web
```

## 🔧 Конфигурация

### .env файл

```env
# URL вашего Flask сервера
API_BASE_URL=http://localhost:5000

# Timeout для API запросов (ms)
API_TIMEOUT=30000

# Включить push notifications (future)
ENABLE_PUSH_NOTIFICATIONS=false

# Использовать AsyncStorage для токенов
SECURE_STORAGE_ENABLED=true
```

## 📚 Главные экраны приложения

### Аутентификация
- **LoginScreen** - Вход в аккаунт
- **RegisterScreen** - Регистрация новый аккаунт
- **LinkTelegramScreen** - Привязка Telegram аккаунта с QR кодом

### Основные функции
- **DashboardScreen** - Главная страница с статистикой
- **DSEListScreen** - Список записей DSE с поиском
- **DSEDetailScreen** - Деталь конкретной записи
- **ChatScreen** - Сообщения и чаты
- **ProfileScreen** - Профиль пользователя
- **CreateDSEScreen** - Создание новой DSE записи

## 🔌 Интеграция с бэкэндом

### Требуемые API endpoints

Убедитесь что на вашем Flask сервере реализованы:

```python
# Authentication
@app.route('/api/auth/login', methods=['POST'])
@app.route('/api/auth/register', methods=['POST'])
@app.route('/api/auth/profile', methods=['GET'])

# DSE
@app.route('/api/dse/list', methods=['GET'])
@app.route('/api/dse/<int:id>', methods=['GET'])
@app.route('/api/dse/create', methods=['POST'])

# Chat
@app.route('/api/chat/list', methods=['GET'])
@app.route('/api/chat/<int:id>/messages', methods=['GET'])

# Invites
@app.route('/api/invites/list', methods=['GET'])
@app.route('/api/invites/create', methods=['POST'])
```

### Формат ответов

```json
{
  "success": true,
  "data": {},
  "message": "Optional message"
}
```

### CORS Configuration

```python
from flask_cors import CORS

# В web/web_app.py
CORS(app)
```

## 🛠️ Частые операции

### Очистить кеш

```bash
npm start -- --clear
```

### Пересбороть зависимости

```bash
rm -rf node_modules
npm install
```

### Включить логирование

```bash
# В App.js или любом файле
import { LogBox } from 'react-native';
LogBox.ignoreLogs(['Warning: ...']);
```

### Просмотреть логи

```bash
# iOS
npx react-native log-ios

# Android
npx react-native log-android
```

## 🐛 Troubleshooting

### Ошибка: "Cannot find module"

```bash
# Очистить и переустановить
rm -rf node_modules package-lock.json
npm install
npm start -- --clear
```

### Ошибка: "Network Error" при установке зависимостей

```bash
# Используйте другой реестр
npm config set registry https://registry.npmmirror.com
npm install
```

### API не доступна

- Проверьте что сервер запущен: `http://localhost:5000`
- Проверьте URL в `.env` файле
- Проверьте CORS настройки на сервере
- Используйте `API_BASE_URL=http://10.0.2.2:5000` для Android эмулятора

### Проблема с камерой на iOS

```bash
# Обновите info.plist
expo prebuild
```

## 📦 Сборка для рилиза

### iOS TestFlight

```bash
# Требует Apple Developer Account
eas build --platform ios
eas submit --platform ios
```

### Android Google Play

```bash
# Требует Google Developer Account
eas build --platform android --release
eas submit --platform android
```

## 📖 Документация

- [README.md](./README.md) - Обзор проекта
- [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) - Интеграция с бэкэндом
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Архитектура приложения
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Разработка и тестирование

## 🏗️ Структура проекта

```
mobile/
├── src/
│   ├── screens/          # Экраны приложения
│   │   ├── auth/        # Экраны входа
│   │   └── main/        # Основные экраны
│   ├── navigation/       # Навигация
│   ├── services/         # API сервис
│   ├── store/           # Zustand хранилище
│   ├── components/      # Компоненты
│   ├── utils/           # Утилиты
│   ├── hooks/           # Custom hooks
│   └── config/          # Конфигурация
├── assets/              # Изображения
├── App.js              # Главная компонента
├── app.json            # Expo конфигурация
├── package.json        # Зависимости
└── .env                # Переменные окружения
```

## 🎨 Customization

### Изменить цвета

Отредактируйте `src/config/app.config.js`:

```javascript
UI: {
  PRIMARY_COLOR: '#000080',     // Основной цвет
  SECONDARY_COLOR: '#2196f3',   // Вторичный
  ERROR_COLOR: '#f44336',       // Ошибка
  // ...
}
```

### Добавить новый экран

1. Создайте файл в `src/screens/`
2. Экспортируйте компоненту
3. Добавьте в `RootNavigator.js`

### Добавить API endpoint

1. Добавьте метод в `src/services/apiService.js`
2. Используйте в соответствующем store

## 💬 Поддержка

- Проверьте документацию выше
- Посмотрите комментарии в исходном коде
- Используйте React Native Debugger
- Проверьте логи консоли

## 🎯 Следующие шаги

```bash
# 1. Запустить приложение
npm start

# 2. Выбрать платформу (i/a/w)

# 3. Протестировать функции:
#    - Логин/Регистрация
#    - Просмотр DSE
#    - Создание записи
#    - Отправка сообщения

# 4. Для развертывания:
eas build --platform ios --platform android
```

Готово! 🎉
