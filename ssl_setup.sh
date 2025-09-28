#!/bin/bash

# 用法: ./install_ssl.sh yourdomain.com youremail@example.com
DOMAIN=$1
EMAIL=$2

# 定义证书目录为当前目录下的 ssl 文件夹
SSL_DIR="$(pwd)/ssl"

# 检查参数
if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "用法: $0 yourdomain.com youremail@example.com"
  exit 1
fi

echo "📥 开始为域名 $DOMAIN 安装 SSL 证书"

# 安装 acme.sh
echo "🔧 安装 acme.sh..."
curl https://get.acme.sh | sh

# 添加软链接
ln -sf /root/.acme.sh/acme.sh /usr/local/bin/acme.sh

# 安装 socat
echo "🔧 安装 socat..."
apt update && apt install -y socat

# 设置默认 CA 为 Let's Encrypt
echo "🔐 设置使用 Let's Encrypt..."
acme.sh --set-default-ca --server letsencrypt

# 注册账号（使用 Let's Encrypt）
echo "🔐 注册 ACME 账号..."
acme.sh --register-account -m "$EMAIL" --server letsencrypt

# 开放 80 端口（如果使用 ufw）
if command -v ufw >/dev/null 2>&1; then
  echo "🛡️ 开放 80 端口"
  ufw allow 80
fi

# 申请证书
echo "📄 申请证书..."
# 先释放 80 端口（standalone 必须占用 80）
# 优先停止 docker compose 的服务（若存在）
if command -v docker >/dev/null 2>&1 && command -v docker compose >/dev/null 2>&1 && [ -f "$PWD/docker-compose.yml" ]; then
  echo "⏸️ 停止 docker compose 服务以释放 80 端口..."
  docker compose down || true
fi
# 如果有系统服务占用 80（常见 nginx/caddy），先停掉
if command -v systemctl >/dev/null 2>&1; then
  systemctl is-active --quiet nginx  && { echo "⏸️ 停止 nginx";  systemctl stop nginx  || true; }
  systemctl is-active --quiet caddy  && { echo "⏸️ 停止 caddy";  systemctl stop caddy  || true; }
fi

# 申请证书（使用 Let's Encrypt，standalone 监听 80）
# 添加 --listen-v4 确保在 IPv6 环境下也能正常工作
if ! acme.sh --issue -d "$DOMAIN" --standalone -k ec-256 --server letsencrypt --listen-v4; then
  echo "❌ 证书申请失败。请确认域名解析到本机、80 端口可从公网访问，且未被占用。" >&2
  exit 1
fi

# 创建证书目录（当前目录下的 ./ssl）
echo "📁 创建证书目录 $SSL_DIR"
mkdir -p "$SSL_DIR"

 # 安装证书
echo "📦 安装证书..."
acme.sh --installcert -d "$DOMAIN" --ecc \
  --key-file       "$SSL_DIR/server.key" \
  --fullchain-file "$SSL_DIR/server.crt" \
  --reloadcmd      "true"

echo "请手动重启 SoloCloud"

# 检查证书文件生成成功
if [ ! -s "$SSL_DIR/server.crt" ] || [ ! -s "$SSL_DIR/server.key" ]; then
  echo "❌ 安装证书失败（文件未生成）。请检查上面的 acme.sh 输出。" >&2
  exit 1
fi

# 保存域名便于自动续期脚本使用
printf "%s" "$DOMAIN" > "$SSL_DIR/domain.txt"

echo "✅ 证书申请与安装完成！"
echo "证书路径：$SSL_DIR/server.key 和 $SSL_DIR/server.crt"