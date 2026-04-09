# Jobogram deploy (одна команда)

Ниже инструкция для Ubuntu VPS и домена `jobogram.ru`.

## 1) Подготовка DNS

Убедитесь, что A-записи направляют на IP вашего VPS:

- `jobogram.ru`
- `www.jobogram.ru`

## 2) Клонирование проекта

```bash
ssh root@YOUR_VPS_IP
git clone https://github.com/your-username/jobogram.git
cd jobogram
```

## 3) Подготовка `.env`

Создайте или отредактируйте `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-your-real-key
APP_URL=https://jobogram.ru
DEBUG=False
```

Важно: файл должен быть в формате `KEY=value` без `export`.

## 4) Деплой одной командой

```bash
chmod +x setup.sh
sudo DOMAIN=jobogram.ru EMAIL=admin@jobogram.ru ./setup.sh
```

Скрипт сам:

- установит Docker, Docker Compose plugin, Nginx, Certbot;
- запустит приложение в Docker;
- настроит Nginx reverse proxy;
- выпустит SSL сертификаты Let's Encrypt;
- включит HTTPS-редирект и выполнит health-check.

## 5) Проверка

```bash
curl -I https://jobogram.ru/health
docker compose ps
docker compose logs -f
```

## Обновление после изменений

```bash
git pull
sudo DOMAIN=jobogram.ru EMAIL=admin@jobogram.ru ./setup.sh
```

## Полезные команды

```bash
docker compose ps
docker compose logs -f
docker compose restart
docker compose down
sudo nginx -t
sudo systemctl reload nginx
```