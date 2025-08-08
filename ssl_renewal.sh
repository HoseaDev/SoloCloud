#!/bin/bash

# SoloCloud SSL Certificate Auto-Renewal Script
# This script automatically renews SSL certificates every 3 months minus 1 day

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="$SCRIPT_DIR/ssl"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
LOG_FILE="$SCRIPT_DIR/logs/ssl_renewal.log"
DOMAIN_FILE="$SSL_DIR/domain.txt"

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Check if domain file exists
if [[ ! -f "$DOMAIN_FILE" ]]; then
    error_exit "Domain file not found. Please run ssl_setup.sh first."
fi

DOMAIN=$(cat "$DOMAIN_FILE")

if [[ -z "$DOMAIN" ]]; then
    error_exit "Domain not found in $DOMAIN_FILE"
fi

# Function to setup cron job
setup_cron() {
    log "Setting up cron job for SSL auto-renewal"
    
    # Calculate renewal schedule (every 89 days = 3 months - 1 day)
    CRON_SCRIPT="$SCRIPT_DIR/ssl_renewal.sh"
    
    # Make script executable
    chmod +x "$CRON_SCRIPT"
    
    # Create cron entry (runs at 3 AM on the 89th day cycle)
    CRON_ENTRY="0 3 */89 * * $CRON_SCRIPT --renew >> $LOG_FILE 2>&1"
    
    # Check if cron entry already exists
    if crontab -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
        log "Cron job already exists"
        echo -e "${YELLOW}Cron job already exists. Current crontab:${NC}"
        crontab -l | grep "$CRON_SCRIPT"
    else
        # Add to crontab
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
        log "Cron job added successfully"
        echo -e "${GREEN}Cron job added successfully!${NC}"
        echo "The script will run every 89 days (3 months - 1 day) at 3 AM"
    fi
    
    # Also create a systemd timer as alternative (for systems that prefer it)
    create_systemd_timer
}

# Function to create systemd timer (alternative to cron)
create_systemd_timer() {
    if command -v systemctl &> /dev/null; then
        log "Creating systemd timer as alternative to cron"
        
        # Create service file
        sudo tee /etc/systemd/system/solocloud-ssl-renewal.service > /dev/null << EOF
[Unit]
Description=SoloCloud SSL Certificate Renewal
After=network.target

[Service]
Type=oneshot
User=$(whoami)
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/ssl_renewal.sh --renew
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE
EOF

        # Create timer file
        sudo tee /etc/systemd/system/solocloud-ssl-renewal.timer > /dev/null << EOF
[Unit]
Description=Run SoloCloud SSL renewal every 89 days
Requires=solocloud-ssl-renewal.service

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
RandomizedDelaySec=3600

[Install]
WantedBy=timers.target
EOF

        # Reload systemd and enable timer
        sudo systemctl daemon-reload
        sudo systemctl enable solocloud-ssl-renewal.timer
        
        log "Systemd timer created and enabled"
        echo -e "${GREEN}Systemd timer created as alternative scheduling method${NC}"
        echo "You can check timer status with: systemctl status solocloud-ssl-renewal.timer"
    fi
}

