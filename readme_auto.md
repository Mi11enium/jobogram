# 1. Подключитесь к VPS
ssh root@your-server-ip

# 2. Клонируйте репозиторий
git clone https://github.com/your-username/jobogram.git
cd jobogram

# 3. Создайте и заполните .env файл (ОБЯЗАТЕЛЬНО!)
nano .env
# Вставьте:
# OPENROUTER_API_KEY=sk-or-v1-ваш_реальный_ключ
# APP_URL=https://jobogram.ru
# DEBUG=False

# 4. Запустите setup.sh (он сделает ВСЁ остальное)
chmod +x setup.sh
./setup.sh