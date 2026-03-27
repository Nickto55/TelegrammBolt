# 📦 Сборка APK для Android

## 🎯 Два способа сборки APK

### Способ 1: Локальная сборка (требует Android SDK)

#### Шаг 1: Установите Android SDK на сервере

```bash
# На сервере (требуются права root)
ssh root@144.31.14.132
cd /root/TelegrammBolt/mobile
sudo chmod +x setup-android-sdk.sh
sudo ./setup-android-sdk.sh
```

Скрипт автоматически:
- ✅ Установит Java JDK 17
- ✅ Скачает Android Command Line Tools
- ✅ Установит Android SDK Platform 34
- ✅ Установит Build Tools 34.0.0
- ✅ Настроит переменные окружения

**Время установки: 5-10 минут**

#### Шаг 2: Применить переменные окружения

```bash
source /root/.bashrc
```

#### Шаг 3: Собрать APK

```bash
cd /root/TelegrammBolt/mobile
npm run android-build
```

Это выполнит:
1. `expo prebuild --platform android` - генерация нативного Android проекта
2. `cd android && ./gradlew assembleRelease` - сборка release APK

**Время сборки: 10-20 минут (первая сборка), 3-5 минут (последующие)**

#### Шаг 4: Найти готовый APK

APK файл будет здесь:
```
/root/TelegrammBolt/mobile/android/app/build/outputs/apk/release/app-release.apk
```

Скачать на локальный компьютер:
```bash
scp root@144.31.14.132:/root/TelegrammBolt/mobile/android/app/build/outputs/apk/release/app-release.apk ~/Downloads/
```

---

### Способ 2: EAS Build (облачная сборка, проще)

#### Шаг 1: Установите EAS CLI

```bash
npm install -g eas-cli
```

#### Шаг 2: Авторизуйтесь в Expo

```bash
eas login
# Введите email и пароль от Expo аккаунта
# Если нет аккаунта: https://expo.dev/signup
```

#### Шаг 3: Настройте проект (в первый раз)

```bash
cd /root/TelegrammBolt/mobile
eas build:configure
```

#### Шаг 4: Соберите APK

```bash
eas build --platform android --profile preview
```

**Время сборки: 10-15 минут**

После завершения вы получите ссылку для скачивания APK.

---

## 🔧 Дополнительные команды

### Debug сборка (быстрее, для тестирования)

```bash
npm run android-build-debug
```

APK будет здесь:
```
android/app/build/outputs/apk/debug/app-debug.apk
```

### Очистка проекта (если возникли ошибки)

```bash
npm run android-clean
rm -rf android/
```

Затем снова:
```bash
npm run android-build
```

---

## ⚙️ Конфигурация APK

### Изменить название приложения

Отредактируйте [`app.json`](mobile/app.json):

```json
{
  "expo": {
    "name": "TelegrammBolt",  // <-- Название приложения
    "slug": "telegrambolt"
  }
}
```

### Изменить package name

```json
{
  "expo": {
    "android": {
      "package": "com.telegrambolt.mobile"  // <-- Уникальный ID
    }
  }
}
```

### Добавить иконку приложения

Замените файлы:
- `mobile/assets/icon.png` (1024x1024)
- `mobile/assets/adaptive-icon.png` (1024x1024)
- `mobile/assets/splash.png` (1242x2436)

### Подписать APK (для Google Play)

Создайте keystore:

```bash
cd android/app
keytool -genkeypair -v -storetype PKCS12 \
  -keystore telegrambolt.keystore \
  -alias telegrambolt \
  -keyalg RSA -keysize 2048 -validity 10000
```

Отредактируйте `android/gradle.properties`:

```properties
MYAPP_UPLOAD_STORE_FILE=telegrambolt.keystore
MYAPP_UPLOAD_KEY_ALIAS=telegrambolt
MYAPP_UPLOAD_STORE_PASSWORD=your_password
MYAPP_UPLOAD_KEY_PASSWORD=your_password
```

