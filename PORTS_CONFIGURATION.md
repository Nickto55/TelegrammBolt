#  Конфигурация портов TelegramBolt
##  Обзор
Веб-интерфейс TelegramBolt по умолчанию работает на порту **5000**, но вы можете изменить его несколькими способами.



##  Быстрая настройка через manage.sh
```
./manage.sh
```
Выберете: *__6__ (Запустить веб с терминалом)* вам будет предложено:
  ```
  Выберите порт для веб-интерфейса:
    1. 5000 (по умолчанию)
    2. 8080
    3. 3000
    4. Другой порт

  Выберите порт (1-4): _
  ```



## Способы изменения портов
1. **Через config/domain.conf:**
  ```
  properties
  WEB_PORT=8080
  ``` 
2. **Через переменную окружения:**
  ```
  bashchmod +x manage.sh
  WEB_PORT=8080 ./manage.sh./manage.sh
  ```

  ```bash
  # Временно для одного запуска
  WEB_PORT=8080 ./manage.sh
  ```

  ```bash
  # Или при прямом запуске
  WEB_PORT=8080 python web/web_app.py
  ```

  ```bash
  # Для Gunicorn
  WEB_PORT=8080 gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8080 web.web_app:app
  ```

3. **Через интерактивное меню manage.sh**
  ```bash
  ./manage.sh
  # Опция 6: Запустить веб с терминалом
  # Выберите нужный порт из списка
  ```

4. **Напрямую в Gunicorn**
  ```bash
  gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:3000 web.web_app:app
  ```



##  Проверка занятых портов
### Через manage.sh
  ```bash
  ./manage.sh
  # Опция 11: Детальный статус
  ```
Вывод покажет:
  ```
  Порты (используемые):
  Порт 5000:
    gunicorn (PID: 12345)
    
  Порт 8080:
    python (PID: 67890)
  ```

### Вручную через команду
  ```bash
  # Проверить конкретный порт
  sudo lsof -i :5000

  # Проверить все стандартные порты
  for PORT in 5000 5001 8080 3000; do
      echo "Порт $PORT:"
      sudo lsof -i :$PORT 2>/dev/null || echo "  Свободен"
  done
  ```


##  Решение проблем
### Ошибка: "Address already in use"
  ```bash
  # 1. Найдите процесс на порту
  sudo lsof -i :5000

  # 2. Завершите процесс
  sudo kill -9 <PID>

  # 3. Или выберите другой порт
  WEB_PORT=8080 ./manage.sh
  ```

### Systemd сервис использует неправильный порт
  ```bash
  # 1. Пересоздайте сервис с новым портом
  ./manage.sh
  # Опция 13: Настройка systemd сервиса
  # Выберите нужный порт

  # 2. Перезапустите
  sudo systemctl daemon-reload
  sudo systemctl restart telegrambolt-web
  ```

### Веб-интерфейс не открывается на новом порту
  ```bash
  # 1. Проверьте firewall
  sudo ufw status
  sudo ufw allow 8080/tcp

  # 2. Проверьте, что сервис работает на правильном порту
  sudo netstat -tulpn | grep <ПОРТ>

  # 3. Проверьте логи
  sudo journalctl -u telegrambolt-web -f
  ```



##  Доступ к веб-интерфейсу
После изменения порта, доступ будет по адресам:
  ```
  http://localhost:5000          # Локально (порт 5000)
  http://localhost:8080          # Локально (порт 8080)
  http://YOUR_SERVER_IP:5000     # Удалённо (порт 5000)
  http://YOUR_SERVER_IP:8080     # Удалённо (порт 8080)
  ```

**Веб-терминал:**
  ```
  http://YOUR_SERVER_IP:5000/terminal
  http://YOUR_SERVER_IP:8080/terminal
  ```



##  Приоритет настроек
Порт определяется в следующем порядке (от высшего к низшему приоритета):
  1. **Параметр командной строки Gunicorn** (`--bind 0.0.0.0:8080`)
  2. **Переменная окружения** (`WEB_PORT=8080`)
  3. **Файл domain.conf** (`WEB_PORT=8080`)
  4. **Значение по умолчанию** (5000)



##  Рекомендации
  1. **Для продакшена:** используйте `config/domain.conf` для постоянной конфигурации
  2. **Для тестирования:** используйте переменную окружения `WEB_PORT=...`
  3. **Для автозапуска:** настройте systemd через `manage.sh` (опция 13)
  4. **Для безопасности:** если открываете доступ извне, используйте reverse proxy (nginx/apache)



##  Связанные файлы
  - `config/domain.conf` - основная конфигурация
  - `manage.sh` - панель управления с интерактивным выбором портов
  - `web/web_app.py` - основное приложение (читает WEB_PORT)
  - `/etc/systemd/system/telegrambolt-web.service` - systemd сервис



##  Примеры использования
### Запуск на нескольких портах одновременно
  ```bash
  # Терминал 1
  WEB_PORT=5000 gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 web.web_app:app

  # Терминал 2
  WEB_PORT=8080 gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8080 web.web_app:app
```

### Тестирование на локальном порту
  ```bash
  # Запуск только на localhost (недоступен извне)
  gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:5000 web.web_app:app
  ```
