#  Запуск мобильного приложения TelegrammBolt

## Общая картина

Теперь у вас есть полное мобильное приложение для Android и iOS. Вот как всё это запустить и интегрировать с существующим сервером.

## Что было создано в папке `/mobile`

### Основная структура
```
mobile/
├── src/                 # Исходный код
├── assets/              # Изображения (нужно подготовить)
├── App.js              # Главная компонента
├── package.json        # Зависимости проекта
├── app.json            # Конфигурация Expo
└── README.md           # Документация
```

### Экраны (Screens)
- **Auth**: LoginScreen, RegisterScreen, LinkTelegramScreen
- **Main**: DashboardScreen, DSEListScreen, DSEDetailScreen, ChatScreen, ProfileScreen, CreateDSEScreen

### State Management (Zustand)
- `authStore.js` - Управление аутентификацией
- `dseStore.js` - Управление DSE записями  
- `chatStore.js` - Управление чатами

### Сервисы
- `apiService.js` - REST API клиент с токен-авторизацией

## 🔧 Инструкции по запуску

### Вариант 1: Быстрый старт (5 минут)

```bash
# 1. Перейти в папку мобильного приложения
cd /home/nickolay/gitCode/TelegrammBolt/mobile

# 2. Скопировать пример .env
cp .env.example .env

# 3. Отредактировать .env 
# Если бэкэнд на локальном компе:
# API_BASE_URL=http://localhost:5000
# Если на удаленном сервере:
# API_BASE_URL=https://your-domain.com

# 4. Установить зависимости
npm install

# 5. Запустить приложение
npm start

# 6. Выбрать платформу:
#    Нажмите 'i' для iOS
#    Нажмите 'a' для Android
#    Нажмите 'w' для Web тестирования
```

### Вариант 2: Запуск конкретной платформы

#### iOS (требует macOS с Xcode)
```bash
cd mobile
npm install
npm run ios
```

#### Android (требует Android Studio)
```bash
cd mobile
npm install
npm run android
```

#### Web (для быстрого тестирования UI)
```bash
cd mobile
npm install
npm run web
```

## 🔌 Интеграция с Flask бэкэндом

### Шаг 1: Проверить наличие API endpoints

В `web/web_app.py` должны быть эти endpoints. Если их нет, добавьте:

```python
@app.route('/api/auth/login', methods=['POST'])
@app.route('/api/auth/register', methods=['POST'])
@app.route('/api/auth/profile', methods=['GET'])
@app.route('/api/dse/list', methods=['GET'])
@app.route('/api/dse/<int:id>', methods=['GET'])
@app.route('/api/dse/create', methods=['POST'])
@app.route('/api/chat/list', methods=['GET'])
@app.route('/api/user/profile/update', methods=['POST'])
# ... и остальные (см. API_ENDPOINTS.md)
```

### Шаг 2: Включить CORS

Отредактируйте `web/web_app.py` и добавьте в начало:

```python
from flask_cors import CORS

# После создания Flask приложения
app = Flask(__name__, ...)
CORS(app)  # Включить CORS для забех источников
```

### Шаг 3: Настроить .env для мобильного приложения

```bash
cd mobile
nano .env  # или используйте VS Code

# Установить правильный URL бэкэнда
API_BASE_URL=http://localhost:5000  # для локальной разработки
```

### Шаг 4: Запустить оба сервера

#### Терминал 1 - Запустить Flask бэкэнд
```bash
cd /home/nickolay/gitCode/TelegrammBolt
python3 web/web_app.py

# Или если у вас есть скрипт
./manage.sh  # выбрать запуск веб-сервера
```

#### Терминал 2 - Запустить мобильное приложение
```bash
cd /home/nickolay/gitCode/TelegrammBolt/mobile
npm start

# Выбрать платформу и начать тестирование
```

## 📱 Тестирование функций

### 1. Аутентификация
- [ ] Откройте приложение
- [ ] Нажмите "Register"
- [ ] Заполните форму регистрации
- [ ] Нажмите "Создать аккаунт"
- [ ] Вернитесь и войдите с новыми учетными данными

### 2. Просмотор DSE записей
- [ ] После входа перейдите на вкладку "DSE List"
- [ ] Должны отобразиться записи из БД
- [ ] Нажмите на запись для просмотра деталей

