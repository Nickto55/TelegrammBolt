# Настройка DuckDNS для SSL

## Проблема
DuckDNS домены (*.duckdns.org) иногда не резолвятся из-за проблем с DNS серверами.

## Решение 1: Проверка и обновление DuckDNS

### 1. Проверьте текущий IP вашего сервера
```bash
curl ifconfig.me
```

### 2. Обновите IP в DuckDNS
Зайдите на https://www.duckdns.org и обновите ваш домен `boltvolna` с новым IP.

Или через API:
```bash
# Замените YOUR_TOKEN и boltvolna на ваши данные
curl "https://www.duckdns.org/update?domains=boltvolna&token=YOUR_TOKEN&ip="
```

### 3. Проверьте DNS резолвинг
```bash
# Проверка DNS
dig boltvolna.duckdns.org

# Проверка с внешнего DNS
dig @8.8.8.8 boltvolna.duckdns.org
```

Должно вернуть IP вашего сервера.

### 4. Подождите распространения DNS
DNS изменения могут занять от 5 минут до 24 часов. Проверяйте периодически:
```bash
watch -n 10 "dig +short boltvolna.duckdns.org"
```

## Решение 2: Использование standalone режима Certbot

Если nginx метод не работает, попробуйте standalone:

### 1. Остановите nginx
```bash
sudo systemctl stop nginx
```

### 2. Получите сертификат через standalone
```bash
sudo certbot certonly --standalone -d boltvolna.duckdns.org --email your@email.com --agree-tos
```

### 3. Настройте nginx вручную
```bash
sudo nano /etc/nginx/sites-available/telegrambot
```

Добавьте:
```nginx
server {
    listen 80;
    server_name boltvolna.duckdns.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name boltvolna.duckdns.org;
    
    ssl_certificate /etc/letsencrypt/live/boltvolna.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/boltvolna.duckdns.org/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Запустите nginx
```bash
sudo nginx -t
sudo systemctl start nginx
```

## Решение 3: Использование другого DNS провайдера

Альтернативы DuckDNS:
- **No-IP** (https://www.noip.com) - более стабильный
- **Dynu** (https://www.dynu.com) - бесплатные домены
- **FreeDNS** (https://freedns.afraid.org) - множество доменов

## Решение 4: Работа без SSL (для тестирования)

Если SSL не критичен, используйте HTTP:

```bash
./manage.sh
# Выберите "7. Настройка SSL/Домена"
# При запросе SSL выберите "3. Пропустить SSL"
```

Доступ будет по: http://boltvolna.duckdns.org

## Решение 5: Использование Cloudflare (рекомендуется)

### Преимущества:
- Бесплатный SSL
- DDoS защита
- CDN
- Лучшая надежность DNS

### Настройка:

1. Зарегистрируйтесь на https://cloudflare.com
2. Добавьте ваш домен (если есть свой) или купите через Cloudflare
3. Измените nameservers домена на Cloudflare
4. В Cloudflare DNS добавьте A-запись с IP вашего сервера
5. Включите "Flexible SSL" в настройках

Cloudflare автоматически предоставит SSL сертификат.

## Проверка firewall

Убедитесь что порты 80 и 443 открыты:

```bash
# Проверка портов
sudo ss -tulpn | grep ':80\|:443'

# Открытие портов через ufw
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# Или через iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables-save
```

## Проверка с внешней стороны

Проверьте доступность вашего домена извне:
- https://dnschecker.org - проверка DNS по всему миру
- https://www.ssllabs.com/ssltest/ - проверка SSL
- https://mxtoolbox.com/SuperTool.aspx - комплексная проверка

## Автоматическое обновление DuckDNS IP

Создайте скрипт для автообновления:

```bash
nano ~/update-duckdns.sh
```

Добавьте:
```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=boltvolna&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns.log -K -
```

Сделайте исполняемым и добавьте в cron:
```bash
chmod +x ~/update-duckdns.sh
crontab -e
```

Добавьте строку:
```
*/5 * * * * ~/update-duckdns.sh >/dev/null 2>&1
```

Теперь IP будет обновляться каждые 5 минут.

## Отладка

### Проверка логов certbot
```bash
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Проверка логов nginx
```bash
sudo tail -f /var/log/nginx/error.log
```

### Тест соединения
```bash
# Проверка HTTP
curl -I http://boltvolna.duckdns.org

# Проверка HTTPS
curl -I https://boltvolna.duckdns.org

# Детальная проверка SSL
openssl s_client -connect boltvolna.duckdns.org:443
```

## Контакты для помощи

Если ничего не помогло:
- Let's Encrypt форум: https://community.letsencrypt.org
- DuckDNS форум: https://www.reddit.com/r/duckdns
- Nginx документация: https://nginx.org/ru/docs/
