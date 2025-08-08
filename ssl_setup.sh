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

# 注册账号
echo "🔐 注册 ACME 账号..."
acme.sh --register-account -m "$EMAIL"

# 开放 80 端口（如果使用 ufw）
if command -v ufw >/dev/null 2>&1; then
  echo "🛡️ 开放 80 端口"
  ufw allow 80
fi

# 申请证书
echo "📄 申请证书..."
acme.sh --issue -d "$DOMAIN" --standalone -k ec-256

# 创建证书目录（当前目录下的 ./ssl）
echo "📁 创建证书目录 $SSL_DIR"
mkdir -p "$SSL_DIR"

# 安装证书
echo "📦 安装证书..."
acme.sh --installcert -d "$DOMAIN" --ecc \
  --key-file       "$SSL_DIR/server.key" \
  --fullchain-file "$SSL_DIR/server.crt" \
  --reloadcmd      "systemctl reload nginx || echo '请手动重启服务'"

echo "✅ 证书申请与安装完成！"
echo "证书路径：$SSL_DIR/server.key 和 $SSL_DIR/server.crt"