# Function to renew certificate
renew_certificate() {
    log "Starting SSL certificate renewal for domain: $DOMAIN"
    
    # Check if certificate exists and when it expires
    if [[ -f "$SSL_DIR/server.crt" ]]; then
        EXPIRY_DATE=$(openssl x509 -enddate -noout -in "$SSL_DIR/server.crt" | cut -d= -f2)
        EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$EXPIRY_DATE" +%s)
        CURRENT_EPOCH=$(date +%s)
        DAYS_LEFT=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
        
        log "Certificate expires in $DAYS_LEFT days"
        
        # Only renew if less than 30 days left (Let's Encrypt recommendation)
        if [[ $DAYS_LEFT -gt 30 ]]; then
            log "Certificate still valid for $DAYS_LEFT days. Skipping renewal."
            echo -e "${GREEN}Certificate still valid for $DAYS_LEFT days. No renewal needed.${NC}"
            return 0
        fi
    fi
    
    # Stop containers for renewal
    log "Stopping containers for renewal"
    docker-compose -f "$COMPOSE_FILE" down
    
    # Create webroot for challenge
    WEBROOT_DIR="$SCRIPT_DIR/webroot"
    mkdir -p "$WEBROOT_DIR"
    
    # Create temporary nginx for challenge
    cat > "$WEBROOT_DIR/nginx-challenge.conf" << EOF
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

    # Start temporary nginx
    log "Starting temporary nginx for certificate challenge"
    docker run -d --name nginx-challenge-renewal \
        -p 80:80 \
        -v "$WEBROOT_DIR/nginx-challenge.conf:/etc/nginx/nginx.conf:ro" \
        -v "$WEBROOT_DIR:$WEBROOT_DIR:ro" \
        nginx:alpine

    sleep 3

    # Renew certificate
    log "Renewing certificate with certbot"
    if sudo certbot renew --webroot --webroot-path="$WEBROOT_DIR" --quiet; then
        log "Certificate renewed successfully"
        
        # Copy new certificates
        sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/server.crt"
        sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/server.key"
        
        # Set proper permissions
        sudo chown $(whoami):$(whoami) "$SSL_DIR/server.crt" "$SSL_DIR/server.key"
        chmod 644 "$SSL_DIR/server.crt"
        chmod 600 "$SSL_DIR/server.key"
        
        log "Certificates copied to SSL directory"
    else
        log "Certificate renewal failed"
        # Clean up and restart services anyway
        docker stop nginx-challenge-renewal || true
        docker rm nginx-challenge-renewal || true
        rm -rf "$WEBROOT_DIR"
        docker-compose -f "$COMPOSE_FILE" up -d
        error_exit "Certificate renewal failed"
    fi
    
    # Clean up temporary nginx
    docker stop nginx-challenge-renewal || true
    docker rm nginx-challenge-renewal || true
    rm -rf "$WEBROOT_DIR"
    
    # Restart services
    log "Restarting SoloCloud services"
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log "SSL certificate renewal completed successfully"
    echo -e "${GREEN}SSL certificate renewed successfully!${NC}"
}

# Function to check certificate status
check_certificate() {
    if [[ ! -f "$SSL_DIR/server.crt" ]]; then
        echo -e "${RED}No SSL certificate found. Run ssl_setup.sh first.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}=== SSL Certificate Status ===${NC}"
    echo "Domain: $DOMAIN"
    echo "Certificate file: $SSL_DIR/server.crt"
    echo "Private key file: $SSL_DIR/server.key"
    echo ""
    
    # Get certificate information
    EXPIRY_DATE=$(openssl x509 -enddate -noout -in "$SSL_DIR/server.crt" | cut -d= -f2)
    ISSUED_DATE=$(openssl x509 -startdate -noout -in "$SSL_DIR/server.crt" | cut -d= -f2)
    ISSUER=$(openssl x509 -issuer -noout -in "$SSL_DIR/server.crt" | sed 's/issuer=//')
    
    echo "Issued: $ISSUED_DATE"
    echo "Expires: $EXPIRY_DATE"
    echo "Issuer: $ISSUER"
    
    # Calculate days left
    EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$EXPIRY_DATE" +%s)
    CURRENT_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
    
    if [[ $DAYS_LEFT -lt 0 ]]; then
        echo -e "${RED}Certificate EXPIRED $((DAYS_LEFT * -1)) days ago!${NC}"
    elif [[ $DAYS_LEFT -lt 30 ]]; then
        echo -e "${YELLOW}Certificate expires in $DAYS_LEFT days (renewal recommended)${NC}"
    else
        echo -e "${GREEN}Certificate expires in $DAYS_LEFT days${NC}"
    fi
}

# Main script logic
case "${1:-}" in
    --setup-cron)
        setup_cron
        ;;
    --renew)
        renew_certificate
        ;;
    --check)
        check_certificate
        ;;
    --help)
        echo "SoloCloud SSL Auto-Renewal Script"
        echo ""
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --setup-cron    Set up automatic renewal via cron job"
        echo "  --renew         Manually renew the SSL certificate"
        echo "  --check         Check current certificate status"
        echo "  --help          Show this help message"
        echo ""
        echo "For first-time setup, run ssl_setup.sh first."
        ;;
    *)
        echo -e "${YELLOW}SoloCloud SSL Auto-Renewal Script${NC}"
        echo ""
        echo "Usage: $0 [--setup-cron|--renew|--check|--help]"
        echo ""
        echo "Run '$0 --help' for more information."
        ;;
esac
