# Mobileная архитектура TelegrammBolt

## Архитектурный обзор

```
┌──────────────────────────────────────────────┐
│         React Native (iOS & Android)         │
├──────────────────────────────────────────────┤
│                  App Container               │
│  ┌────────────────────────────────────────┐  │
│  │    Navigation (React Navigation)       │  │
│  │  ┌──────────────────────────────────┐  │  │
│  │  │  Stack / Tab Navigators          │  │  │
│  │  │  - Auth Stack                    │  │  │
│  │  │  - Main Stack                    │  │  │
│  │  └──────────────────────────────────┘  │  │
│  └────────────────────────────────────────┘  │
├──────────────────────────────────────────────┤
│            Screens / Components              │
│  - LoginScreen, RegisterScreen               │
│  - DashboardScreen, DSEListScreen            │
│  - ChatScreen, ProfileScreen                 │
│  - Reusable components (Toast, etc)          │
├──────────────────────────────────────────────┤
│        State Management (Zustand)            │
│  - authStore                                 │
│  - dseStore                                  │
│  - chatStore                                 │
├──────────────────────────────────────────────┤
│           Services Layer                     │
│  - apiService (API calls)                    │
│  - StorageService (AsyncStorage)             │
│  - Others...                                 │
├──────────────────────────────────────────────┤
│        Utilities & Helpers                   │
│  - dateUtils, validation, errorHandler       │
│  - Custom hooks                              │
├──────────────────────────────────────────────┤
│                                              │
│  ⬇️  HTTP Requests (axios)                   │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │    Flask Backend (web_app.py)       │    │
│  │    - REST API Endpoints              │    │
│  │    - Authentication & WebSockets     │    │
│  │    - Database Operations             │    │
│  └─────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

## Данные потока

### 1. Аутентификация

```
User Input (Email/Password)
           ↓
    LoginScreen
           ↓
   authStore.login()
           ↓
 apiService.login()
           ↓
 axios POST /api/auth/login
           ↓
  Flask Backend (验证)
           ↓
   Получить token + user data
           ↓
Сохранить в AsyncStorage
           ↓
Обновить authStore
           ↓
Перейти на Dashboard
```

### 2. Загрузка данных

```
Component Mount
           ↓
   useEffect()
           ↓
  useDSEStore.getDSEList()
           ↓
 apiService.getDSEList()
           ↓
axios GET /api/dse/list?page=X
           ↓
  Flask returns JSON
           ↓
 Update Zustand state
           ↓
 Re-render component with data
```

### 3. Отправка сообщения

```
User types message
           ↓
 Press Send button
           ↓
useChatStore.sendMessage()
           ↓
apiService.sendMessage()
           ↓
axios POST /api/chat/{id}/message
           ↓
  Flask saves message
           ↓
Returns message object
           ↓
Add to local messages array
           ↓
Update UI
```

## Компоненты и их ответственность

### Navigation Components
- `RootNavigator.js` - Главная навигация (Auth vs Main)
- Stack Navigator - Навигация между экранами
- Tab Navigator - Нижнее меню навигации

### Screens
Организованы по функциям:
- `screens/auth/` - Экраны входа/регистрации
- `screens/main/` - Основные экраны приложения

### State Management (Stores)
- `authStore` - Состояние аутентификации
- `dseStore` - CRUD операции с DSE
- `chatStore` - Управление чатами

### Services
- `apiService` - Все HTTP запросы через axios
- `StorageService` - AsyncStorage операции

### Utils
- `dateUtils` - Форматирование дат
- `validation` - Валидация данных
- `errorHandler` - Обработка ошибок

## Лучшие практики

### 1. Структура компонента

```javascript
// Imports
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';

// Component
const MyComponent = ({ navigation, route }) => {
  // State
  const [data, setData] = useState(null);
  
  // Store
  const { fetchData } = useMyStore();
  
  // Effects
  useEffect(() => {
    fetchData();
  }, []);
  
  // Handlers
  const handlePress = () => {};
  
  // Render
  return (
    <View style={styles.container}>
      <Text>{data}</Text>
    </View>
  );
};

// Styles
const styles = StyleSheet.create({
  container: { flex: 1 },
});

export default MyComponent;
```

### 2. API Error Handling

```javascript
try {
  await someApiCall();
} catch (error) {
  const message = formatErrorMessage(error);
  Alert.alert('Error', message);
}
```

### 3. Loading States

```javascript
{isLoading ? (
  <ActivityIndicator />
) : data ? (
  <DataComponent data={data} />
) : (
  <EmptyComponent />
)}
```

## Интеграция с бэкэндом

### API Endpoints используемые:

```
Authentication:
GET    /api/auth/profile
POST   /api/auth/login
POST   /api/auth/register

DSE:
GET    /api/dse/list
GET    /api/dse/{id}
POST   /api/dse/create
PUT    /api/dse/{id}

Chat:
GET    /api/chat/list
POST   /api/chat/{id}/message
```

### Требуемые ответы сервера:

```json
{
  "success": true,
  "data": {},
  "message": "Optional"
}
```

## Performance Optimizations

1. **Memoization** - Использование React.memo для компонентов
2. **Lazy Loading** - Загрузка данных по странам
3. **Caching** - Локальное кеширование часто используемых данных
4. **FlatList** - Оптимизированные списки
5. **Image Optimization** - Сжатие и кеширование изображений

## Security Considerations

1. **Token Storage** - Использование AsyncStorage для токенов
2. **HTTPS** - Всегда использовать в production
3. **API Validation** - Валидировать на сервере
4. **Sensitive Data** - Не логировать/хранить пароли
5. **Network Security** - Certificate pinning (если требуется)

## Debugging и Testing

### React Native Debugger
```bash
npm install -g react-native-debugger
react-native-debugger
```

### Console Logs
```javascript
console.log('debug', data);
console.error('error', error);
```

### Network Inspection
- DevTools в React Native Debugger
- Network tab в Chrome DevTools

## Развертывание

### TestFlight (iOS)
```bash
eas build --platform ios
eas submit --platform ios
```

### Google Play (Android)
```bash
eas build --platform android
eas submit --platform android
```

## Resources

- [React Native Docs](https://reactnative.dev/)
- [React Navigation Docs](https://reactnavigation.org/)
- [Zustand Docs](https://github.com/pmndrs/zustand)
- [Expo Docs](https://docs.expo.dev/)
