# Решение проблемы с Python 3.13

## Проблема

При запуске бота на Python 3.13 возникает ошибка:

```
AttributeError: 'Updater' object has no attribute '_Updater__polling_cleanup_cb' 
and no __dict__ for setting new attributes
```

Это связано с изменениями в Python 3.13, которые несовместимы с python-telegram-bot версий до 21.x.

## Решения

### Вариант 1: Обновить python-telegram-bot (РЕКОМЕНДУЕТСЯ)

Обновлен файл `requirements.txt` для использования последней версии библиотеки:

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/pip install --upgrade python-telegram-bot
```

Или переустановите все зависимости:

```bash
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/pip install --upgrade -r requirements.txt
```

### Вариант 2: Установить Python 3.11 или 3.12 (если обновление не помогло)

#### Debian/Ubuntu

```bash
# Добавить deadsnakes PPA (только для Ubuntu)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update

# Установить Python 3.12
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev

# Пересоздать виртуальное окружение
cd /opt/telegrambot
sudo rm -rf .venv
sudo -u telegrambot python3.12 -m venv .venv
sudo -u telegrambot .venv/bin/pip install --upgrade pip
sudo -u telegrambot .venv/bin/pip install -r requirements.txt

# Перезапустить бота
sudo systemctl restart telegrambot
# или для init.d:
sudo service telegrambot restart
```

#### Debian (без PPA)

Для Debian нужно собрать Python из исходников или использовать pyenv:

**С помощью pyenv:**

```bash
# Установка pyenv
curl https://pyenv.run | bash

# Добавить в ~/.bashrc:
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Установка зависимостей для сборки Python
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev \
    liblzma-dev

# Установка Python 3.12
pyenv install 3.12.0
pyenv global 3.12.0

# Пересоздать окружение
cd /opt/telegrambot
sudo rm -rf .venv
sudo -u telegrambot python3 -m venv .venv
sudo -u telegrambot .venv/bin/pip install --upgrade pip
sudo -u telegrambot .venv/bin/pip install -r requirements.txt
```

#### Docker (изменить базовый образ)

Если используете Docker, измените Dockerfile:

```dockerfile
# Было:
FROM python:3.13-slim

# Стало:
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

CMD ["python", "bot.py"]
```

Затем пересоберите образ:

```bash
docker build -t telegrambot .
docker stop telegrambot_container
docker rm telegrambot_container
docker run -d --name telegrambot_container telegrambot
```

### Вариант 3: Использовать виртуальную среду conda

```bash
# Установка Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Создание окружения с Python 3.12
conda create -n telegrambot python=3.12
conda activate telegrambot

# Установка зависимостей
cd /opt/telegrambot
pip install -r requirements.txt

# Запуск бота
python bot.py
```

## Проверка версии Python

```bash
# Проверить системную версию
python3 --version

# Проверить версию в виртуальном окружении
/opt/telegrambot/.venv/bin/python --version

# Проверить версию используемую ботом
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python --version
```

## Обновленные файлы

После обновления `requirements.txt`:

```
python-telegram-bot>=21.0
reportlab==4.0.7
pandas>=1.5.0
openpyxl>=3.0.0
```

## Тестирование после обновления

```bash
# Тестовый запуск
cd /opt/telegrambot
sudo -u telegrambot .venv/bin/python bot.py

# Если всё работает, запустить как службу
sudo systemctl start telegrambot
# или
sudo service telegrambot start

# Проверить логи
sudo journalctl -u telegrambot -f
# или
tail -f /var/log/syslog | grep telegrambot
```

## Автоматическая установка с правильной версией

Скрипты `setup.sh` и `setup_minimal.sh` теперь автоматически проверяют версию Python:

- **Python 3.9-3.12**: ✅ Рекомендуется, установка продолжается автоматически
- **Python 3.13+**: ⚠️ Предупреждение, требуется подтверждение
- **Python < 3.9**: ❌ Установка прерывается

При обнаружении Python 3.13+ скрипт предупредит и предложит отменить установку для установки совместимой версии.

## Рекомендации

1. **Для production**: Используйте Python 3.11 или 3.12
2. **Для разработки**: Можно использовать Python 3.13 с обновленной библиотекой
3. **Для Docker**: Используйте образ `python:3.12-slim`
4. **Обновления**: Регулярно обновляйте `python-telegram-bot` для получения исправлений

## Дополнительные ресурсы

- [python-telegram-bot GitHub](https://github.com/python-telegram-bot/python-telegram-bot)
- [Список изменений Python 3.13](https://docs.python.org/3/whatsnew/3.13.html)
- [deadsnakes PPA для Ubuntu](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)
