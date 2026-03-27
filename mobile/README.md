# TelegrammBolt Mobile App

Кроссплатформенное мобильное приложение для Android и iOS, разработанное на React Native с использованием Expo.

## Функции

- **Аутентификация**: Вход, регистрация и привязка Telegram аккаунта
- **Управление записями DSE**: Просмотр, создание и редактирование записей
- **Сообщения**: Спивающиеся чаты с другими пользователями
- **Профиль**: Управление данными профиля и настройками
- **QR код сканер**: Быстрая привязка Telegram аккаунта

## Требования

- Node.js 16+ и npm/yarn
- Expo CLI: `npm install -g expo-cli`
- iOS: Xcode (для программирования на iOS)
- Android: Android Studio (для программирования на Android)

## Установка

### 1. Клонирование репозитория

```bash
cd TelegrammBolt
cd mobile
```

### 2. Установка зависимостей

```bash
npm install
# или
yarn install
```

### 3. Конфигурация

Создайте `.env` файл на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и установите правильный URL API:

```
API_BASE_URL=http://your-server.com:5000
```

### 4. Запуск приложения

#### Для разработки

```bash
npm start
```

Затем выберите:
- `i` - запустить на iOS симуляторе
- `a` - запустить на Android эмуляторе
- `w` - запустить в веб-браузере

#### Для Android

```bash
npm run android
```

#### Для iOS

```bash
npm run ios
```

## Структура проекта

```
mobile/
├── src/
│   ├── screens/
│   │   ├── auth/           # Экраны аутентификации
│   │   └── main/           # Основные экраны приложения
│   ├── navigation/          # Навигация и роутинг
│   ├── services/            # API сервисы
│   ├── store/              # State management (Zustand)
│   ├── components/         # Переиспользуемые компоненты
│   └── utils/              # Утилиты и помощники
├── assets/                  # Изображения и иконки
├── App.js                   # Главный файл приложения
├── app.json                 # Конфигурация Expo
├── package.json             # Зависимости проекта
└── babel.config.js          # Конфигурация Babel
```

## API Интеграция

Приложение использует тот же REST API что и веб-версия. Все API запросы идут через `apiService.js`.

### Основные endpoints

- `POST /api/auth/login` - Вход
- `POST /api/auth/register` - Регистрация
- `GET /api/auth/profile` - Получить профиль
- `GET /api/dse/list` - Список DSE
- `GET /api/dse/{id}` - Деталь DSE
- `POST /api/dse/create` - Создать DSE
- `GET /api/chat/list` - Список чатов
- `GET /api/chat/{id}/messages` - Сообщения чата

## Сборка и развертывание

### Сборка для iOS

```bash
npm run deploy
```

Или с использованием EAS:

```bash
eas build --platform ios
```

### Сборка для Android

```bash
npm run android
```

Для APK файла:

```bash
eas build --platform android
```

## Технологический стек

- **React Native** - UI фреймворк
- **Expo** - Платформа для разработки
- **React Navigation** - Навигация
- **Zustand** - State management
- **Axios** - HTTP клиент
- **AsyncStorage** - Локальное хранилище

## Разработка

### Добавление новых экранов

1. Создайте новый компонент в `src/screens/`
2. Добавьте экран в навигацию в `RootNavigator.js`
3. Используйте состояние из соответствующего store

### Добавление новых API endpoints

1. Добавьте метод в `src/services/apiService.js`
2. Используйте метод в соответствующем стене store

### Изменение стилей

Используйте встроенные стили StyleSheet. Основной цвет приложения: `#000080`

## Лиц лицензией и поддержка

Часть проекта TelegrammBolt. Для поддержки обратитесь к основному репозиторию.
