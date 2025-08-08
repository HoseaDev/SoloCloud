#!/bin/bash

# SoloCloud SSL Certificate Auto-Renewal (acme.sh + standalone)
# - 不使用 docker 或临时 nginx
# - 证书默认安装到脚本目录下的 ./ssl
# - 支持 cron 和 systemd timer 定时执行

set -euo pipefail

# === Colors ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# === sudo handling ===
if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

# === Paths ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
SSL_DIR="./ssl"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
LOG_FILE="$SCRIPT_DIR/logs/ssl_renewal.log"
DOMAIN_FILE="$SSL_DIR/domain.txt"

# Ensure log dir exists
mkdir -p "$(dirname "$LOG_FILE")"

log(){ echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"; }
err(){ echo -e "${RED}ERROR:${NC} $*" >&2; log "ERROR: $*"; }

need(){ command -v "$1" >/dev/null 2>&1 || { err "缺少命令: $1"; exit 1; }; }

# === Helpers ===
stop_80_services(){
  RESTORE_CMDS=()
  if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet nginx 2>/dev/null; then
      log "⏸️ 停止 nginx 以释放 80 端口"
      $SUDO systemctl stop nginx || true
      RESTORE_CMDS+=("$SUDO systemctl start nginx")
    fi
    if systemctl is-active --quiet caddy 2>/dev/null; then
      log "⏸️ 停止 caddy 以释放 80 端口"
      $SUDO systemctl stop caddy || true
      RESTORE_CMDS+=("$SUDO systemctl start caddy")
    fi
  fi
}

restore_services(){
  for cmd in "${RESTORE_CMDS[@]:-}"; do
    log "▶ 恢复: $cmd"
    bash -c "$cmd" || true
  done
}

# === Core actions ===
renew_certificate(){
  need acme.sh
  mkdir -p "$SSL_DIR"

  if [[ ! -f "$DOMAIN_FILE" ]]; then
    err "未找到域名文件: $DOMAIN_FILE 。请先运行 ssl_setup.sh 申请首张证书。"
    exit 1
  fi
  DOMAIN=$(tr -d '\n\r' < "$DOMAIN_FILE")
  if [[ -z "$DOMAIN" ]]; then
    err "域名文件为空: $DOMAIN_FILE"
    exit 1
  fi

  # 若已有证书, 展示剩余天数
  if [[ -f "$SSL_DIR/server.crt" ]]; then
    EXPIRY_DATE=$(openssl x509 -enddate -noout -in "$SSL_DIR/server.crt" | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$EXPIRY_DATE" +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - $(date +%s)) / 86400 ))
    log "当前证书剩余: ${DAYS_LEFT} 天"
    if (( DAYS_LEFT > 30 )); then
      log "证书仍然有效(>30天)，将尝试按 ACME 策略续期（可能跳过）。"
    fi
  fi

  # 确保 80 端口可用（standalone 模式）
  stop_80_services
  trap 'restore_services' EXIT

  log "🔄 使用 acme.sh 续期: $DOMAIN (standalone/ec-256)"
  # 若初次申请用的是 --standalone，则 acme.sh 会复用该方式
  acme.sh --renew -d "$DOMAIN" --ecc --standalone || {
    err "acme.sh 续期失败，请检查 80 端口访问与 DNS 解析"; exit 1; }

  log "📦 安装证书到 $SSL_DIR"
  acme.sh --installcert -d "$DOMAIN" --ecc \
    --key-file       "$SSL_DIR/server.key" \
    --fullchain-file "$SSL_DIR/server.crt" \
    --reloadcmd      "systemctl reload nginx || echo '如需重载其他服务请手动重启'"

  chmod 600 "$SSL_DIR/server.key"
  chmod 644 "$SSL_DIR/server.crt"

  log "✅ 续期完成: $SSL_DIR/server.crt"
}

check_certificate(){
  if [[ ! -f "$SSL_DIR/server.crt" ]]; then
    err "未找到证书文件: $SSL_DIR/server.crt"
    return 1
  fi
  echo -e "${GREEN}=== SSL Certificate Status ===${NC}"
  echo "Domain: $(cat "$DOMAIN_FILE" 2>/dev/null || echo '?')"
  echo "Certificate: $SSL_DIR/server.crt"
  echo "Private Key: $SSL_DIR/server.key"
  EXPIRY_DATE=$(openssl x509 -enddate -noout -in "$SSL_DIR/server.crt" | cut -d= -f2)
  ISSUED_DATE=$(openssl x509 -startdate -noout -in "$SSL_DIR/server.crt" | cut -d= -f2)
  ISSUER=$(openssl x509 -issuer -noout -in "$SSL_DIR/server.crt" | sed 's/issuer=//')
  echo "Issued:  $ISSUED_DATE"
  echo "Expires: $EXPIRY_DATE"
  echo "Issuer:  $ISSUER"
  EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$EXPIRY_DATE" +%s)
  DAYS_LEFT=$(( (EXPIRY_EPOCH - $(date +%s)) / 86400 ))
  if (( DAYS_LEFT < 0 )); then
    echo -e "${RED}证书已过期 $((-DAYS_LEFT)) 天!${NC}"
  elif (( DAYS_LEFT < 30 )); then
    echo -e "${YELLOW}证书将于 ${DAYS_LEFT} 天后过期，建议尽快续期${NC}"
  else
    echo -e "${GREEN}证书有效，剩余 ${DAYS_LEFT} 天${NC}"
  fi
}

setup_cron(){
  log "配置 cron 定时续期（每 60 天凌晨 3 点）"
  CRON_SCRIPT="$SCRIPT_DIR/ssl_renewal.sh"
  chmod +x "$CRON_SCRIPT"
  # 约 60 天一次（Let's Encrypt 90 天有效期，提前续期更稳）
  CRON_ENTRY="0 3 */60 * * $CRON_SCRIPT --renew >> $LOG_FILE 2>&1"
  if crontab -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
    log "cron 已存在："; crontab -l | grep "$CRON_SCRIPT" || true
  else
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    log "cron 添加成功"
  fi
  create_systemd_timer
}

create_systemd_timer(){
  if command -v systemctl >/dev/null 2>&1; then
    log "创建 systemd timer（作为 cron 的备选）"
    $SUDO tee /etc/systemd/system/solocloud-ssl-renewal.service >/dev/null <<EOF
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

    $SUDO tee /etc/systemd/system/solocloud-ssl-renewal.timer >/dev/null <<EOF
[Unit]
Description=Run SoloCloud SSL renewal periodically
Requires=solocloud-ssl-renewal.service

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
RandomizedDelaySec=3600

[Install]
WantedBy=timers.target
EOF

    $SUDO systemctl daemon-reload
    $SUDO systemctl enable --now solocloud-ssl-renewal.timer || true
    log "systemd timer 已创建并启用"
  fi
}

usage(){
  echo "SoloCloud SSL Auto-Renewal"
  echo "Usage: $0 [--setup-cron|--renew|--check|--help]"
}

case "${1:-}" in
  --setup-cron) setup_cron ;; 
  --renew)      renew_certificate ;;
  --check)      check_certificate ;;
  --help|*)     usage ;;
cesac
