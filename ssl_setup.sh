#!/bin/bash

# SoloCloud SSL Certificate Setup Script
# This script handles initial SSL certificate issuance using Let's Encrypt

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SSL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ssl"
WEBROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/webroot"
COMPOSE_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker-compose.yml"

echo -e "${GREEN}=== SoloCloud SSL Certificate Setup ===${NC}"

# Determine sudo usage: allow running as root; non-root will use sudo when needed
if [[ $EUID -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Certbot not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install certbot
        else
            echo -e "${RED}Please install Homebrew first, then run: brew install certbot${NC}"
            exit 1
        fi
    elif [[ -f /etc/debian_version ]]; then
        # Debian/Ubuntu
        $SUDO apt update
        $SUDO apt install -y certbot
    elif [[ -f /etc/redhat-release ]]; then
        # RHEL/CentOS/Fedora
        $SUDO yum install -y certbot || $SUDO dnf install -y certbot
    else
        echo -e "${RED}Unsupported OS. Please install certbot manually.${NC}"
        exit 1
    fi
fi

# Prompt for domain
read -p "Enter your domain name (e.g., example.com): " DOMAIN

if [[ -z "$DOMAIN" ]]; then
    echo -e "${RED}Domain name is required!${NC}"
    exit 1
fi

# Validate domain format
if ! [[ "$DOMAIN" =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
    echo -e "${RED}Invalid domain format!${NC}"
    exit 1
fi

echo -e "${YELLOW}Setting up SSL certificate for domain: $DOMAIN${NC}"

# Create webroot directory for challenge
mkdir -p "$WEBROOT_DIR"

# Create temporary nginx config for certificate challenge
cat > "${WEBROOT_DIR}/nginx-challenge.conf" << EOF
events {}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile      on;

    server {
        listen 80;
        server_name $DOMAIN;

        location /.well-known/acme-challenge/ {
            root $WEBROOT_DIR;
        }

        location / {
            return 301 https://\$server_name\$request_uri;
        }
    }
}
EOF

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker compose -f "$COMPOSE_FILE" down || true

# Start temporary nginx for challenge
echo -e "${YELLOW}Starting temporary nginx for certificate challenge...${NC}"
docker run -d --name nginx-challenge \
    -p 80:80 \
    -v "${WEBROOT_DIR}/nginx-challenge.conf:/etc/nginx/nginx.conf:ro" \
    -v "$WEBROOT_DIR:$WEBROOT_DIR:ro" \
    nginx:alpine

# Wait a moment for nginx to start
sleep 3

# Request certificate
echo -e "${YELLOW}Requesting SSL certificate from Let's Encrypt...${NC}"
$SUDO certbot certonly \
    --webroot \
    --webroot-path="$WEBROOT_DIR" \
    --email "admin@$DOMAIN" \
    --agree-tos \
    --no-eff-email \
    --domains "$DOMAIN" \
    --non-interactive

# Stop temporary nginx
docker stop nginx-challenge || true
docker rm nginx-challenge || true

# Copy certificates to ssl directory
echo -e "${YELLOW}Copying certificates to SSL directory...${NC}"
$SUDO cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/server.crt"
$SUDO cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/server.key"

# Set proper permissions
$SUDO chown $(whoami):$(whoami) "$SSL_DIR/server.crt" "$SSL_DIR/server.key"
chmod 644 "$SSL_DIR/server.crt"
chmod 600 "$SSL_DIR/server.key"

# Save domain for renewal script
echo "$DOMAIN" > "$SSL_DIR/domain.txt"

# Clean up
rm -rf "$WEBROOT_DIR"

echo -e "${GREEN}SSL certificate successfully installed!${NC}"
echo -e "${YELLOW}Certificate files:${NC}"
echo "  - Certificate: $SSL_DIR/server.crt"
echo "  - Private Key: $SSL_DIR/server.key"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update your nginx.conf to enable HTTPS (uncomment the SSL server block)"
echo "2. Update the server_name in nginx.conf to match your domain: $DOMAIN"
echo "3. Run: docker compose up -d"
echo "4. Set up auto-renewal with: ./ssl_renewal.sh --setup-cron"
