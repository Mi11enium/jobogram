#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DOMAIN="jobogram.ru"

echo -e "${GREEN}🚀 Starting HH Dashboard deployment for ${DOMAIN}...${NC}"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Update system
echo -e "${YELLOW}📦 Updating system...${NC}"
apt-get update && apt-get upgrade -y

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $SUDO_USER
fi

# Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Install Nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Nginx...${NC}"
    apt-get install -y nginx
fi

# Install Certbot for SSL
echo -e "${YELLOW}📦 Installing Certbot...${NC}"
apt-get install -y certbot python3-certbot-nginx

# Create .env file if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    cat > .env << EOF
OPENROUTER_API_KEY=your_api_key_here
APP_URL=https://${DOMAIN}
DEBUG=False
EOF
    echo -e "${RED}⚠️ Please edit .env file and add your OpenRouter API key!${NC}"
    echo -e "${YELLOW}Run: nano .env${NC}"
    exit 1
fi

# Create directories
mkdir -p logs data

# Configure Nginx
echo -e "${YELLOW}🔧 Configuring Nginx for ${DOMAIN}...${NC}"
cat > /etc/nginx/sites-available/jobogram << EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN} www.${DOMAIN};

    # SSL certificates (will be added by certbot)
    # ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to Streamlit
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/jobogram /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# Restart Nginx
systemctl restart nginx

# Obtain SSL certificate
echo -e "${YELLOW}🔒 Obtaining SSL certificate from Let's Encrypt...${NC}"
certbot --nginx -d ${DOMAIN} -d www.${DOMAIN} --non-interactive --agree-tos --email admin@${DOMAIN} --redirect

# Build and run Docker container
echo -e "${GREEN}🐳 Building Docker image...${NC}"
docker-compose build

echo -e "${GREEN}🚀 Starting container...${NC}"
docker-compose up -d

# Check if container is running
sleep 5
if docker ps | grep -q jobogram; then
    echo -e "${GREEN}✅ Container is running!${NC}"
else
    echo -e "${RED}❌ Container failed to start. Check logs: docker-compose logs${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}📊 Dashboard available at: https://${DOMAIN}${NC}"
echo -e ""
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  - View logs: docker-compose logs -f"
echo -e "  - Stop: docker-compose down"
echo -e "  - Restart: docker-compose restart"
echo -e "  - Check status: docker-compose ps"
echo -e ""
echo -e "${YELLOW}Nginx commands:${NC}"
echo -e "  - Test config: nginx -t"
echo -e "  - Restart: systemctl restart nginx"
echo -e "  - Reload: systemctl reload nginx"
echo -e ""
echo -e "${YELLOW}SSL certificate renews automatically via cronjob${NC}"