Отредактируйте `android/app/build.gradle`:

```gradle
android {
    signingConfigs {
        release {
            storeFile file(MYAPP_UPLOAD_STORE_FILE)
            storePassword MYAPP_UPLOAD_STORE_PASSWORD
            keyAlias MYAPP_UPLOAD_KEY_ALIAS
            keyPassword MYAPP_UPLOAD_KEY_PASSWORD
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}
```

---

## 🐛 Решение проблем

### Ошибка: "ANDROID_HOME not set"

```bash
# Убедитесь, что переменные применены
echo $ANDROID_HOME
# Должно вывести: /opt/android-sdk

# Если пусто, примените снова
source /root/.bashrc
```

### Ошибка: "SDK location not found"

Создайте файл `mobile/android/local.properties`:

```properties
sdk.dir=/opt/android-sdk
```

### Ошибка: "Gradle build failed"

Очистите и пересоберите:

```bash
cd mobile
rm -rf android/
npm run android-build
```

### Ошибка: "Out of memory"

Увеличьте память для Gradle в `android/gradle.properties`:

```properties
org.gradle.jvmargs=-Xmx4096m -XX:MaxMetaspaceSize=512m
```

### Ошибка: "Execution failed for task ':app:mergeDexRelease'"

Включите multidex в `android/app/build.gradle`:

```gradle
android {
    defaultConfig {
        multiDexEnabled true
    }
}
```

---

## 📋 Сравнение способов

| Характеристика | Локальная сборка | EAS Build |
|----------------|------------------|-----------|
| Требования | Android SDK, Java | Только npm |
| Установка | 15-20 минут | 2 минуты |
| Первая сборка | 15-20 минут | 10-15 минут |
| Последующие | 3-5 минут | 10-15 минут |
| Интернет | Только первый раз | Каждый раз |
| Стоимость | Бесплатно | Бесплатно (лимит) |
| Контроль | Полный | Ограниченный |

---

## 🚀 Быстрый старт (рекомендуется для начала)

**Для первого раза используйте EAS Build:**

```bash
# 1. Установите EAS CLI
npm install -g eas-cli

# 2. Войдите в аккаунт
eas login

# 3. Соберите APK
cd /root/TelegrammBolt/mobile
eas build --platform android --profile preview

# 4. Скачайте APK по ссылке из консоли
```

**После тестирования можно перейти на локальную сборку для полного контроля.**

---

## 📱 Установка APK на телефон

### Способ 1: Через USB

```bash
# Подключите телефон через USB
# Включите "Отладка по USB" на телефоне

adb install app-release.apk
```

### Способ 2: Через файл

1. Скопируйте APK на телефон
2. Откройте APK на телефоне
3. Разрешите "Установку из неизвестных источников"
4. Установите приложение

### Способ 3: Через QR код

Загрузите APK на сервер и создайте QR код со ссылкой:

```bash
# Разместите APK в web/static/
cp app-release.apk /root/TelegrammBolt/web/static/

# Создайте ссылку
echo "https://your-domain.com/static/app-release.apk"
```

---

## ✅ Checklist перед сборкой

- [ ] `.env` настроен с правильным `API_BASE_URL`
- [ ] `app.json` имеет правильное название и package
- [ ] Иконки добавлены в `assets/`
- [ ] Версия обновлена в `package.json` и `app.json`
- [ ] Протестировано в dev режиме (`npm start`)
- [ ] Все зависимости установлены (`npm install`)

---

## 🎯 Следующие шаги после сборки

1. **Тестирование**: Установите APK на реальное устройство и протестируйте все функции
2. **Оптимизация**: Проверьте размер APK и оптимизируйте если нужно
3. **Подпись**: Подпишите APK для публикации в Google Play
4. **Публикация**: Загрузите в Google Play Console

---

**Готово!** 🎉 Теперь у вас есть полная инструкция по сборке APK двумя способами.
