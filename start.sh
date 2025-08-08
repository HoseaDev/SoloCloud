#!/bin/bash

# SoloCloud 启动脚本

# 设置环境变量
export FLASK_ENV=production
export FLASK_APP=app.py

# 设置Docker环境下的会话配置
export SESSION_COOKIE_SECURE=false
export SESSION_COOKIE_HTTPONLY=true
export SESSION_COOKIE_SAMESITE=Lax

# 创建必要的目录结构
echo "Setting up directories..."
mkdir -p /app/logs /app/data /app/uploads
mkdir -p /app/uploads/{images,videos,audio,files,archives,code,thumbnails,chat,chat_thumbnails}

# 确保当前用户有写权限（简化权限处理）
chmod -R u+w /app/logs /app/data /app/uploads 2>/dev/null || true

# 等待一下确保目录创建完成
sleep 1

# 启动应用
echo "Starting SoloCloud in production mode..."
echo "Directories created and permissions set."
echo "Logs: $(ls -la /app/logs 2>/dev/null || echo 'Directory not accessible')"
echo "Data: $(ls -la /app/data 2>/dev/null || echo 'Directory not accessible')"
echo "Uploads: $(ls -la /app/uploads 2>/dev/null || echo 'Directory not accessible')"

exec gunicorn --config gunicorn.conf.py app:app
