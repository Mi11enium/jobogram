# Проверка DNS
dig jobogram.ru
nslookup jobogram.ru

# Проверка портов
netstat -tulpn | grep -E ':(80|443|8501)'

# Проверка Nginx конфигурации
nginx -t

# Проверка SSL сертификата
certbot certificates

# Проверка Docker контейнера
docker ps
docker logs hh-dashboard --tail 50