### 3. Создание записи
- [ ] Нажмите кнопку "+ Создать DSE"
- [ ] Заполните название и описание
- [ ] Нажмите "Создать"
- [ ] Проверьте что запись появилась в списке

### 4. Профиль
- [ ] Перейдите на вкладку "Profile"
- [ ] Посмотрите данные пользователя
- [ ] Нажмите "Выход" для выхода

## Помощь и документация

### Документы в папке `/mobile`

1. **[QUICKSTART.md](./mobile/QUICKSTART.md)** - Быстрый старт
2. **[README.md](./mobile/README.md)** - Полная инструкция
3. **[ARCHITECTURE.md](./mobile/ARCHITECTURE.md)** - Архитектура приложения
4. **[INTEGRATION_GUIDE.md](./mobile/INTEGRATION_GUIDE.md)** - Подробная интеграция
5. **[DEVELOPMENT.md](./mobile/DEVELOPMENT.md)** - Разработка и troubleshooting

### Основной документ для интеграции

**[API_ENDPOINTS.md](./API_ENDPOINTS.md)** - Все API endpoints с примерами

##  Решение проблем

### Проблема: "Cannot find module"
```bash
cd mobile
rm -rf node_modules package-lock.json
npm install
```

### Проблема: "Network error" при подключении к API
- Убедитесь что Flask сервер запущен: `http://localhost:5000`
- Проверьте API_BASE_URL в `.env`
- Включите CORS на бэкэнде
- Для Android эмулятора используйте: `API_BASE_URL=http://10.0.2.2:5000`

### Проблема: "CORS policy" error
```python
# Добавьте в web/web_app.py
from flask_cors import CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### Проблема: iOS/Android не ловит API
- Проверьте что устройство подключено к той же сети
- Используйте IP адрес вместо localhost: `http://192.168.1.100:5000`
- Отключите firewall

## Следующие шаги

### Готово к production?

Запакуйте приложение для распределения:

#### iOS (TestFlight)
```bash
cd mobile
eas build --platform ios --auto-submit
eas submit --platform ios
```

#### Android (Google Play)
```bash
cd mobile
eas build --platform android --release
eas submit --platform android
```

### Хотите добавить новые функции?

1. Создайте новый экран в `src/screens/`
2. Добавьте API метод в `src/services/apiService.js`
3. Используйте в соответствующем store (authStore, dseStore и т.д.)
4. Добавьте маршрут в `src/navigation/RootNavigator.js`

### Нужно изменить дизайн?

1. Отредактируйте цвета в `src/config/app.config.js`
2. Измените стили в каждом компоненте (StyleSheet)
3. Добавьте новые компоненты в `src/components/`

##  Checklist для полной интеграции

- [ ] Установлены Node.js и Expo CLI
- [ ] Зависимости установлены (`npm install`)
- [ ] Файл `.env` настроен правильно
- [ ] Flask сервер запущен и доступен
- [ ] CORS включен на бэкэнде
- [ ] Требуемые API endpoints реализованы
- [ ] Приложение запускается без ошибок
- [ ] Аутентификация работает
- [ ] DSE записи загружаются
- [ ] Сообщения отправляются/получаются
- [ ] Профиль показывает данные пользователя

##  Контакты и поддержка

Если возникают вопросы:

1. Проверьте документацию (QUICKSTART.md, README.md и т.д.)
2. Посмотрите на примеры кода в `src/`
3. Используйте React Native Debugger
4. Проверьте логи консоли

##  Итоговая структура проекта

```
TelegrammBolt/
├── web/              # Flask веб-приложение
├── bot/              # Telegram бот
├── config/           # Конфигурация
├── mobile/           # 🆕 React Native мобильное приложение
│   ├── src/
│   │   ├── screens/
│   │   ├── navigation/
│   │   ├── services/
│   │   ├── store/
│   │   ├── utils/
│   │   └── config/
│   └── ... (остальные файлы)
├── API_ENDPOINTS.md  # 🆕 Документация API для мобильной интеграции
└── README.md         # Основная документация
```

---

**Поздравляем!**  

У вас теперь есть:
-  Полнофункциональное мобильное приложение для iOS и Android
-  Интегрированное с существующим Flask бэкэндом
-  Готовое к тестированию и развертыванию

**Начните с:**
```bash
cd mobile
npm install
npm start
```

Выбирайте платформу и начинайте разработку! 🚀
