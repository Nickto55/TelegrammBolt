# 🤖 TelegrammBolt

> Telegram бот для управления заявками ДСЕ с веб-интерфейсом

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0-orange.svg)](CHANGELOG.md)

---

## 📋 О проекте

TelegrammBolt - это Telegram бот с веб-интерфейсом для управления заявками на диагностические средства электроники (ДСЕ).

### ✨ Возможности

- 🤖 **Telegram бот** - Удобное управление через мессенджер
- 🌐 **Веб-интерфейс** - Полнофункциональная панель управления
- 📊 **Отчеты** - Генерация Excel и PDF отчетов
- 👥 **Мультипользователь** - Система ролей и прав доступа
- 💬 **Чат** - Встроенная система сообщений
- 🔔 **Уведомления** - Автоматический мониторинг ДСЕ
- 📧 **Email** - Отправка отчетов по почте
- 🔐 **Безопасность** - Авторизация через Telegram

---

## 🚀 Быстрый старт

### Автоматическая установка с интерактивной настройкой (Ubuntu/Debian)

```bash
# Один скрипт для всего - установка + настройка
curl -fsSL https://raw.githubusercontent.com/Nickto55/TelegrammBolt/main/install.sh | sudo bash
```

**Что установщик спросит:**
- 🤖 Токен бота (от @BotFather)
- 👨‍💼 ID администратора (от @userinfobot)
- 📧 Email настройки (опционально)
- 🌐 Веб-интерфейс (вкл/выкл)
- 🔒 HTTPS (опционально)

**См. подробную инструкцию:** [QUICK_INSTALL.md](QUICK_INSTALL.md)

### Запуск

```bash
```bash
# Через службу
sudo systemctl start telegrambot

# Или вручную
cd /opt/telegrambot
python bot.py
```

---

## 📚 Документация

- **[📦 Установка](INSTALLATION.md)** - Полное руководство по установке
- **[� Решение проблем](TROUBLESHOOTING.md)** - Все известные ошибки и решения
- **[⚡ Шпаргалка](CHEATSHEET.md)** - Быстрый справочник команд

---

## 📦 Требования

- **Python**: 3.9 - 3.12 (рекомендуется), 3.13+ (см. TROUBLESHOOTING.md)
- **ОС**: Ubuntu 20.04+, Debian 10+, или Docker
- **Telegram**: Аккаунт и бот токен от [@BotFather](https://t.me/BotFather)

### Python зависимости

```
python-telegram-bot>=21.0
flask>=3.0.0
flask-cors>=4.0.0
gunicorn>=21.2.0
reportlab==4.0.7
pandas>=1.5.0
openpyxl>=3.0.0
```

---

## 🌟 Основные функции

### Telegram Бот

- ✅ Добавление/редактирование/удаление заявок ДСЕ
- ✅ Просмотр списка заявок
- ✅ Фильтрация по статусу, типу, дате
- ✅ Прикрепление фотографий
- ✅ Генерация отчетов (Excel, PDF)
- ✅ Отправка отчетов на email
- ✅ Групповой чат
- ✅ Система уведомлений

### Веб-интерфейс

- 🌐 Авторизация через Telegram
- 📊 Панель управления с статистикой
- 📋 Управление заявками ДСЕ
- 📈 Генерация и экспорт отчетов
- 💬 Веб-чат
- 🔐 Система ролей и прав
- 📱 Адаптивный дизайн

---

## 🔧 Команды бота

- `/start` - Начало работы
- `/add` - Добавить заявку ДСЕ
- `/list` - Список заявок
- `/edit` - Редактировать заявку
- `/delete` - Удалить заявку
- `/search` - Поиск заявок
- `/export` - Экспорт в Excel/PDF
- `/settings` - Настройки
- `/help` - Помощь

---

## 🛠️ Разработка

### Структура проекта (текущая)

```
TelegrammBolt/
├── bot.py                      # Главный файл бота
├── commands.py                 # Команды и обработчики
├── user_manager.py             # Управление пользователями
├── chat_manager.py             # Управление чатами
├── dse_manager.py              # Управление ДСЕ
├── dse_watcher.py              # Мониторинг ДСЕ
├── pdf_generator.py            # Генератор PDF
├── genereteTabl.py             # Генератор Excel
├── web_app.py                  # Веб-приложение
├── config.py                   # Конфигурация
├── requirements.txt            # Зависимости
└── ...
```

### Локальная разработка

```bash
# Клонировать репозиторий
git clone https://github.com/Nickto55/TelegrammBolt.git
cd TelegrammBolt

# Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или .venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить конфигурацию
cp ven_bot.json.example ven_bot.json
nano ven_bot.json

# Запустить бота
python bot.py

# Запустить веб (в отдельном терминале)
python web_app.py
```

---

## 🐳 Docker

### Быстрый запуск

```bash
# Создать docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  bot:
    build: .
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    restart: unless-stopped
EOF

# Запустить
docker-compose up -d
```

### Dockerfile (пример)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

---

## 🤝 Вклад в проект

Приветствуются Pull Requests!

1. Fork проекта
2. Создайте ветку (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

---

## 📄 Лицензия

Распространяется под лицензией MIT. См. `LICENSE` для деталей.

---

## 🔗 Полезные ссылки

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [python-telegram-bot](https://docs.python-telegram-bot.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [ReportLab](https://www.reportlab.com/docs/reportlab-userguide.pdf)

---

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/Nickto55/TelegrammBolt/issues)
- **Pull Requests**: [GitHub PRs](https://github.com/Nickto55/TelegrammBolt/pulls)
- **Документация**: [docs/](docs/) или файлы `.md` в корне

---

## 🎯 Дорожная карта

### v1.0 (Текущая) ✅
- ✅ Базовый функционал бота
- ✅ Веб-интерфейс
- ✅ Генерация отчетов
- ✅ Система уведомлений

### v2.0 (В разработке) 🚧
- 🏗️ Реструктуризация проекта
- 🐳 Docker support
- 🧪 Unit тесты
- 📚 Улучшенная документация
- 🔄 CI/CD

### v3.0 (Планируется) 📋
- 🗄️ Поддержка PostgreSQL
- 📱 Мобильное приложение
- 🔌 Plugin система
- 🌍 Интернационализация

---

## ⭐ Авторы

- **Nickto55** - [GitHub](https://github.com/Nickto55)

---

## 🙏 Благодарности

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Отличная библиотека для Telegram
- [Flask](https://github.com/pallets/flask) - Микрофреймворк для веба
- [ReportLab](https://www.reportlab.com/) - PDF генератор
- Все контрибьюторы проекта

---

<div align="center">

**Сделано с ❤️ для эффективного управления заявками ДСЕ**

[⬆ Вернуться наверх](#-telegrammbolt)

</div>
