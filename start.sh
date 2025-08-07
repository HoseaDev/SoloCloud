#!/bin/bash

# SoloCloud 启动脚本

# 设置环境变量
export FLASK_ENV=production
export FLASK_APP=app.py

# 创建必要的目录
mkdir -p /var/log/solocloud
mkdir -p /var/run/solocloud
mkdir -p logs

# 设置权限
chmod 755 /var/log/solocloud
chmod 755 /var/run/solocloud

# 激活虚拟环境（如果使用）
# source venv/bin/activate

# 启动应用
echo "Starting SoloCloud in production mode..."
gunicorn --config gunicorn.conf.py app:app
