# 1. Подключитесь к вашему VPS
ssh root@your-server-ip

# 2. Убедитесь, что DNS записи настроены правильно
# Должны быть A записи для jobogram.ru и www.jobogram.ru, указывающие на IP вашего VPS

# 3. Клонируйте проект
git clone https://github.com/your-username/hh-dashboard.git
cd hh-dashboard

# 4. Создайте .env файл с вашим API ключом
nano .env
# Добавьте (замените на реальный ключ):
# OPENROUTER_API_KEY=sk-or-v1-ваш_реальный_ключ
# APP_URL=https://jobogram.ru
# DEBUG=False

# 5. Установите Nginx и Certbot (ОБЯЗАТЕЛЬНЫЙ ШАГ!)
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# 6. Скопируйте конфиг Nginx
sudo cp nginx.conf /etc/nginx/sites-available/hh-dashboard

# 7. Активируйте сайт
sudo ln -s /etc/nginx/sites-available/hh-dashboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Удаляем дефолтный сайт

# 8. Проверьте конфигурацию Nginx
sudo nginx -t

# 9. Перезапустите Nginx
sudo systemctl restart nginx

# 10. Получите SSL сертификат для вашего домена
sudo certbot --nginx -d jobogram.ru -d www.jobogram.ru

# Когда certbot спросит, выберите опцию перенаправления HTTP на HTTPS (option 2)

# 11. Запустите Docker контейнер
docker-compose up -d

# 12. Проверьте, что все работает
docker-compose ps
docker-compose logs -f

# 13. Проверьте, что сайт доступен
curl -I https://jobogram.ru/health