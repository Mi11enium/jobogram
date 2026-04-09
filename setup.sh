#!/bin/bash
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DOMAIN="${DOMAIN:-jobogram.ru}"
EMAIL="${EMAIL:-admin@jobogram.ru}"
WWW_DOMAIN="www.${DOMAIN}"

echo -e "${GREEN}Starting Jobogram deployment for ${DOMAIN}${NC}"

if [ "${EUID}" -ne 0 ]; then
  echo -e "${RED}Run this script as root (sudo).${NC}"
  exit 1
fi

if [ ! -f "docker-compose.yml" ] || [ ! -f "app.py" ]; then
  echo -e "${RED}Run setup.sh from the project root directory.${NC}"
  exit 1
fi

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

echo -e "${YELLOW}Installing required packages...${NC}"
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release nginx certbot python3-certbot-nginx

if ! command_exists docker; then
  echo -e "${YELLOW}Installing Docker...${NC}"
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sh /tmp/get-docker.sh
fi

if ! docker compose version >/dev/null 2>&1; then
  echo -e "${YELLOW}Installing Docker Compose plugin...${NC}"
  apt-get install -y docker-compose-plugin
fi

if [ ! -f ".env" ]; then
  cat > .env <<EOF
OPENROUTER_API_KEY=
APP_URL=https://${DOMAIN}
DEBUG=False
EOF
  echo -e "${RED}Created .env template. Fill OPENROUTER_API_KEY and run setup again.${NC}"
  exit 1
fi

if ! rg -n "^OPENROUTER_API_KEY=" ".env" >/dev/null 2>&1; then
  echo -e "${RED}.env is missing OPENROUTER_API_KEY line.${NC}"
  exit 1
fi

if rg -n "^OPENROUTER_API_KEY=\\s*$" ".env" >/dev/null 2>&1; then
  echo -e "${RED}OPENROUTER_API_KEY is empty in .env.${NC}"
  exit 1
fi

mkdir -p logs data

echo -e "${YELLOW}Building and starting containers...${NC}"
docker compose down --remove-orphans || true
docker compose up -d --build

echo -e "${YELLOW}Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/jobogram <<EOF
server {
    listen 80;
    server_name ${DOMAIN} ${WWW_DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

ln -sf /etc/nginx/sites-available/jobogram /etc/nginx/sites-enabled/jobogram
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo -e "${YELLOW}Requesting SSL certificate from Let's Encrypt...${NC}"
certbot --nginx \
  -d "${DOMAIN}" \
  -d "${WWW_DOMAIN}" \
  --non-interactive \
  --agree-tos \
  --email "${EMAIL}" \
  --redirect

nginx -t
systemctl reload nginx

echo -e "${YELLOW}Waiting for healthcheck...${NC}"
sleep 5

if curl -fsS "http://127.0.0.1:8501/_stcore/health" >/dev/null; then
  echo -e "${GREEN}Container healthcheck passed.${NC}"
else
  echo -e "${RED}Container healthcheck failed. Check logs: docker compose logs -f${NC}"
  exit 1
fi

if curl -kfsS "https://${DOMAIN}/health" >/dev/null; then
  echo -e "${GREEN}Nginx HTTPS healthcheck passed.${NC}"
else
  echo -e "${YELLOW}HTTPS healthcheck failed. Check DNS/ports (80, 443) and certbot output.${NC}"
fi

echo -e "${GREEN}----------------------------------------${NC}"
echo -e "${GREEN}Deployment completed.${NC}"
echo -e "${GREEN}App URL: https://${DOMAIN}${NC}"
echo -e "${GREEN}----------------------------------------${NC}"
echo "Useful commands:"
echo "  docker compose ps"
echo "  docker compose logs -f"
echo "  docker compose restart"
echo "  docker compose down"