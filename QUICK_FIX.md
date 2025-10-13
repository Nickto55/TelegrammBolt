# ⚡ Команды для исправления ошибки Python 3.13

## Если вы получили ошибку AttributeError с Updater

### Быстрое исправление (1 команда):

```bash
cd /opt/telegrambot && sudo -u telegrambot .venv/bin/pip install --upgrade python-telegram-bot && sudo systemctl restart telegrambot
```

Или для init.d:
```bash
cd /opt/telegrambot && sudo -u telegrambot .venv/bin/pip install --upgrade python-telegram-bot && sudo service telegrambot restart
```

### Проверка:

```bash
# Проверить версию библиотеки
/opt/telegrambot/.venv/bin/pip show python-telegram-bot | grep Version

# Должно быть: Version: 21.0 или выше
```

### Если не помогло - установить Python 3.12:

**Ubuntu:**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y && \
sudo apt-get update && \
sudo apt-get install -y python3.12 python3.12-venv && \
cd /opt/telegrambot && \
sudo rm -rf .venv && \
sudo -u telegrambot python3.12 -m venv .venv && \
sudo -u telegrambot .venv/bin/pip install --upgrade pip && \
sudo -u telegrambot .venv/bin/pip install -r requirements.txt && \
sudo systemctl restart telegrambot
```

**Docker - изменить первую строку Dockerfile:**
```dockerfile
FROM python:3.12-slim
```

Затем:
```bash
docker build -t telegrambot . && \
docker stop telegrambot_container && \
docker rm telegrambot_container && \
docker run -d --name telegrambot_container telegrambot
```

### Тестовый запуск:

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py
```

Если запустился без ошибок - всё исправлено! Нажмите Ctrl+C.

### Документация:
- [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md) - подробное описание всех решений
- [DOCKER_PYTHON_FIX.md](DOCKER_PYTHON_FIX.md) - специально для Docker
